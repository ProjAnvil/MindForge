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

设计原则（fail-open）：任何异常一律静默退出 0，绝不阻断用户输入。
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
        "1. 术语有中文社区定译就用定译：ablation study=消融实验，"
        "hallucination=幻觉，prompt=提示词。\n"
        "2. 术语没有通用定译就保留英文原词：token、agent、hook、embedding、"
        "ghost token。中英混排是中文技术写作的惯例。\n"
        "3. 禁止字面直译英文黑话。\n"
        "4. 以下直译词禁用，按箭头右侧的写法表达；右侧是高亮条款所指的中文措辞，"
        "拿不准就保留英文原词："
        + (pairs + more if pairs else "暂无") +
        "\n5. 措辞要像人在说话：说「剩下的待办」「发现的问题」「这儿有个 bug」，"
        "别端着写成「遗留缺口」「结构性缺陷」这类从英文句型硬搬过来的词。"
        "汇报进展说「大致了解了」，别写「已初步清楚」。"
        "\n6. 英文名词短语别硬拼成中文合成词：slot key 说「slot 的 key」，"
        "key-value 就写 key-value，不写「槽键」「键-值关系」。"
        "名词叠着名词时，拆成短句直说。"
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
except Exception:
    # fail-open：任何未预期错误都放行。
    sys.exit(0)
