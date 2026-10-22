#!/usr/bin/env python3
"""zh-guard L2 出口层：Stop / SubagentStop hook（MindForge style-rules-zh-cn 插件内）。

职责：agent 回答结束时触发，检查 last_assistant_message。
命中术语字典中的直译词时，迫使 agent 修正后重新输出：

  - Claude Code：返回 continue:false + 重写指引（exit 2）；
  - zcode（检测 ZCODE_PLUGIN_ROOT）：返回 decision:"block" + reason，
    zcode 的 Stop 契约里 continue:false 语义是「允许结束」，不能输出。
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
import os
import re
import sys

from zh_guard_common import (
    allow_block,
    ensure_user_dict,
    is_off,
    load_pairs,
    load_state,
    record_block,
    save_state,
    state_path,
    strip_code,
)


def main():
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

    # 平台检测：zcode 只向插件进程注入 ZCODE_PLUGIN_ROOT。
    # zcode 的 Stop 契约是 decision:block（continue:false 在那里
    # 语义相反，会把拦截整个废掉），必须分开输出。
    is_zcode = bool(os.environ.get("ZCODE_PLUGIN_ROOT"))

    cwd = payload.get("cwd") or ""
    pairs = load_pairs(cwd)
    if not pairs:
        sys.exit(0)

    text = strip_code(msg)
    hits = []
    for bad, good, is_regex in pairs:
        if is_regex:
            try:
                m = re.search(bad, text)
            except re.error:
                continue  # 无效正则：跳过该词条（fail-open）
            if m:
                hits.append((m.group(0), good))
        elif bad in text:
            hits.append((bad, good))
    if not hits:
        sys.exit(0)

    content_hash = hashlib.sha1(msg.encode("utf-8")).hexdigest()
    spath = state_path("state-", session_id)
    state = load_state(spath)
    if not allow_block(state, content_hash):
        sys.exit(0)

    record_block(state, content_hash)
    save_state(spath, state)

    fixes = "；".join("%s→%s" % (bad, good) for bad, good in hits[:10])
    reason = (
        "你的上一条回复包含字面直译的术语，不是地道中文，需要重写。"
        "按箭头右侧的写法表达（右侧是自然的中文措辞，要据此重写整句，"
        "不要做机械的词到词替换）：" + fixes + "。"
        "其余内容、结论和代码保持不变，"
        "输出修正后的完整回复。"
        "再次提醒：有中文社区定译用定译，无定译保留英文原词，"
        "禁止字面直译英文黑话。"
    )
    if is_zcode:
        body = json.dumps({
            "decision": "block",
            "reason": reason,
        }, ensure_ascii=False)
    else:
        body = json.dumps({
            "continue": False,
            "reason": reason,
            "stopReason": reason,
        }, ensure_ascii=False)
    sys.stdout.write(body + "\n")
    sys.stderr.write(reason + "\n")
    sys.exit(2)


try:
    main()
except SystemExit:
    raise
except Exception:
    # fail-open：任何未预期错误都放行。
    sys.exit(0)
