#!/usr/bin/env python3
"""zh-guard 文件写入口：PreToolUse hook（MindForge style-rules-zh-cn 插件内）。

职责：模型往文件里写内容前触发，检查 tool_input.content / new_string。
文档类文件命中术语字典或句式套话时，deny 并给出重写指引，
迫使模型改写后再写。未命中或任何异常时放行。

背景：Stop 出口检测只看助手消息正文，模型把直译词写进 README、
文档、注释时，正文往往只说「文件已写好」——文件内容是出口层的盲区。
这一层在写入前拦住它。

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
import os
import re
import sys
import time

TEXT_SUFFIXES = (".md", ".markdown", ".txt", ".rst")

try:
    HERE = os.path.dirname(os.path.abspath(__file__))
    STATE_DIR = os.environ.get(
        "ZH_GUARD_STATE_DIR",
        os.path.join(os.environ.get("TMPDIR", "/tmp"), "zh-guard"),
    )
    MAX_BLOCKS_PER_WINDOW = 3
    WINDOW_SECONDS = 600

    def guard_home():
        return os.environ.get(
            "ZH_GUARD_HOME",
            os.path.join(os.path.expanduser("~"), ".claude", "zh-guard"),
        )

    def is_off():
        if os.environ.get("ZH_GUARD_OFF"):
            return True
        if os.path.exists(os.path.join(HERE, "OFF")):
            return True
        return os.path.exists(os.path.join(guard_home(), "OFF"))

    def ensure_user_dict():
        """安装迁移 + 版本同步（与 inject.py / inspect.py 相同的机制）。"""
        try:
            home = guard_home()
            user = os.path.join(home, "terminology.tsv")
            bundled = os.path.join(HERE, "terminology.tsv")
            if not os.path.exists(bundled):
                return
            with open(bundled, encoding="utf-8") as f:
                bundled_text = f.read()
            if not os.path.exists(user):
                os.makedirs(home, exist_ok=True)
                with open(user, "w", encoding="utf-8") as f:
                    f.write(bundled_text)
                return
            marker = ""
            for line in bundled_text.splitlines():
                if line.startswith("@sync") or line.startswith("# @sync"):
                    marker = line.strip()
                    break
            with open(user, encoding="utf-8") as f:
                user_text = f.read()
            if marker and marker in user_text:
                return
            bundled_keys = set()
            for line in bundled_text.splitlines():
                line = line.lstrip("\ufeff")
                if not line or line.startswith("#"):
                    continue
                key = line.split("\t")[0].strip()
                if key:
                    bundled_keys.add(key)
            kept = []
            for line in user_text.splitlines():
                line = line.lstrip("\ufeff")
                if not line or line.startswith("#"):
                    continue
                key = line.split("\t")[0].strip()
                if key and key not in bundled_keys:
                    kept.append(line)
            text = bundled_text if bundled_text.endswith("\n") else bundled_text + "\n"
            if kept:
                text += "\n# 以下为用户自加词条（字典升级时自动保留）\n" + "\n".join(kept) + "\n"
            with open(user, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception:
            pass

    def dict_paths():
        override = os.environ.get("ZH_GUARD_DICT")
        if override:
            return [override] if os.path.exists(override) else []
        paths = []
        default = os.path.join(HERE, "terminology.tsv")
        if os.path.exists(default):
            paths.append(default)
        user = os.path.join(guard_home(), "terminology.tsv")
        if os.path.exists(user):
            paths.append(user)
        return paths

    def load_dict():
        """合并读取 [(词, 期望写法, 是否正则), ...]。用户条目覆盖插件默认。"""
        merged = {}
        for path in dict_paths():
            with open(path, encoding="utf-8-sig") as f:
                for line in f:
                    line = line.rstrip("\n").lstrip("\ufeff")
                    if not line or line.startswith("#"):
                        continue
                    parts = [p.strip() for p in line.split("\t")]
                    if len(parts) >= 2 and parts[0]:
                        merged[parts[0]] = parts[1]
        out = []
        for bad, good in merged.items():
            if bad.startswith("re:"):
                out.append((bad[3:], good, True))
            else:
                out.append((bad, good, False))
        return out

    def strip_code(text):
        """豁免围栏代码块、行内代码与引号内提及，只检查自然语言部分。"""
        text = re.sub(r"```.*?```", "", text, flags=re.S)
        text = re.sub(r"`[^`\n]*`", "", text)
        text = re.sub(r"「[^」\n]*」", "", text)
        text = re.sub(r"\u201c[^\u201d\n]*\u201d", "", text)
        return text

    def state_path(session_id):
        safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id or "default")
        return os.path.join(STATE_DIR, "file-state-" + safe + ".json")

    def load_state(path):
        try:
            with open(path, encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"blocked_hashes": [], "block_times": []}

    def save_state(path, state):
        try:
            os.makedirs(STATE_DIR, exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                json.dump(state, f)
        except Exception:
            pass

    def allow_block(state, content_hash):
        now = time.time()
        if content_hash in state.get("blocked_hashes", []):
            return False
        recent = [t for t in state.get("block_times", []) if now - t < WINDOW_SECONDS]
        if len(recent) >= MAX_BLOCKS_PER_WINDOW:
            return False
        return True

    def record_block(state, content_hash):
        now = time.time()
        hashes = state.get("blocked_hashes", [])
        hashes.append(content_hash)
        state["blocked_hashes"] = hashes[-20:]
        times = [t for t in state.get("block_times", []) if now - t < WINDOW_SECONDS]
        times.append(now)
        state["block_times"] = times

    def main():
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

        pairs = load_dict()
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
        spath = state_path(session_id)
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

    main()
except SystemExit:
    raise
except Exception:
    # fail-open：任何未预期错误都放行。
    sys.exit(0)
