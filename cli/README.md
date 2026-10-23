# mindforge CLI

MindForge 的安装器与工具箱（Go 编写，仅标准库，零外部依赖）。像 `eslint --init`
和 `cspell --init` 一样，一条命令完成安装、初始化和诊断。

hook 执行器（注入 / 检测脚本）仍是仓库里那几个 fail-open 的 Python 脚本——
本 CLI 是**安装器、生成器和医生**，不是运行时。CLI 把整个 hook 载荷
（脚本 + 内置词典 + 写作规范）嵌入单一二进制，`go build` 一次，安装不再依赖
仓库检出。

## 命令

```
mindforge install [--lang=zh-cn|en] [--platform=claude,zcode] [--yes]
    交互式用户级安装：检测本地 agent → 选择平台 → 选择主语言 → 注册
    hook（写入各平台自己的配置格式）→ 播种用户词典 → 打印摘要。
    --yes 全部取默认（CI / 脚本友好）。

mindforge init dict [--lang=zh-cn] [--force]
    在当前目录生成项目级词典 mindforge.zh-dict.tsv（模板全注释，
    不会误伤；提交进仓库即团队共享）。

mindforge doctor
    体检：python3 运行时、三级词典层级与条数、各平台 hook 注册状态、
    旧目录（~/.claude/zh-guard）残留提醒、Kimi 支持状态。
```

## 平台支持

| 平台 | 配置写入位置 | hook 脚本目录 | 状态 |
|---|---|---|---|
| Claude Code | `~/.claude/settings.json`（保留既有配置与外来 hook） | `~/.claude/MindForge/hooks/` | 支持（含 Subagent 事件） |
| zcode | `~/.zcode/cli/config.json`（`hooks.enabled=true`，保留 timeoutMs 等字段） | `~/.zcode/mindforge/hooks/` | 支持（仅 zcode 的 7 事件；Stop 走 `--platform` 参数） |
| Codex | `~/.codex/hooks.json`（单一格式，不碰 config.toml） | `~/.codex/mindforge/hooks/` | 支持（需 codex 0.145+；文件编辑工具名是 apply_patch/Edit/Write；首次使用需在 `/hooks` 里信任；Stop 走 `--platform`） |
| Kimi Code | `~/.kimi-code/config.toml` | — | 检测可见，暂不安装（上游 Stop payload 缺助手消息，issue #2123） |

用 `--platform` 指定装进哪个 harness（`claude` / `zcode` / `codex`，逗号分隔多个）；
不带该参数则交互式选择，`--yes` 默认装所有检测到的受支持平台。

安装是幂等的：重复 `mindforge install` 不会重复注册——旧条目按
`mindforge/hooks/` 路径标记识别并整体替换。外来的 hook 配置逐字节保留。

## 构建与测试

```
make cli        # 构建到 bin/mindforge
make cli-test   # go vet + go test ./cli/
go run ./cli doctor   # 不构建直接跑
```

嵌入的 hook 载荷来自仓库根 `assets.go`（`//go:embed hooks/...`）；
改 `hooks/` 下的脚本后重新 `make cli` 即可让安装器分发新版。

## 路线图

- `mindforge add <term>` — 词条飞轮 CLI 化（--scope project|user）
- `mindforge uninstall` — 反安装（清理干净）
- Kimi Code 安装（等上游 Stop payload 修复）
- charmbracelet TUI（当前为可脚本化的编号提示，交互层保持薄）
