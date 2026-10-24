#!/usr/bin/env python3
"""zh-guard L1 注入层：UserPromptSubmit hook（MindForge style-rules-zh-cn 插件内）。

职责：每轮用户输入触发，向会话注入中文术语规范（additionalContext），
在生成阶段压住直译术语。预防为主，零延迟。

字典三级（项目级 > 用户级 > 内置），公共逻辑见 zh_guard_common.py：
  1. 内置 terminology.tsv 是发布源；
  2. 首次运行时迁移到 ~/.claude/MindForge/（用户可改，升级保留自加词条）；
  3. 项目级 mindforge.zh-dict.tsv 从 stdin 的 cwd 向上发现，
     展示顺序最靠前；
  4. ZH_GUARD_DICT 环境变量可指定单一字典文件（调试用）。

设计原则（fail-open）：异常报告到 stderr 后退出 0，不阻断用户输入。
停用方式：export ZH_GUARD_OFF=1，或创建 OFF 文件（ZH_GUARD_HOME/ 或插件目录）。
"""
import json
import sys

from zh_guard_common import (
    ensure_user_dict,
    is_off,
    load_display_entries,
    migrate_legacy_home,
)

MAX_SHOWN = 50


def build_context(entries):
    shown = entries[:MAX_SHOWN]
    pairs = "、".join(
        "%s→%s" % (bad, good) if good else bad for bad, good in shown
    )
    more = "" if len(entries) <= MAX_SHOWN else (
        "（仅列前 %d 条，其余用 term-dict MCP 的 lookup_term 查询）" % MAX_SHOWN
    )
    return (
        "【中文术语规范（自动注入）】\n"
        "1. 优先用自然、易懂的中文，保留原意，不要硬套专业术语。"
        "通用术语如 hallucination=幻觉，prompt=提示词。\n"
        "2. 术语没有通用定译就保留英文原词：token、agent、hook、embedding、"
        "ghost token。中英混排是中文技术写作的惯例。\n"
        "3. 禁止字面直译英文黑话。\n"
        "4. 以下是措辞检查规则，箭头右侧是建议写法；"
        "先判断原句语境，保留原意和合法用法，不要机械替换："
        + (pairs + more if pairs else "暂无") +
        "\n5. 措辞要像人在说话：说「剩下的待办」「发现的问题」「这儿有个 bug」，"
        "别端着写成「遗留缺口」「结构性缺陷」这类从英文句型硬搬过来的词。"
        "汇报进展说「大致了解了」，别写「已初步清楚」。"
        "\n6. 英文名词短语别硬拼成中文合成词：slot key 说「slot 的 key」，"
        "key-value 就写 key-value，不写「槽键」「键-值关系」。"
        "名词叠着名词时，拆成短句直说。"
        "\n7. 正式回答前，先把完整中文草稿交给 term-dict MCP 的 check_text 预检；"
        "有项目目录时传入绝对路径 cwd。使用 corrected_text 中的安全替换结果，"
        "remaining_findings 则结合原句改写，合法用法保留。修改后再次调用复查，"
        "不要把候选列表、占位符或「直接给结论」之类指令照抄到回答里。"
        "工具不可用时自行检查，不要声称已经调用；Stop 仍会补查。"
    )


def main():
    migrate_legacy_home()
    if is_off():
        sys.exit(0)
    ensure_user_dict()
    raw = sys.stdin.read()
    if not raw.strip():
        sys.exit(0)
    # prompt 内容不参与注入决策；cwd 用于发现项目级词典。
    try:
        payload = json.loads(raw)
    except Exception:
        sys.exit(0)
    cwd = payload.get("cwd") or ""
    ctx = build_context(load_display_entries(cwd))
    print(json.dumps({
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": ctx,
        },
    }, ensure_ascii=False))


try:
    main()
except SystemExit:
    raise
except Exception as exc:
    print("zh-guard 术语注入失败：%s" % exc, file=sys.stderr)
    sys.exit(0)
