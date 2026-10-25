# style-rules-zh-cn：方案 A，只注入写作指导

默认回答流程只给已有模型请求添加简短写作规则，不调用词典工具、
不检查或退回已生成回复，不启动额外模型审稿。中文使用简要表达原则，
英文插件保留 ASD-STE100。词典与研究脚本保留，但不会默认加载。

## 结构

| 组件 | 文件 | 事件/通道 | 职责 |
|---|---|---|---|
| 默认注入器 | inject-style-rules.sh | SessionStart / UserPromptSubmit（+ SubagentStart，仅 Claude） | 读取选定语言的一份规则，不调用模型 |
| 中文规则 | style-rules-zh.md | prompt 内容 | 简短、自然、保留语境和事实 |
| 英文规则 | style-rules-en.md | prompt 内容 | ASD-STE100 风格指导 |
| 词典与维护 | terminology.tsv / term-dict-server.py / tidy-dict.py | 仅显式手动使用 | 不注册到默认回复流程 |
| 历史检查器 | inject.py / inspect.py / inspect-file.py | 仅手动实验 | 不随 CLI 默认安装，不注册成自动 hook |
| 成本实验 | evals/scripts/zh_pregen_cost.py / zh_dict_cost.py | 手动运行 | 比较规则、工具查询和 Stop 返修的代价 |

默认注入器在规则文件缺失时放行，不阻断回复。模型是否遵守规则仍不是程序保证，
但默认方案不会因查词或审批新增一个模型往返。
工程检查信息（测试描述、断言失败、参数校验、异常诊断、词典体检和成本评测报告）
统一使用英文。中文词条、含义、测试语料及给 agent 的中文写作反馈保持原语言；
诊断中引用的原始数据也不翻译。

## 多平台

中文和英文默认都只注入 prompt。`hooks/hooks.json` 仅含 SessionStart /
UserPromptSubmit；Claude 通过 `hooks/subagent-hooks.json` 额外注入 SubagentStart。
CLI 在 Claude Code、zcode、Codex 上注册同样的开始／提问事件；
zcode / Codex 不额外注册子代理事件。Kimi 的安装适配仍未提供。

默认配置没有 Stop、SubagentStop、PreToolUse、prompt 型审稿或 `mcpServers`。
升级安装只替换 MindForge 自己注册的配置，保留外来 hooks 和已有词典数据。
旧会话有配置快照，更新插件后必须新建会话；如之前独立注册过词典 MCP，
需要另行禁用，不能指望插件升级撤回已有会话中的工具或提示。

## term-dict MCP 服务（仅手动启用）

该服务保留在源代码中，但默认插件不注册、CLI 不安装，也不要求生成前调用。
用户明确需要词典资料或手动实验时，可自行注册源代码中的
`term-dict-server.py`。它是零依赖 Python stdio 实现，
与手动检查器共享检测引擎，每次调用现读；`mindforge_add_term`
写入 workspace 后，显式查询和预检传同一 `cwd` 即可读取。
可选 `cwd` 必须是绝对路径；
提供时与 hook 一样加载项目词表，不提供时只合并内置与用户级。

| 工具 | 用途 |
|---|---|
| `mindforge_lookup_term(query, cwd?)` | 双向查词：英文/中文子串匹配词语、建议写法、含义 |
| `mindforge_check_text(text, cwd?)` | 草稿保持不变，返回句子标注、段落及相关建议和含义 |
| `mindforge_add_term(term, cwd?, suggestion?, meaning?, scope?)` | 默认写 workspace；必须传其绝对路径 `cwd`。显式 `scope=user` 才写用户级 |
| `mindforge_init_dict(cwd)` | 初始化全注释三列词典；已有词典不覆盖，返回路径与创建状态 |

### workspace 词典维护

`mindforge_add_term` 默认 `scope` 为 `workspace`，不再默认追加到
`~/.claude/MindForge/terminology.tsv`。MCP 是常驻服务，不能把启动目录
猜成当前 workspace，因此 workspace 写入必须传有效目录的绝对路径 `cwd`；
缺失、相对路径、目录不存在都报错，不静默回退到用户级。

初始化和追加会复用从 `cwd` 向上找到的最近词典，遇到 `.git` 目录或文件即停。
没有词典时在该 Git 根创建；没有 Git 边界时在传入的目录创建。
`mindforge_add_term` 会在需要时自动初始化，单独初始化则调用
`mindforge_init_dict`：

```json
{"cwd": "/absolute/path/to/workspace"}
```

返回的 `structuredContent` 为
`{"path": "/absolute/path/to/workspace/mindforge.zh-dict.tsv", "created": true}`。
重复调用返回 `created: false`，不改已有文件。

追加含义示例，工具名为 `mindforge_add_term`：

```json
{
  "cwd": "/absolute/path/to/workspace",
  "term": "病灶分析",
  "meaning": "本项目指排查问题根因，不指定具体实验方法"
}
```

只有用户明确要求全局共享时，才指定 `scope: "user"`；此时无需 `cwd`。
返回文本显示实际写入路径，多个 workspace 不共享隐式目录状态。
初始化模板来自 `project-dict-template.tsv`，CLI 和 MCP 使用同一份内容。

### 手动草稿检查

只有用户明确需要时才提交中文草稿，结合用户问题、对话背景和项目含义复核标注，
只在必要时局部润色，或判断原文合理并保留。MCP 不改写草稿，返回：

- `draft`：未经修改的完整草稿，批注不会混入正文。
- `draft_id`：完整草稿的 SHA-256，用于区分不同草稿。
- `annotations`：所有非重叠命中，包含 `term`、`text`、可空的 `suggestion`
  和 `meaning`，以及 `start`、`end`、`line`、`column`。
  每条还有完整 `sentence`、其 `sentence_start` / `sentence_end`、段落 `context`、
  `rule_id`、`annotation_id` 和 `draft_id`。用户无需填写这些字段。
- `needs_review`：是否有需要按语境复核的批注，不表示原文一定有错。

`start/end` 是原文中从 0 开始的字符偏移，`end` 不包含在匹配内；
`line/column` 从 1 开始，句子范围同样使用字符偏移；所有位置对应 `draft`。
句子按中文句末标点、空白前的英文句点和换行定位，保留行内代码及引号提及，
不是句法分析；段落按空行分隔。Markdown 标题和列表项以行作为边界。
相同草稿和词典得到确定的标注 ID；草稿、词条含义或建议变化后重新检查，
不能拿旧标注的位置继续修改。标注 ID 不会写回词典，也不是全局忽略规则。

例如项目说明「机械胳膊指科幻人物的身体部件」时，
`小说里，他举起机械胳膊挡住攻击。` 原稿不变，批注给出该句和项目含义，
由 agent 判断是否需要润色，而不是强行改成工业术语。
仅登记词语时可查询、可注入，但不会产生需要改写的批注或 Stop 拦截。
只改标注所在的必要句子，其他句子、数字、代码和结论保持不变；
允许保留合法用法，不能编造用户未提供的含义。

重叠命中采用从左到右、同起点最长优先，不对同一处重复批注。
无效正则会记录错误并跳过，词典最多三列；空建议与空含义不是错误。
所有建议都只是参考，不提供自动替换动作或显示前换词。

定位：拉模式知识层，不替代 L1（推送预防）与 L2（外部检测）——
模型感知不到自己在说翻译腔（P3），不会总记得主动查询，外部检测仍是兜底。
提示词不能保证每次调用工具，Stop 仍检查最终原稿；没有新增外部模型调用或分词依赖。

默认安装不提供 MCP。如确实需要，手动指向仓库源代码：

```
claude mcp add term-dict -- python3 /absolute/path/to/MindForge/hooks/term-dict-server.py
```

## 安装

```
/plugin marketplace add ProjAnvil/MindForge
/plugin install style-rules-zh-cn@mindforge
```

依赖系统 `python3`。

开发工作区的修改不会自动更新已加载的插件缓存。升级方案 A 后新建会话；
不要把仍在运行的旧检查器、独立 MCP 或外来 hook 的行为误认为默认方案 A。
本次三列设计不读取旧第四列动作；如有旧词典，删除第四列，把必要说明写进第三列。
若曾手动启用显示替换 hook，需要移除该手动配置；本版本不再分发相关脚本。

## 成本实验与历史方案对比

生产默认选择 A，以下工具查询、完整词典注入和 Stop 返修仅供手动对照研究。
保存的报告记录当时的 prompt 和模型 usage；规则变更后应重新运行，
不能把旧快照中的 token 数直接当成当前版本的注入开销。

### 短／中／长上下文与真实改写对照

若只比较两个**生成前**方案，使用独立实验：

```sh
evals/.venv/bin/python evals/scripts/zh_pregen_cost.py --live --rounds 3 \
  --output evals/reports/zh-pregen-cost.json
evals/.venv/bin/python -m pytest evals/tests/test_zh_pregen_cost.py -q
```

A 组只给简短写作指导，一次请求直接回答；B 组用相同指导和问题，
先通过原生 function calling 调用真实 `mindforge_lookup_term`，获取含义后再回答。
两组背景、问题和回答长度预算一致，均无 Stop、草稿预检或生成后返修。
B 组计入工具定义、选择工具的输出、实际返回内容和两次模型请求的全部 usage。
原生 `tool_choice` 约束用于确保实验中确实拿到语境，不用于证明单靠提示词就能必然触发工具。
只开放这一个只读工具；不会调用词典写入工具。
JSON 保留各请求 usage、缓存计数、工具参数和返回内容；本地工具耗时包含 MCP 子进程启动。

使用 `evals/scripts/zh_dict_cost.py` 评测当前的「句子标注 → Stop 续写润色」，
不是字符串替换。短、中、长合成背景默认分别为 2,000 / 16,000 / 64,000 个字符；
回复草稿长度保持不变，分别测试命中词典和已经自然的未命中文本。
不把长回复与长上下文混为一谈。

本地模式调用真实注入／Stop／MCP 脚本，token 文本计数明确标记估算，
没有真实模型时不报告模型耗时。真实模式复用 `evals/.env` 中的
`SMELT_API_KEY`、`SMELT_BASE_URL`、`SMELT_AGENT_MODEL`，仅提交合成测试语料：

```sh
# Local hook measurements and explicitly estimated content tokens, no model calls
evals/.venv/bin/python evals/scripts/zh_dict_cost.py --hook-rounds 20

# Actual provider usage and paired baseline vs dictionary + polishing requests
evals/.venv/bin/python evals/scripts/zh_dict_cost.py --live \
  --hook-rounds 20 --model-rounds 3 \
  --output evals/reports/zh-dict-context-cost.json

# Deterministic benchmark regression tests
evals/.venv/bin/python -m pytest evals/tests/test_zh_dict_cost.py -q
```

真实模式平衡两组请求的先后顺序，记录每组生成及续写请求汇总的输入／输出 token、
缓存命中、实际请求耗时和 hook 耗时。命中时包括新增续写请求再次读取上下文的成本，
而不是只数返回批注或改写后的回答。模型未逐字生成同一草稿时明确报错，
不能把不一致的样本当成有效对照。

报告保存 JSON 原始指标与同名 Markdown 汇总，检查数字／单位是否保留，
并展示真实改写结果。剩余标注不等于错误；不额外调用 judge 模型评判语义。
处理 token 数不等于收费 token，缓存命中需单独考虑；网络、缓存和样本量会影响耗时。
该研究衡量受控样本的成本，不代表真实会话的命中率，也不是完整 coding agent 的性能评测。

下面的单次 hook 统计是早期参考，不包括长上下文在模型续写请求中的完整重读成本；
当前端到端数据应以新的上下文对照报告为准。

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

## 手动词典工具：三级加载 + 首次运行迁移 + 版本同步

本节仅描述显式启用的词典工具；默认写作 hook 不读取、迁移或同步词典。

字典按三级加载，优先级从低到高（后加载覆盖先加载）：

1. **内置**：本目录 `terminology.tsv`，随插件分发，是发布源；
2. **用户级**：`~/.claude/MindForge/terminology.tsv`（`ZH_GUARD_HOME` 可改），
   首次 hook 运行时从内置迁移过去，升级时保留自加词条；
   旧版安装在 `~/.claude/zh-guard/` 的字典与 OFF 标记会在新版首次运行时
   自动搬迁过来（旧目录不删除，确认无误后可手动清理）；
3. **项目级**：`mindforge.zh-dict.tsv`，放在项目根随仓库提交，团队共享
   （cspell 项目词典同款机制）。hook 从 stdin 的 `cwd` 逐级向上发现，
   遇到含 `.git` 的目录即停——项目根之外的词典不生效。

展示顺序（L1 注入）与覆盖顺序相反：项目级 → 用户级 → 内置，
越具体越靠前，超出注入上限时先牺牲宽泛层。L2 出口检测、文件写检测、
L1 注入三个执行点都吃三级合并结果；term-dict MCP 是常驻进程拿不到
会话 cwd，只有调用时显式提供绝对路径 `cwd` 才合并项目级。

**手动工具要求**：`zh_guard_common.py` 和 `project-dict-template.tsv` 必须与 Python
工具脚本同目录，不能只复制 `term-dict-server.py`。默认安装没有这套 Python 载荷。

- **发布源**：本目录 `terminology.tsv`（在 MindForge 仓库内维护）。
- **手动工具首次运行迁移**：字典被复制到
  `~/.claude/MindForge/terminology.tsv`。
- **版本同步**：自带字典里有一行 `# @sync <版本>`。当本地副本缺这个标记
  （旧版本安装）或版本落后时，hook 会把自带字典刷新到本地，
  **并保留用户自加的词条**（第一列不在自带字典里的行）。

  这是刻意的取舍：否则出厂时被复制走的写法（曾经的
  `下一刀 → 下一个削减项`）会永久屏蔽后续修正。用户对自带词条的本地改写
  会在字典升级时被新版覆盖；想完全自控请用自己的 key，或用
  `ZH_GUARD_DICT` 指向自己的字典文件。
- **运行时合并**：读取插件自带 + `~/.claude/MindForge/` 两份字典，用户条目优先。
- **用户词条**：直接编辑 `~/.claude/MindForge/terminology.tsv`。
  格式：TSV `词语<TAB>建议写法（可空）<TAB>含义或语境说明（可空）`，
  `#` 开头为注释。两列表示词语和建议写法，不把第二列当作含义。
  仅登记一个词语也可以；有含义而没有建议时保留空的第二个单元格。
  注释只留格式、简短分组和 `@sync` 标记；不要为了填满三列而猜测译法。
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

默认同时处理自带字典和 `~/.claude/MindForge/` 下的用户字典。它会：

1. **排版**：按最宽词条补空格，三列对齐（中文按两格宽算），注释和分组原样保留；
2. **归一化**：去 BOM、去多余空白、约定行尾；
3. **去重**：同一词条保留最后一次出现（与运行时「用户条目优先」一致）；
4. **体检**：坏正则、多余列、重复词条，逐条报告；`--check` 时有硬错误则非零退出。

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
- **建议与含义怎么写**：

  1. 写中文作者真会说的话，不要「为翻译而翻译」的机器名词。
     反例 `下一刀 → 下一个削减项`；正例 `下一刀 → 下一处可以精简的部分`。
  2. 第二列只作参考，不是标准答案；只知道意思时留空，把含义写在第三列。
  3. 拿不准译法的名词保留英文原词：token、agent、hook、ghost token 不译。
  4. 优先保留原意，不要为了套专业术语而改成别的意思。
     例如「病灶分析」在排查问题时说「分析问题原因」，不能直接认作 ablation。

  英文原词和语境说明放第三列，不用用户编写复杂的规则或句子标注。
- **回馈上游**：通用性强的词条欢迎提交回 MindForge 仓库的
  `hooks/terminology.tsv`。

## 手动检查器停用与恢复

下面的开关只用于可选的历史检查器。默认写作注入请通过客户端的插件／hook 开关管理。

```
export ZH_GUARD_OFF=1        # 本会话停用（仅 zh-guard 部分）
touch ~/.claude/MindForge/OFF # 持久停用
rm ~/.claude/MindForge/OFF    # 恢复
```

## 检测语义（L2）

- 第一列按字面子串匹配 assistant 消息正文。
- 只有建议或含义非空的条目参与复核；仅登记词语不阻断。
- 豁免区：围栏代码块、行内代码、「」与""引号内提及。
- 防循环：同一消息每会话只阻断一次；10 分钟窗口内最多阻断 3 次。
- 状态存 `$TMPDIR/zh-guard/`。

## 测试

```
python3 hooks/test_zh_guard_common.py  # 三列词典、完整句子/段落、标注标识与保护区
python3 hooks/test_scheme_a.py        # 默认入口只注入规则、不挂载工具或模型审稿
python3 hooks/test_english_diagnostics.py # 工程检查使用英文，中文产品资料保持原文
python3 hooks/test_english_installation.py # 英文只注入规范，切换语言保留数据和外来 hook
python3 hooks/test_zh_guard.py         # 注入、项目含义、Stop 与文件写入口
python3 hooks/test_term_dict_mcp.py    # 原稿不变的句子标注、词语/含义入库与查询
python3 hooks/test_tidy_dict.py        # 空单元格保留、三列体检与排版幂等
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
| `ZH_GUARD_HOME` | 用户目录（默认 `~/.claude/MindForge`），存用户词条与 OFF 文件 |
| `ZH_GUARD_DICT` | 指定单一字典文件（调试用，跳过合并与迁移） |
| `ZH_GUARD_STATE_DIR` | 防循环状态目录（默认 `$TMPDIR/zh-guard`） |
| `ZH_GUARD_OFF` | 任意非空值停用 zh-guard |
