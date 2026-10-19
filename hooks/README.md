# style-rules-zh-cn 插件（中文写作规范 + 翻译腔防御）

MindForge 中文 hook 插件。设计文档：WorkBuddy `zh-guard-spec-v2.0.md`（zh-guard 部分）。

## 结构

| 组件 | 文件 | 事件/通道 | 职责 |
|---|---|---|---|
| 写作规范 | inject-style-rules.sh | SessionStart / UserPromptSubmit / SubagentStart | 注入受控写作规范（中文+英文） |
| L0 字典 | terminology.tsv | - | 术语字典（数据飞轮，仓库内维护） |
| L1 术语注入 | inject.py | UserPromptSubmit | 每轮注入术语规范 + 「直译词→期望写法」对照 |
| L2 出口检测 | inspect.py | Stop / SubagentStop | 命中直译词要求重写（按地道措辞重写整句） |
| 知识层（拉模式） | term-dict-server.py | MCP（term-dict） | 按需查词 / 交付前自查 / 飞轮入库 |
| 字典整理 | tidy-dict.py | 手动运行 | 排版对齐 + 体检（去重、坏正则、缺列） |
| 整理效果评测 | eval-tidy-dict.py | 手动运行 | 前后对比：行为等价 + token/字符 + 耗时 |

所有 hook 全部 fail-open：任何异常静默放行，绝不卡死会话。

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

## 字典：安装迁移 + 版本同步

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
30 条 + term-dict MCP 拉模式」这一层。
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
python3 hooks/test_zh_guard.py         # zh-guard hooks（16 项）
python3 hooks/test_term_dict_mcp.py    # term-dict MCP（5 项）
python3 hooks/test_tidy_dict.py        # 字典整理/体检（5 项）
python3 hooks/test_eval_tidy_dict.py   # 评测工具自身（5 项）
bash hooks/test-inject-style-rules.sh  # 写作规范（14 项）

python3 hooks/eval-tidy-dict.py        # 整理前后的效果/成本/耗时评测
```

改 hook 前先补测试（TDD）。

## 环境变量

| 变量 | 作用 |
|---|---|
| `ZH_GUARD_HOME` | 用户目录（默认 `~/.claude/zh-guard`），存用户词条与 OFF 文件 |
| `ZH_GUARD_DICT` | 指定单一字典文件（调试用，跳过合并与迁移） |
| `ZH_GUARD_STATE_DIR` | 防循环状态目录（默认 `$TMPDIR/zh-guard`） |
| `ZH_GUARD_OFF` | 任意非空值停用 zh-guard |
