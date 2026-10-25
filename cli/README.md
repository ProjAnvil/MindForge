# mindforge CLI

MindForge 的安装器与工具箱（Go 编写，仅标准库，零外部依赖）。像 `eslint --init`
和 `cspell --init` 一样，一条命令完成安装、初始化和诊断。

默认 hook 只有 shell 写作提示注入，不运行 Python 检测或额外模型审稿。
CLI 内嵌注入脚本、写作规则及供手动命令使用的词典参考／模板，
`go build` 一次，安装无需仓库检出；可选 Python 词典工具不属于默认安装载荷。

## 命令

```
mindforge install [--lang=zh-cn|en] [--platform=claude,zcode] [--yes]
    交互式用户级安装：检测本地 agent → 选择平台 → 选择主语言 → 注册
    写作提示 hook（写入各平台自己的配置格式）→ 打印摘要，不创建词典。
    --yes 全部取默认（CI / 脚本友好）。

mindforge init dict [--lang=zh-cn] [--force]
    在当前目录生成项目级词典 mindforge.zh-dict.tsv（模板全注释，
    不会误伤；提交进仓库即团队共享）。三列分别是词语、可空的建议
    写法、可空的含义或语境说明，不要求用户提供替换词或 JSON 规则。

mindforge doctor
    体检：python3 运行时、三级词典层级与条数、各平台 hook 注册状态、
    旧目录（~/.claude/zh-guard）残留提醒、Kimi 支持状态。
    诊断结果、错误、警告与修复提示统一使用英文，不随主写作语言切换。
```

工程测试描述、断言失败和通用参数/配置校验错误也使用英文；
中文词典、初始化示例及产品写作提示不因此翻译。

### 中英文统一采用方案 A：只注入规则

`mindforge install --lang=zh-cn` 注入简短的自然中文表达指导；
`mindforge install --lang=en` 保留 ASD-STE100 风格的英文写作提示。
在 SessionStart / UserPromptSubmit 注入；Claude Code 还覆盖 SubagentStart。
两种模式都不创建词典，不注册词典注入、Stop / SubagentStop、
文件写检测、模型审稿或词典 MCP，不要求生成前调用工具。
运行时仅需 shell，不需要 Python。市场插件和 shell setup 采用同样边界。

升级安装时移除 MindForge 自己注册的旧词典检查，保留外来 hooks；
已有词典及文件不会删除，手动注册的 MCP 也不会擅自改动。
曾手动启用词典 MCP 的用户需要单独禁用它，并新建会话，才能完全使用无工具的默认流程。

### 可选手动项目词典

`mindforge init dict` 仍可显式创建三列资料文件，但默认写作 hook 不读取它。
实际文件使用 Tab 分隔，以下表格仅用于说明：

| 词语 | 建议写法 | 含义或语境说明 |
|---|---|---|
| 病灶分析 | 空单元格 | 本项目指排查问题根因，不指定具体实验方法 |
| 机械胳膊 | 空单元格 | 本项目指科幻角色的身体部件，不是工业设备 |
| 槽键 | slot 的 key | 指 slot 对象的 key |
| 星环 | 空单元格 | 空单元格 |

第二列为空时，两次 Tab 之间不填文字，不能把「留空」当作建议写法。
最后一行也可只写一个词语，仅作登记，不触发纠错。词典最多三列，
不需要第四列动作；所有建议由 agent 根据语境决定是否采纳，不自动换词。
已有两列文件仍表示「词语、建议写法」，含义必须放第三列。

仓库保留可手动启用的词典 MCP 工具，不自动注册或随默认安装复制。
显式启用后可调用 `mindforge_init_dict(cwd)` 初始化 workspace 词典，已有内容不会覆盖。
`mindforge_add_term` 默认写 workspace，必须传当前目录的绝对路径 `cwd`，
找不到词典时自动初始化；只有显式 `scope=user` 才写用户级词典。
MCP 从子目录调用时复用最近的项目词典；没有词典则选 Git 根
（支持 `.git` 目录和 worktree 的 `.git` 文件），无 Git 根时选传入的目录。
CLI 的 `mindforge init dict` 仍在执行命令的当前目录创建词典；
两种入口共用同一份注释模板。

手动 MCP `mindforge_check_text` 可接收草稿及绝对路径 `cwd`，
返回原稿和句子/段落批注。agent 只在必要时局部润色，也可保留原文，
不会让用户维护位置、标注 ID 或草稿版本。更完整的接口见
[hook 文档](../hooks/README.md#回答前预检)。

## 平台支持

| 平台 | 配置写入位置 | hook 脚本目录 | 状态 |
|---|---|---|---|
| Claude Code | `~/.claude/settings.json`（保留既有配置与外来 hook） | `~/.claude/MindForge/hooks/` | 支持（含 Subagent 事件） |
| zcode | `~/.zcode/cli/config.json`（`hooks.enabled=true`，保留 timeoutMs 等字段） | `~/.zcode/mindforge/hooks/` | 仅 SessionStart / UserPromptSubmit 注入 |
| Codex | `~/.codex/hooks.json`（单一格式，不碰 config.toml） | `~/.codex/mindforge/hooks/` | 仅开始／提问注入，首次使用需在 `/hooks` 里信任 |
| Kimi Code | `~/.kimi-code/config.toml` | — | 检测可见，尚未完成安装适配 |

用 `--platform` 指定装进哪个 harness（`claude` / `zcode` / `codex`，逗号分隔多个）；
不带该参数则交互式选择，`--yes` 默认装所有检测到的受支持平台。

安装是幂等的：重复 `mindforge install` 不会重复注册——旧条目按
`mindforge/hooks/` 路径标记识别并整体替换。外来的 hook 配置逐字节保留。

## 构建与测试

```
make cli        # 构建到 bin/mindforge
make cli-test   # go vet + go test ./cli/mindforge/
go run ./cli/mindforge doctor   # 不构建直接跑
```

或者直接从 GitHub 安装二进制（main 分支；CLI 发版后可换 `@latest`）：

```
go install github.com/ProjAnvil/MindForge/cli/mindforge@main
```

嵌入的 hook 载荷来自仓库根 `assets.go`（`//go:embed hooks/...`）；
改 `hooks/` 下的脚本后重新 `make cli` 即可让安装器分发新版。

## 路线图

- `mindforge add <term>` — 词条飞轮 CLI 化（--scope project|user）
- `mindforge uninstall` — 反安装（清理干净）
- Kimi Code 安装适配
- charmbracelet TUI（当前为可脚本化的编号提示，交互层保持薄）
