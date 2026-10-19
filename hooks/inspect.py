#!/usr/bin/env python3
"""zh-guard L2 出口层：Stop / SubagentStop hook（MindForge style-rules-zh-cn 插件内）。

职责：agent 回答结束时触发，检查 last_assistant_message。
命中术语字典中的直译词时，返回 continue:false + 重写指引（exit 2），
迫使 agent 修正后重新输出。未命中或任何异常时放行。

字典（install 时迁移模型，与 inject.py 相同）：
  1. 插件自带 terminology.tsv 是发布源；
  2. 首次运行时若 ~/.claude/zh-guard/terminology.tsv 不存在，自动复制过去；
  3. 运行时合并读取插件自带 + 用户目录（用户条目优先）；
  4. ZH_GUARD_DICT 环境变量可指定单一字典文件（调试用）。

防循环：
  1. 同一内容（hash 相同）只阻断一次；
  2. 每会话 10 分钟窗口内最多阻断 3 次，超出直接放行。
停用方式：export ZH_GUARD_OFF=1，或创建 OFF 文件（ZH_GUARD_HOME/ 或插件目录）。

设计原则（fail-open）：脚本错误、超时、字典缺失，一律放行，
绝不卡死会话。
"""
import hashlib
import json
import os
import re
import shutil
import sys
import time

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
        """安装迁移：用户字典不存在时，从插件自带字典复制过去。绝不覆盖。"""
        try:
            home = guard_home()
            user = os.path.join(home, "terminology.tsv")
            bundled = os.path.join(HERE, "terminology.tsv")
            if not os.path.exists(user) and os.path.exists(bundled):
                os.makedirs(home, exist_ok=True)
                shutil.copyfile(bundled, user)
        except Exception:
            pass

    def dict_paths():
        """返回字典文件路径列表：插件自带在前，用户覆盖在后。"""
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
        """合并读取 [(词, 期望写法, 是否正则), ...]。用户条目覆盖插件默认。

        第一列以 re: 开头表示正则词条（匹配可变模式，如 第N刀），
        其余按字面子串匹配。无效正则在使用处跳过（fail-open）。
        """
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
        """去掉围栏代码块、行内代码与引号内提及，只检查自然语言部分。

        引号豁免：「」与“”内的术语属于提及（讨论这个词），
        不是使用（拿这个词表达意思），不拦截。
        """
        text = re.sub(r"```.*?```", "", text, flags=re.S)
        text = re.sub(r"`[^`\n]*`", "", text)
        text = re.sub(r"「[^」\n]*」", "", text)
        text = re.sub(r"\u201c[^\u201d\n]*\u201d", "", text)
        return text

    def state_path(session_id):
        safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id or "default")
        return os.path.join(STATE_DIR, "state-" + safe + ".json")

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
        """防循环判定：同 hash 只断一次；窗口内限次。"""
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
        msg = payload.get("last_assistant_message") or ""
        if not msg.strip():
            sys.exit(0)
        session_id = payload.get("session_id") or "default"

        pairs = load_dict()
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
        spath = state_path(session_id)
        state = load_state(spath)
        if not allow_block(state, content_hash):
            sys.exit(0)

        record_block(state, content_hash)
        save_state(spath, state)

        fixes = "；".join("%s→%s" % (bad, good) for bad, good in hits[:10])
        reason = (
            "你的上一条回复包含字面直译的术语，不是地道中文，需要重写。"
            "修正以下术语：" + fixes + "。"
            "其余内容、结论和代码保持不变，"
            "输出修正后的完整回复。"
            "再次提醒：有中文社区定译用定译，无定译保留英文原词，"
            "禁止字面直译英文黑话。"
        )
        body = json.dumps({
            "continue": False,
            "reason": reason,
            "stopReason": reason,
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
