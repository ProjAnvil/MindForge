#!/usr/bin/env python3
"""zh-guard 公共库：三级词典加载与共享工具（MindForge style-rules-zh-cn 插件内）。

被 inject.py / inspect.py / inspect-file.py / term-dict-server.py 引用。
本模块 import 时无任何副作用；各 hook 脚本保持 fail-open 薄壳，
错误处理（SystemExit 之外的异常一律 exit 0）留在各自脚本里。

三级词典（优先级从低到高，后加载覆盖先加载）：
  1. 内置：插件自带 terminology.tsv，随插件分发；
  2. 用户级：~/.claude/MindForge/terminology.tsv（ZH_GUARD_HOME 可改），
     用户自加词条、字典升级时保留；
  3. 项目级：从 hook stdin 的 cwd 向上发现的 mindforge.zh-dict.tsv，
     放项目根，随仓库提交，团队共享（cspell 项目词典同款机制）。

项目级发现规则：从 cwd 逐级向上，每层先查词典文件、再查 .git；
遇到含 .git 的目录而该层没有词典即停——项目根之外不查，
避免把 $HOME 里的同名文件误当项目词典。

展示顺序（L1 注入用）：项目级 → 用户级 → 内置，越具体越靠前；
超出注入上限时先牺牲宽泛层。

调试：ZH_GUARD_DICT 指定单一字典文件时，跳过三级合并。
"""
import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.environ.get(
    "ZH_GUARD_STATE_DIR",
    os.path.join(os.environ.get("TMPDIR", "/tmp"), "zh-guard"),
)
MAX_BLOCKS_PER_WINDOW = 3
WINDOW_SECONDS = 600
PROJECT_DICT_NAME = "mindforge.zh-dict.tsv"


def guard_home():
    return os.environ.get(
        "ZH_GUARD_HOME",
        os.path.join(os.path.expanduser("~"), ".claude", "MindForge"),
    )


def legacy_home():
    """产品目录改名前的旧位置（~/.claude/zh-guard）。

    仅用于一次性迁移：发现旧字典/旧 OFF 时搬到 guard_home()。
    ZH_GUARD_LEGACY_HOME 供测试隔离。
    """
    return os.environ.get(
        "ZH_GUARD_LEGACY_HOME",
        os.path.join(os.path.expanduser("~"), ".claude", "zh-guard"),
    )


def is_off():
    if os.environ.get("ZH_GUARD_OFF"):
        return True
    if os.path.exists(os.path.join(HERE, "OFF")):
        return True
    if os.path.exists(os.path.join(guard_home(), "OFF")):
        return True
    # 旧目录的 OFF 在迁移完成前也要认，避免停用状态因目录改名失效。
    return os.path.exists(os.path.join(legacy_home(), "OFF"))


def migrate_legacy_home():
    """一次性迁移：~/.claude/zh-guard → ~/.claude/MindForge。

    字典与 OFF 各自独立搬迁（新位置已有就不动）；旧目录不删除，
    迁移完成后可手动清理。搬过来的旧字典随后照常走 @sync 版本同步：
    自带词条刷新、用户自加词条保留。幂等，可反复调用。
    在 hook 的停用检查之前执行，保证改名后停用状态也无缝。
    """
    try:
        home = guard_home()
        legacy = legacy_home()
        if not os.path.isdir(legacy):
            return
        old_off = os.path.join(legacy, "OFF")
        if os.path.exists(old_off) and not os.path.exists(os.path.join(home, "OFF")):
            os.makedirs(home, exist_ok=True)
            # OFF 是状态标记：移动而非复制。留在旧位置会让
            # 「删新 OFF 恢复」失效（旧副本还压着停用状态）。
            shutil.move(old_off, os.path.join(home, "OFF"))
        old_dict = os.path.join(legacy, "terminology.tsv")
        new_dict = os.path.join(home, "terminology.tsv")
        if os.path.exists(old_dict) and not os.path.exists(new_dict):
            os.makedirs(home, exist_ok=True)
            shutil.copyfile(old_dict, new_dict)
    except Exception:
        pass


def ensure_user_dict():
    """安装迁移 + 版本同步。

    0. 产品目录改名迁移：~/.claude/zh-guard → ~/.claude/MindForge，
       旧字典与 OFF 存在则搬过来（见 migrate_legacy_home）；
    1. 用户字典不存在：复制插件自带字典过去；
    2. 已存在且 @sync 版本与自带字典一致：不动；
    3. 版本不一致：以新版自带字典为底，
       把用户自加词条（第一列不在自带字典里的行）追加回去。

    用户对自带词条本身的本地改写会被新版覆盖——这是刻意的：
    字典要能迭代，想完全自控请用 ZH_GUARD_DICT 指向自己的文件。
    """
    try:
        migrate_legacy_home()
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


def find_project_dict(cwd):
    """从 cwd 向上找项目级词典 mindforge.zh-dict.tsv。

    每层先查词典、再查 .git：含 .git 且无词典即停（项目根边界）。
    """
    try:
        d = os.path.abspath(cwd or ".")
        while True:
            candidate = os.path.join(d, PROJECT_DICT_NAME)
            if os.path.isfile(candidate):
                return candidate
            if os.path.isdir(os.path.join(d, ".git")):
                return None
            parent = os.path.dirname(d)
            if parent == d:
                return None
            d = parent
    except Exception:
        return None


def dict_paths(cwd=None):
    """返回三级字典路径列表（加载序：内置 → 用户 → 项目）。

    ZH_GUARD_DICT 指定单一文件时只返回它（调试模式）。
    """
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
    if cwd:
        project = find_project_dict(cwd)
        if project:
            paths.append(project)
    return paths


def _iter_raw_entries(path):
    """逐行产出 (term, expected, note)；跳过注释与缺列行。"""
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.rstrip("\n").lstrip("\ufeff")
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("\t")]
            if not parts or not parts[0]:
                continue
            good = parts[1] if len(parts) >= 2 else ""
            note = parts[2] if len(parts) >= 3 else ""
            yield parts[0], good, note


def load_pairs(cwd=None):
    """合并三级词典，返回 [(bad, good, is_regex), ...]。

    后加载（更具体层）覆盖先加载；re: 前缀按正则词条处理。
    供 L2 出口检测与文件写检测使用。
    """
    merged = {}
    for path in dict_paths(cwd):
        for term, good, _ in _iter_raw_entries(path):
            merged[term] = good
    out = []
    for bad, good in merged.items():
        if bad.startswith("re:"):
            out.append((bad[3:], good, True))
        else:
            out.append((bad, good, False))
    return out


def load_display_entries(cwd=None):
    """三级合并 + 展示排序，返回 [(term, target), ...]。

    展示序：项目级 → 用户级 → 内置（越具体越靠前）；
    同层保持文件内顺序。正则词条以 humanize 后的模式串展示。
    供 L1 注入使用。
    """
    merged = {}
    origin = {}
    for idx, path in enumerate(dict_paths(cwd)):
        for term, good, _ in _iter_raw_entries(path):
            merged[term] = good
            origin[term] = idx
    by_level = {}
    for term, target in merged.items():
        by_level.setdefault(origin.get(term, 0), []).append((term, target))
    out = []
    for idx in sorted(by_level, reverse=True):  # 层级深的在前
        for term, target in by_level[idx]:
            shown = humanize_regex(term[3:]) if term.startswith("re:") else term
            out.append((shown, target))
    return out


def load_note_entries(cwd=None):
    """合并三级词典，返回 [(term, expected, note), ...]。

    保留原始 term（含 re: 前缀）与说明列，供 term-dict MCP 查询使用；
    后加载（更具体层）覆盖先加载。
    """
    merged = {}
    for path in dict_paths(cwd):
        for term, good, note in _iter_raw_entries(path):
            merged[term] = (good, note)
    return [(term, good, note) for term, (good, note) in merged.items()]


def humanize_regex(pattern):
    """把正则渲染成人能读的形式：第\\s*\\d+\\s*刀 → 第N刀。"""
    try:
        p = pattern.replace("\\s*", "").replace("\\s+", " ")
        p = re.sub(r"\\d\+?", "N", p)
        return p.lstrip("^").rstrip("$") or pattern
    except Exception:
        return pattern


def strip_code(text):
    """豁免围栏代码块、行内代码与引号内提及，只检查自然语言部分。"""
    text = re.sub(r"```.*?```", "", text, flags=re.S)
    text = re.sub(r"`[^`\n]*`", "", text)
    text = re.sub(r"「[^」\n]*」", "", text)
    text = re.sub(r"\u201c[^\u201d\n]*\u201d", "", text)
    return text


def state_path(prefix, session_id):
    safe = re.sub(r"[^A-Za-z0-9_-]", "_", session_id or "default")
    return os.path.join(STATE_DIR, prefix + safe + ".json")


def load_state(path):
    import json
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"blocked_hashes": [], "block_times": []}


def save_state(path, state):
    import json
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(state, f)
    except Exception:
        pass


def allow_block(state, content_hash):
    """防循环判定：同 hash 只断一次；窗口内限次。"""
    import time
    now = time.time()
    if content_hash in state.get("blocked_hashes", []):
        return False
    recent = [t for t in state.get("block_times", []) if now - t < WINDOW_SECONDS]
    if len(recent) >= MAX_BLOCKS_PER_WINDOW:
        return False
    return True


def record_block(state, content_hash):
    import time
    now = time.time()
    hashes = state.get("blocked_hashes", [])
    hashes.append(content_hash)
    state["blocked_hashes"] = hashes[-20:]
    times = [t for t in state.get("block_times", []) if now - t < WINDOW_SECONDS]
    times.append(now)
    state["block_times"] = times
