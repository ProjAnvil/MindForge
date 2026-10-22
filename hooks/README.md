# style-rules-zh-cn 插件（中文写作规范 + 翻译腔防御）

MindForge 中文 hook 插件。设计文档：WorkBuddy `zh-guard-spec-v2.0.md`（zh-guard 部分）。

## 结构

| 组件 | 文件 | 事件/通道 | 职责 |
|---|---|---|---|
| 写作规范 | inject-style-rules.sh | SessionStart / UserPromptSubmit（+ SubagentStart，仅 Claude） | 注入受控写作规范（中文+英文） |
| 公共库 | zh_guard_common.py | - | 三级词典加载、豁免、防循环状态（hook 脚本的同目录依赖） |
| L0 字典 | terminology.tsv（内置） / mindforge.zh-dict.tsv（项目级） | - | 三级术语字典：内置 → 用户级 → 项目级（数据飞轮） |
| L1 术语注入 | inject.py | UserPromptSubmit | 每轮注入术语规范 + 「直译词→期望写法」对照 |
| L2 出口检测 | inspect.py | Stop（+ SubagentStop，仅 Claude） | 命中直译词要求重写（按地道措辞重写整句） |
| L2 文件写入口 | inspect-file.py | PreToolUse（Write\|Edit\|NotebookEdit） | 文档类文件（.md/.markdown/.txt/.rst）写入前检测，deny 并要求改写 |
| L2 句式判官 | claude-prompt-hooks.json | Stop（prompt 型，仅 Claude Code） | 字典未命中时小模型判断是否地道中文，覆盖长尾句式 |
| 知识层（拉模式） | term-dict-server.py | MCP（term-dict） | 按需查词 / 交付前自查 / 飞轮入库 |
| 字典整理 | tidy-dict.py | 手动运行 | 排版对齐 + 体检（去重、坏正则、缺列） |
| 整理效果评测 | eval-tidy-dict.py | 手动运行 | 前后对比：行为等价 + token/字符 + 耗时 |
| 方案成本评测 | eval-zh-guard.py | 手动运行 | 装 vs 不装（含空字典）：token、耗时、拦截代价 |

所有 hook 全部 fail-open：任何异常静默放行，绝不卡死会话。

## 多平台

hook 配置按平台拆分：

- `hooks/hooks.json`（标准位置，Claude Code 与 zcode 都自动加载）只含三平台
  都支持的事件：SessionStart、UserPromptSubmit、Stop。
- `hooks/subagent-hooks.json` 只含 Claude Code 支持的 SubagentStart /
  SubagentStop，由 `.claude-plugin/plugin.json` 的 `hooks` 字段声明
  （与自动发现的 hooks.json 合并加载，Claude Code 行为不变）。

### zcode

zcode 直接装本插件（`.claude-plugin/plugin.json` 在其 manifest 查找列表内）。
`.zcode-plugin/plugin.json` 专为 zcode 准备：不带 `hooks` 字段，zcode 优先读它，
只会自动加载 `hooks/hooks.json`，不会再看到自己没有的事件
（SubagentStart / SubagentStop 在 zcode 属于永不触发的死配置）。

- 注入（SessionStart / UserPromptSubmit）：zcode 同样解析
  `hookSpecificOutput.additionalContext`，脚本原样可用。
- MCP：zcode 自动启动 term-dict。
- Stop：zcode 的契约是 `decision:"block"` + reason；`continue:false` 在 zcode
  里语义相反（允许结束）。inspect.py 检测 `ZCODE_PLUGIN_ROOT` 自动切换输出。
- 子代理：zcode 没有子代理事件，规范注入与 L2 覆盖不到子代理。
- 文件写入口（PreToolUse）：zcode 支持，matcher `Write|Edit` 语义一致。
- 句式判官（prompt 型 hook）：Claude Code 独有类型，配置在
  `hooks/claude-prompt-hooks.json`（Claude 专属文件，zcode 不加载，
  不会产生死配置告警）。判官每轮 Stop 增加一次小模型调用（默认
  Haiku 级，约 1-3 秒），只在字典出口未命中时才有拦截作用；
  `stop_hook_active` 为 true 时判官直接放行，防止连环阻断。
- 用户级 config 里的 hook 需要 `hooks.enabled: true`；插件 hook 跟随插件
  启停，不需要。更新插件后新建 session 才生效（hook 配置有会话快照）。

### 已知边界

- 文件写入口只查 .md/.markdown/.txt/.rst；代码内中文注释需要先隔离
  字符串与 docstring，暂不检测。编辑本插件自己的 README（内含直译词
  示例）会被拦一次，重试同内容即放行，或给示例词加「」引号。
- Kimi 上 Stop payload 不含助手消息（上游 issue #2123），出口层失效；
  文件写入口是 Kimi 上唯一可用的输出检测口，将来注册时 matcher 需按
  Kimi 工具名写 `WriteFile|StrReplaceFile`。

### Kimi Code

尚未适配。配置在 `~/.kimi-code/config.toml` 的 `[[hooks]]`（仅 4 个字段），
注入机制是 stdout 纯文本附加到上下文，只有 PreToolUse / Stop /
UserPromptSubmit 三个事件可阻断，其余全是观察型（fire-and-forget）。

## term-dict MCP 服务

插件清单声明了 `mcpServers`（`${CLAUDE_PLUGIN_ROOT}` 定位），装插件即得，
工具自动命名空间化。纯 Python stdio 实现，零依赖，系统 `python3` 即可运行。
与 L1/L2 共享同一份合并字典（含 `re:` 正则词条），每次调用现读，`add_term`
入库后立即可查、下轮注入生效。

| 工具 | 用途 |
|---|---|
| `lookup_term(query)` | 双向查词：英文/中文子串匹配直译词、期望写法、说明 |
| `check_text(text)` | 交付前自查：L2 同款检测（代码块与引号提及豁免） |
| `add_term(term, expected, note)` | 数据飞轮：追加用户词条，term 支持 `re:` 前缀 |

定位：拉模式知识层，不替代 L1（推送预防）与 L2（外部检测）——
模型感知不到自己在说翻译腔（P3），不会总记得主动查询，外部检测仍是兜底。

符号链接部署（`setup-claude.sh`）不自动注册 MCP，手动执行：

```
claude mcp add term-dict -- python3 "$HOME/.claude/hooks/term-dict-server.py"
```

## 安装

```
/plugin marketplace add ProjAnvil/MindForge
/plugin install style-rules-zh-cn@mindforge
```

依赖系统 `python3`。

## 这套东西到底要花多少：eval-zh-guard.py

装了它，每轮多付多少 token、多等多少毫秒。三个对照组，把账算到能归因为止：

| 对照组 | 是什么 | 量的东西 |
|---|---|---|
| 基线 | 完全没装这套 hook | 恒为 0，对比的零点 |
| 空字典 | hook 装了，但字典一张词条都没有 | 5 条规则文本 + hook 引擎的成本 |
| 完整字典 | hook + 现在的字典 | 前两者 + 字典本身的边际成本 |

```
python3 hooks/eval-zh-guard.py               # 打印对比表
python3 hooks/eval-zh-guard.py --json        # 机器可读，CI diff 用
python3 hooks/eval-zh-guard.py --rounds 20   # 计时轮数
python3 hooks/eval-zh-guard.py --turns 10 50 # 折算成几轮对话的累计 token
```

当前实测（`estimate` 后端，见下）：

| 每轮成本 | 基线 | 空字典 | 完整字典 |
|---|---|---|---|
| 注入字符 / token | 0 | 409 / 254 | 851 / **533** |
| 其中字典带来的边际 | — | 0 | **279 token** |
| L1 耗时（净，扣掉解释器启动） | 0 | ~30 ms | ~25 ms |
| L2 耗时（净） | 0 | ≈同上 | ~27 ms |

另外，**最贵的一项不在注入，而在拦截**：一旦命中，那条回复白写一遍还要重写一遍
（约 236 token）+ 重写指令 128 token，单次约 364 token；防循环上限是 10 分钟 3 次，
最坏窗口约 1092 token。所以省钱的优先级是：先让模型少踩词（规则注入 + term-dict
MCP 查词），再砍注入文本，几十毫秒那个量级不值得动。

token 计数优先 `tiktoken`（真值），装不上就退到写明公式的估算
（`中文字符 + 1.3 × 英日词数`），表头会标注用的是哪个。注意 tiktoken 首次使用要联网
下载词表，离线环境会落到估算。

（另有一个 `eval-tidy-dict.py`，只评测 tidy 整理前后的行为等价性，与上面的方案级
成本不是一回事。）

## 字典：三级加载 + 安装迁移 + 版本同步

字典按三级加载，优先级从低到高（后加载覆盖先加载）：

1. **内置**：本目录 `terminology.tsv`，随插件分发，是发布源；
2. **用户级**：`~/.claude/zh-guard/terminology.tsv`（`ZH_GUARD_HOME` 可改），
   首次 hook 运行时从内置迁移过去，升级时保留自加词条；
3. **项目级**：`mindforge.zh-dict.tsv`，放在项目根随仓库提交，团队共享
   （cspell 项目词典同款机制）。hook 从 stdin 的 `cwd` 逐级向上发现，
   遇到含 `.git` 的目录即停——项目根之外的词典不生效。

展示顺序（L1 注入）与覆盖顺序相反：项目级 → 用户级 → 内置，
越具体越靠前，超出注入上限时先牺牲宽泛层。L2 出口检测、文件写检测、
L1 注入三个执行点都吃三级合并结果；term-dict MCP 是常驻进程拿不到
会话 cwd，只合并前两级。

**部署要求**：`zh_guard_common.py` 必须与 hook 脚本同目录
（插件市场安装自动满足；手动复制部署时别漏拷这个文件）。

- **发布源**：本目录 `terminology.tsv`（在 MindForge 仓库内维护）。
- **安装时迁移**：首次 hook 运行时，字典被复制到
  `~/.claude/zh-guard/terminology.tsv`。
- **版本同步**：自带字典里有一行 `# @sync <版本>`。当本地副本缺这个标记
  （旧版本安装）或版本落后时，hook 会把自带字典刷新到本地，
  **并保留用户自加的词条**（第一列不在自带字典里的行）。

  这是刻意的取舍：否则出厂时被复制走的写法（曾经的
  `下一刀 → 下一个削减项`）会永久屏蔽后续修正。用户对自带词条的本地改写
  会在字典升级时被新版覆盖；想完全自控请用自己的 key，或用
  `ZH_GUARD_DICT` 指向自己的字典文件。
- **运行时合并**：读取插件自带 + `~/.claude/zh-guard/` 两份字典，用户条目优先。
- **用户词条**：直接编辑 `~/.claude/zh-guard/terminology.tsv`。
  格式：TSV 三列 `直译词<TAB>期望写法<TAB>说明`，`#` 开头为注释。
  带可变数字等模式用正则词条：第一列以 `re:` 开头
  （如 `re:第\s*\d+\s*刀`），无效正则自动跳过。
  词条要写精确（「病灶实验」而非「病灶」），避免误伤医学等合法语境。
  会话里看到新直译词 → 补一行 → 当轮注入即生效。

### 手动整理字典：tidy-dict.py

字典是给人看的文件，手改之后跑一遍体检 + 排版：

```
python3 hooks/tidy-dict.py                      # 只读体检，打印报告
python3 hooks/tidy-dict.py --write              # 体检 + 写回排版（对齐、去重）
python3 hooks/tidy-dict.py --check              # 有硬错误时退出码 1（可挂 pre-commit）
python3 hooks/tidy-dict.py --path myspace.tsv   # 只处理指定文件
```

默认同时处理自带字典和 `~/.claude/zh-guard/` 下的用户字典。它会：

1. **排版**：按最宽词条补空格，三列对齐（中文按两格宽算），注释和分组原样保留；
2. **归一化**：去 BOM、去多余空白、约定行尾；
3. **去重**：同一词条保留最后一次出现（与运行时「用户条目优先」一致）；
4. **体检**：坏正则、缺第二列、重复词条，逐条报告；`--check` 时非零退出。

只读体检不会动文件，可以随便跑。排版是幂等的：再跑一次不会有新变化。

### 整理到底有用没用：eval-tidy-dict.py

道理讲再多不如一组数。`eval-tidy-dict.py` 用当前字典程序化地造一份「整理前」
的脏副本（重复词条、参差空白、BOM、多余空行），再跑一遍 tidy 得到「整理后」，
然后对比三件事：

| 维度 | 怎么看 | 当前实测 |
|---|---|---|
| 行为等价 | 20 条标注语料逐条跑真实 L2，判定必须一模一样 | 完全一致，precision/recall/F1 = 1.0 |
| 成本 | L1 注入的字符数 / token 数 / 词条数 | 持平，不反弹 |
| 耗时 | hook 端到端（含解释器启动）+ 字典解析单独计时 | 端到端 ~150 ms（噪声 ±8 ms），字典解析 0.028 → 0.023 ms |

```
python3 hooks/eval-tidy-dict.py                  # 打印对比表
python3 hooks/eval-tidy-dict.py --json           # 机器可读指标，CI 里 diff 用
python3 hooks/eval-tidy-dict.py --rounds 30      # 计时多跑几轮压噪声
python3 hooks/eval-tidy-dict.py --corpus X.tsv   # 换成自己的语料（句子<TAB>block\|pass）
```

token 计数优先用 `tiktoken`（装了更准），没装就用标注清楚的估算公式，表头会写明
用的是哪个。语料默认 20 条，覆盖三类：真用了直译词、干净的中文、豁免区（引号
提及和代码块）。

一个值得记的**负结果**：想靠去重省 token 是省不出来的——加载层本来就按唯一键
合并。整理改的是文件卫生和可读性，不是运行开销；真正的 token 杠杆在「注入上限
40 条 + term-dict MCP 拉模式」这一层。
- **期望写法怎么写**（第二列，最容易写坏的一列）：

  1. 写中文作者真会说的话，不要「为翻译而翻译」的机器名词。
     反例 `下一刀 → 下一个削减项`；正例 `下一刀 → 下一处可以精简的部分`。
  2. 要能直接替换原文里的直译词，所以不带括号注释、不写整句模板。
  3. 拿不准译法的名词保留英文原词：token、agent、hook、ghost token 不译。
  4. 有社区定译的用定译：ablation study=消融实验，ground truth=真值。

  英文原词和括号里的一句解释请放第三列（说明），不要塞进第二列。
- **回馈上游**：通用性强的词条欢迎提交回 MindForge 仓库的
  `hooks/terminology.tsv`。

## 停用与恢复

```
export ZH_GUARD_OFF=1        # 本会话停用（仅 zh-guard 部分）
touch ~/.claude/zh-guard/OFF # 持久停用
rm ~/.claude/zh-guard/OFF    # 恢复
```

## 检测语义（L2）

- 第一列按字面子串匹配 assistant 消息正文。
- 豁免区：围栏代码块、行内代码、「」与""引号内提及。
- 防循环：同一消息每会话只阻断一次；10 分钟窗口内最多阻断 3 次。
- 状态存 `$TMPDIR/zh-guard/`。

## 测试

```
python3 hooks/test_zh_guard.py         # zh-guard hooks（24 项，含三级词典、zcode 契约、文件写入口、句式词条）
python3 hooks/test_term_dict_mcp.py    # term-dict MCP（5 项）
python3 hooks/test_tidy_dict.py        # 字典整理/体检（5 项）
python3 hooks/test_eval_tidy_dict.py   # tidy 评测工具自身（5 项）
python3 hooks/test_eval_zh_guard.py    # 方案成本评测工具自身（6 项）
bash hooks/test-inject-style-rules.sh  # 写作规范（14 项）

python3 hooks/eval-zh-guard.py         # 装 vs 不装：token 与耗时对比
python3 hooks/eval-tidy-dict.py        # 整理前后：行为等价 + 成本对比
```

改 hook 前先补测试（TDD）。

## 环境变量

| 变量 | 作用 |
|---|---|
| `ZH_GUARD_HOME` | 用户目录（默认 `~/.claude/zh-guard`），存用户词条与 OFF 文件 |
| `ZH_GUARD_DICT` | 指定单一字典文件（调试用，跳过合并与迁移） |
| `ZH_GUARD_STATE_DIR` | 防循环状态目录（默认 `$TMPDIR/zh-guard`） |
| `ZH_GUARD_OFF` | 任意非空值停用 zh-guard |
