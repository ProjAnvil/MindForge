#!/usr/bin/env python3
"""Optional Claude MessageDisplay hook: replace explicit safe rules only."""
import hashlib
import json
import os
import sys
import tempfile

from zh_guard_common import (
    apply_replacements,
    ensure_user_dict,
    is_off,
    lint_text,
    mask_protected,
    state_path,
)


def save_display_state(path, state):
    directory = os.path.dirname(path)
    os.makedirs(directory, mode=0o700, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=directory, prefix="display-", delete=False,
        ) as stream:
            temporary = stream.name
            json.dump(state, stream)
        os.replace(temporary, path)
    finally:
        if temporary is not None and os.path.exists(temporary):
            os.unlink(temporary)


def main():
    if is_off():
        return
    payload = json.load(sys.stdin)
    if not isinstance(payload, dict):
        raise ValueError("MessageDisplay 输入必须是 JSON 对象")
    session, message = payload.get("session_id"), payload.get("message_id")
    delta, index, final = payload.get("delta"), payload.get("index"), payload.get("final")
    if not all(isinstance(value, str) and value for value in (session, message)):
        raise ValueError("MessageDisplay 缺少 session_id 或 message_id")
    if (not isinstance(delta, str) or type(index) is not int or index < 0
            or not isinstance(final, bool)):
        raise ValueError("MessageDisplay 需要 delta、非负 index 和布尔 final")
    cwd = payload.get("cwd") or ""
    if not isinstance(cwd, str):
        raise ValueError("MessageDisplay cwd 必须是目录路径")

    key = hashlib.sha256((session + "\0" + message).encode("utf-8")).hexdigest()
    path = state_path("display-", key)
    digest = hashlib.sha256(
        json.dumps([delta, final], ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    try:
        with open(path, encoding="utf-8") as stream:
            state = json.load(stream)
    except FileNotFoundError:
        state = None

    replay = False
    if state is None:
        if index != 0:
            raise ValueError("缺少此前显示批次的围栏状态，保留原文")
        before = ""
    elif index == state["index"] and digest == state["digest"]:
        before = state["before"]
        replay = True
    elif index == state["index"] + 1 and not state["final"]:
        before = state["after"]
    else:
        raise ValueError("显示批次重复内容不一致或顺序错误，保留原文")

    ensure_user_dict()
    masked, after = mask_protected(delta, before)
    findings = lint_text(delta, cwd=cwd, masked_text=masked)
    displayed = apply_replacements(delta, findings)
    if not replay:
        # Only hashes, sequence numbers and fence markers are persisted, never draft text.
        save_display_state(path, {
            "index": index, "digest": digest, "before": before,
            "after": after, "final": final,
        })
    print(json.dumps({"displayContent": displayed}, ensure_ascii=False))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print("zh-guard MessageDisplay 失败，保留原文：%s" % exc, file=sys.stderr)
