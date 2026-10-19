# zh-guard（MindForge 插件版）

中文翻译腔防御系统。设计文档：WorkBuddy `zh-guard-spec-v2.0.md`（唯一权威）。

## 结构

| 层 | 文件 | 事件 | 职责 |
|---|---|---|---|
| L0 | terminology.tsv | - | 术语字典（数据飞轮） |
| L1 | inject.py | UserPromptSubmit | 每轮注入术语规范 + 负面清单 |
| L2 | inspect.py | Stop / SubagentStop | 出口检测，命中直译词要求重写 |

三层全部 fail-open：任何异常静默放行，绝不卡死会话。

## 安装

```
/plugin marketplace add ProjAnvil/MindForge
/plugin install zh-guard@mindforge
```

依赖系统 `python3`。与 `style-rules-zh-cn` 配套使用：style-rules 管句式（P2），
zh-guard 管术语直译（P1）。

## 字典维护（数据飞轮）

- 插件自带默认字典：本目录 `terminology.tsv`（随插件更新）。
- **用户词条**：写到 `~/.claude/zh-guard/terminology.tsv`，与默认字典合并，
  同名词条用户优先。插件更新不会覆盖用户词条。
- 格式：TSV 三列 `直译词<TAB>期望写法<TAB>说明`，`#` 开头为注释。
- 词条要写精确（「病灶实验」而非「病灶」），避免误伤医学等合法语境。
- 会话里看到新直译词 → 补一行 → 当轮注入即生效（L1 每次现读字典）。

## 停用与恢复

```
export ZH_GUARD_OFF=1        # 本会话停用
touch ~/.claude/zh-guard/OFF # 持久停用
rm ~/.claude/zh-guard/OFF    # 恢复
```

## 检测语义

- 第一列按字面子串匹配 assistant 消息正文。
- 豁免区：围栏代码块、行内代码、「」与""引号内提及。
- 防循环：同一消息每会话只阻断一次；10 分钟窗口内最多阻断 3 次。
- 状态存 `$TMPDIR/zh-guard/`。

## 测试

```
python3 test_zh_guard.py
```

12 项测试，覆盖注入格式、阻断与放行、代码块/引号豁免、fail-open、
防循环、kill switch、用户字典合并与覆盖。改 hook 前先补测试（TDD）。

## 环境变量

| 变量 | 作用 |
|---|---|
| `ZH_GUARD_HOME` | 用户目录（默认 `~/.claude/zh-guard`），存用户词条与 OFF 文件 |
| `ZH_GUARD_DICT` | 指定单一字典文件（调试用，跳过合并） |
| `ZH_GUARD_STATE_DIR` | 防循环状态目录（默认 `$TMPDIR/zh-guard`） |
| `ZH_GUARD_OFF` | 任意非空值停用 |
