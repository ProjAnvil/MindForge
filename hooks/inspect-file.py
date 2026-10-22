#!/usr/bin/env python3
"""zh-guard 文件写入口：PreToolUse hook（MindForge style-rules-zh-cn 插件内）。

职责：模型往文件里写内容前触发，检查 tool_input.content / new_string。
文档类文件命中术语字典或句式套话时，deny 并给出重写指引，
迫使模型改写后再写。未命中或任何异常时放行。

背景：Stop 出口检测只看助手消息正文，模型把直译词写进 README、
文档、注释时，正文往往只说「文件已写好」——文件内容是出口层的盲区。
这一层在写入前拦住它。

字典三级（项目级 > 用户级 > 内置），公共逻辑见 zh_guard_common.py；
项目级词典从 stdin 的 cwd 向上发现（mindforge.zh-dict.tsv）。

范围（刻意收窄，避免误伤）：
  1. 只查文档类文件：.md / .markdown / .txt / .rst。代码文件里的中文
     注释要隔离出字符串与 docstring 才可靠，留给后续版本。
  2. 豁免区与消息层一致：围栏代码块、行内代码、「」与“”引号内提及。
  3. 防循环：同一文件同一内容每会话只拦一次；10 分钟窗口内最多 3 次
     （与 inspect.py 相互独立的状态文件，互不挤占额度）。
  4. 编辑本插件自己的文档（README 里本来就有直译词示例）会被拦一次，
     重试同内容即放行；想一次写对，给示例词加「」引号。

阻断契约（三平台同形）：
  - stdout：hookSpecificOutput.permissionDecision = deny
    （Claude Code / zcode / Kimi 的 PreToolUse 都认这个形状）
  - stderr：阻断理由（Kimi 以 stderr 为 reason）
  - exit 2：阻断快捷方式

停用方式与 inspect.py 一致：export ZH_GUARD_OFF=1，或创建 OFF 文件。
设计原则（fail-open）：任何未预期错误都放行，绝不卡死写入。
"""
import hashlib
import json
import re
import sys

from zh_guard_common import (
    allow_block,
    ensure_user_dict,
    is_off,
    load_pairs,
    load_state,
    migrate_legacy_home,
    record_block,
    save_state,
    state_path,
    strip_code,
)

TEXT_SUFFIXES = (".md", ".markdown", ".txt", ".rst")


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
    tool_input = payload.get("tool_input") or {}
    path = tool_input.get("file_path") or tool_input.get("path") or ""
    if not path.lower().endswith(TEXT_SUFFIXES):
        sys.exit(0)
    content = tool_input.get("content") or tool_input.get("new_string") or ""
    if not content.strip():
        sys.exit(0)
    session_id = payload.get("session_id") or "default"
    cwd = payload.get("cwd") or ""

    pairs = load_pairs(cwd)
    if not pairs:
        sys.exit(0)

    text = strip_code(content)
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

    content_hash = hashlib.sha1(
        (path + "\n" + content).encode("utf-8")
    ).hexdigest()
    spath = state_path("file-state-", session_id)
    state = load_state(spath)
    if not allow_block(state, content_hash):
        sys.exit(0)

    record_block(state, content_hash)
    save_state(spath, state)

    fixes = "；".join("%s→%s" % (bad, good) for bad, good in hits[:10])
    reason = (
        "你即将写入 %s 的内容包含字面直译的术语或套话，不是地道中文，"
        "先改写再写入。按箭头右侧的写法重写整句（不要机械替换）：%s。"
        "其余内容与结构保持不变。"
        "再次提醒：有中文社区定译用定译，无定译保留英文原词，"
        "禁止字面直译英文黑话。" % (path, fixes)
    )
    body = json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        },
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
