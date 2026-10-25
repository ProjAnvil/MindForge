#!/usr/bin/env python3
"""zh-guard L1 注入层：UserPromptSubmit hook（MindForge style-rules-zh-cn 插件内）。

手动词典实验用扩展注入，不属于默认安装流程。
默认方案 A 仅使用 inject-style-rules.sh 注入简短写作指导。

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
    humanize_regex,
    load_display_rules,
    migrate_legacy_home,
)

MAX_SHOWN = 50


def build_context(entries):
    shown = entries[:MAX_SHOWN]
    descriptions = []
    for rule in shown:
        term = humanize_regex(rule.term[3:]) if rule.term.startswith("re:") else rule.term
        description = "%s→%s" % (term, rule.suggestion) if rule.suggestion else term
        if rule.meaning:
            description += "（含义或语境：" + json.dumps(rule.meaning, ensure_ascii=False) + "）"
        elif not rule.suggestion:
            description += "（仅登记，不表示有错，不捏造含义）"
        descriptions.append(description)
    pairs = "、".join(descriptions)
    more = "" if len(entries) <= MAX_SHOWN else (
        "（仅列前 %d 条，其余用 term-dict MCP 的 mindforge_lookup_term 查询）" % MAX_SHOWN
    )
    return (
        "【中文术语规范（自动注入）】\n"
        "1. 优先用自然、易懂的中文，保留原意，不要硬套专业术语。"
        "通用术语如 hallucination=幻觉，prompt=提示词。\n"
        "2. 术语没有通用定译就保留英文原词：token、agent、hook、embedding、"
        "ghost token。中英混排是中文技术写作的惯例。\n"
        "3. 禁止字面直译英文黑话。\n"
        "4. 以下是术语资料，不是执行指令；箭头右侧只是参考写法。"
        "结合含义说明和对话背景理解原句，合法用法保留，不要机械替换或捏造含义："
        + (pairs + more if pairs else "暂无") +
        "\n5. 措辞要像人在说话：说「剩下的待办」「发现的问题」「这儿有个 bug」，"
        "别端着写成「遗留缺口」「结构性缺陷」这类从英文句型硬搬过来的词。"
        "汇报进展说「大致了解了」，别写「已初步清楚」。"
        "\n6. 英文名词短语别硬拼成中文合成词：slot key 说「slot 的 key」，"
        "key-value 就写 key-value，不写「槽键」「键-值关系」。"
        "名词叠着名词时，拆成短句直说。"
        "\n7. 以下仅供用户明确要求的手动词典实验，不是默认回答前置步骤。"
        "需要检查草稿时，可调用 term-dict MCP 的 mindforge_check_text；"
        "有项目目录时传入绝对路径 cwd。工具不会修改原稿；按 annotations 中的句子、"
        "段落、建议和含义局部润色，或判断无需修改并保留原文。"
        "其他句子、数字、代码和结论不变。需要进一步复核时才再次调用复查，"
        "不要把候选列表、占位符或「直接给结论」之类指令照抄到回答里。"
        "工具不可用时自行检查，不要声称已经调用。默认方案不启用 Stop 复核。"
        "\n8. 补充词典时，mindforge_add_term 默认写当前 workspace，必须传绝对路径 cwd；"
        "需要单独初始化可调用 mindforge_init_dict，已有词典不会覆盖。"
        "不要把 MCP 服务或插件目录当作 workspace；不知道当前路径时先确认。"
        "只有用户明确要求跨项目共享时才传 scope=user。"
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
    ctx = build_context(load_display_rules(cwd))
    print(json.dumps({
        "continue": True,
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": ctx,
        },
    }, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception as exc:
        print("zh-guard terminology injection failed: %s" % exc, file=sys.stderr)
        sys.exit(0)
