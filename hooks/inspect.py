#!/usr/bin/env python3
"""zh-guard L2 出口层：Stop / SubagentStop hook（MindForge style-rules-zh-cn 插件内）。

职责：agent 回答结束时触发，检查 last_assistant_message。
命中术语字典中的直译词时，迫使 agent 修正后重新输出：

  - 返回 decision:"block" + reason（exit 2），让助手检查并修正。
    未命中或任何异常时放行。

字典三级（项目级 > 用户级 > 内置），公共逻辑见 zh_guard_common.py；
项目级词典从 stdin 的 cwd 向上发现（mindforge.zh-dict.tsv）。

防循环：同一内容只阻断一次；10 分钟窗口内最多 3 次。
停用方式：export ZH_GUARD_OFF=1，或创建 OFF 文件。

设计原则（fail-open）：脚本错误、超时、字典缺失，一律放行，
绝不卡死会话。
"""
import hashlib
import json
import sys

from zh_guard_common import (
    allow_block,
    ensure_user_dict,
    format_findings,
    is_off,
    lint_text,
    load_state,
    migrate_legacy_home,
    record_block,
    save_state,
    state_path,
)


def main():
    migrate_legacy_home()
    if is_off():
        sys.exit(0)
    ensure_user_dict()
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
    except Exception:
        sys.exit(0)
    msg = payload.get("last_assistant_message") or ""
    if not msg.strip():
        sys.exit(0)
    session_id = payload.get("session_id") or "default"

    cwd = payload.get("cwd") or ""
    hits = lint_text(msg, cwd=cwd)
    if not hits:
        sys.exit(0)

    content_hash = hashlib.sha1(msg.encode("utf-8")).hexdigest()
    spath = state_path("state-", session_id)
    state = load_state(spath)
    if not allow_block(state, content_hash):
        sys.exit(0)

    record_block(state, content_hash)
    save_state(spath, state)

    fixes = format_findings(hits)
    reason = (
        "你的上一条回复命中措辞检查规则，请结合原句确认是否需要改写。"
        "以下是检测结果：" + fixes + "。"
        "标为可直接替换的按建议修正；标为按语境改写的先判断原句意思，"
        "合法的中文用法保留，不要机械替换候选写法或改写指令。"
        "不要把排查问题原因硬套成其他专业概念。"
        "其余内容、结论和代码保持不变，"
        "用 term-dict MCP 的 check_text 复查草稿（工具可用时），再输出完整回复。"
        "再次提醒：有中文社区定译用定译，无定译保留英文原词，"
        "禁止字面直译英文黑话。"
    )
    body = json.dumps({
        "decision": "block",
        "reason": reason,
    }, ensure_ascii=False)
    sys.stdout.write(body + "\n")
    sys.stderr.write(reason + "\n")
    sys.exit(2)


try:
    main()
except SystemExit:
    raise
except Exception as exc:
    print("zh-guard Stop 检测失败：%s" % exc, file=sys.stderr)
    sys.exit(0)
