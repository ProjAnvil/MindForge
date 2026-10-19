# style-rules-zh-cn 插件（中文写作规范 + 翻译腔防御）

MindForge 中文 hook 插件。设计文档：WorkBuddy `zh-guard-spec-v2.0.md`（zh-guard 部分）。

## 结构

| 组件 | 文件 | 事件 | 职责 |
|---|---|---|---|
| 写作规范 | inject-style-rules.sh | SessionStart / UserPromptSubmit / SubagentStart | 注入受控写作规范（中文+英文） |
| L0 字典 | terminology.tsv | - | 术语字典（数据飞轮，仓库内维护） |
| L1 术语注入 | inject.py | UserPromptSubmit | 每轮注入术语规范 + 负面清单 |
| L2 出口检测 | inspect.py | Stop / SubagentStop | 命中直译词要求重写 |

所有 hook 全部 fail-open：任何异常静默放行，绝不卡死会话。

## 安装

```
/plugin marketplace add ProjAnvil/MindForge
/plugin install style-rules-zh-cn@mindforge
```

依赖系统 `python3`。

## 字典的安装时迁移

- **发布源**：本目录 `terminology.tsv`（在 MindForge 仓库内维护）。
- **安装时迁移**：首次 hook 运行（或 `setup-claude.sh` 安装）时，
  字典被复制到 `~/.claude/zh-guard/terminology.tsv`，绝不覆盖已有文件。
- **运行时合并**：读取插件自带 + `~/.claude/zh-guard/` 两份字典，
  用户条目优先。插件更新带来的新词条自动生效，用户词条不丢。
- **用户词条**：直接编辑 `~/.claude/zh-guard/terminology.tsv`。
  格式：TSV 三列 `直译词<TAB>期望写法<TAB>说明`，`#` 开头为注释。
  词条要写精确（「病灶实验」而非「病灶」），避免误伤医学等合法语境。
  会话里看到新直译词 → 补一行 → 当轮注入即生效。
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
python3 hooks/test_zh_guard.py        # zh-guard（13 项）
bash hooks/test-inject-style-rules.sh # 写作规范（14 项）
```

改 hook 前先补测试（TDD）。

## 环境变量

| 变量 | 作用 |
|---|---|
| `ZH_GUARD_HOME` | 用户目录（默认 `~/.claude/zh-guard`），存用户词条与 OFF 文件 |
| `ZH_GUARD_DICT` | 指定单一字典文件（调试用，跳过合并与迁移） |
| `ZH_GUARD_STATE_DIR` | 防循环状态目录（默认 `$TMPDIR/zh-guard`） |
| `ZH_GUARD_OFF` | 任意非空值停用 zh-guard |
