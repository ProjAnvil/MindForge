#!/usr/bin/env python3
"""zh-guard 公共库：三级词典加载与共享工具（MindForge style-rules-zh-cn 插件内）。

被注入、MCP、出口检测与文件检测入口共同引用。
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
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sys
from typing import Iterable, NamedTuple

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_DIR = os.environ.get(
    "ZH_GUARD_STATE_DIR",
    os.path.join(os.environ.get("TMPDIR", "/tmp"), "zh-guard"),
)
MAX_BLOCKS_PER_WINDOW = 3
WINDOW_SECONDS = 600
PROJECT_DICT_NAME = "mindforge.zh-dict.tsv"


# dataclasses imports inspect, which would load the sibling hook script.
class Rule:
    def __init__(self, term: str, suggestion: str = "", meaning: str = ""):
        if not term.strip() or term.lstrip().startswith(("#", "@sync")):
            raise ValueError("term must be nonempty and must not be a comment or sync marker")
        self.term = term
        self.suggestion = suggestion
        self.meaning = meaning


class Finding(NamedTuple):
    term: str
    text: str
    suggestion: str
    meaning: str
    start: int
    end: int
    line: int
    column: int
    context: str
    sentence: str
    sentence_start: int
    sentence_end: int
    rule_id: str
    annotation_id: str
    draft_id: str


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


def _drop_legacy_action_column(line):
    """旧格式的第 4 列是动作（replace/rewrite），新格式没有这一列。

    升级刷新时保留用户自加词条，若原样保留旧 4 列行，
    整本词典会因列数超限而加载失败。动作列在方案 A 下已无含义，
    因此直接裁掉，词条和建议写法保持不变。
    """
    parts = [p.strip() for p in line.split("\t")]
    if len(parts) <= 3:
        return line
    return "\t".join(parts[:3])


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
                kept.append(_drop_legacy_action_column(line))
        text = bundled_text if bundled_text.endswith("\n") else bundled_text + "\n"
        if kept:
            text += "\n# 以下为用户自加词条（字典升级时自动保留）\n" + "\n".join(kept) + "\n"
        with open(user, "w", encoding="utf-8") as f:
            f.write(text)
    except Exception:
        pass


def _project_directories(cwd):
    directory = os.path.abspath(cwd or ".")
    while True:
        yield directory
        parent = os.path.dirname(directory)
        if os.path.exists(os.path.join(directory, ".git")) or parent == directory:
            return
        directory = parent


def find_project_dict(cwd):
    """从 cwd 向上找项目级词典 mindforge.zh-dict.tsv。

    每层先查词典、再查 .git：含 .git 且无词典即停（项目根边界）。
    """
    try:
        for directory in _project_directories(cwd):
            candidate = os.path.join(directory, PROJECT_DICT_NAME)
            if os.path.isfile(candidate):
                return candidate
        return None
    except Exception:
        return None


def init_workspace_dict(cwd: str) -> tuple[str, bool]:
    """复用就近词典；不存在时在 Git 根或显式 workspace 目录创建，不覆盖。"""
    if not isinstance(cwd, str) or not os.path.isabs(cwd) or not os.path.isdir(cwd):
        raise ValueError("cwd must be the absolute path of an existing workspace directory")
    target = os.path.join(os.path.abspath(cwd), PROJECT_DICT_NAME)
    for directory in _project_directories(cwd):
        candidate = os.path.join(directory, PROJECT_DICT_NAME)
        if os.path.lexists(candidate):
            if not os.path.isfile(candidate):
                raise ValueError("workspace dictionary path is not a regular file: %s" % candidate)
            return candidate, False
        if os.path.exists(os.path.join(directory, ".git")):
            target = candidate
    with open(os.path.join(HERE, "project-dict-template.tsv"), encoding="utf-8") as stream:
        template = stream.read()
    try:
        with open(target, "x", encoding="utf-8") as stream:
            stream.write(template)
    except FileExistsError:
        if not os.path.isfile(target):
            raise
        return target, False
    return target, True


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
    """词语、可空的建议写法、可空的含义；只填词语是登记而非纠错规则。"""
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.rstrip("\n").lstrip("\ufeff")
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split("\t")]
            if not parts or not parts[0]:
                continue
            suggestion = parts[1] if len(parts) >= 2 else ""
            meaning = parts[2] if len(parts) >= 3 else ""
            if len(parts) > 3:
                raise ValueError("%s: entries have at most three columns: %s" % (path, parts[0]))
            yield parts[0], suggestion, meaning


def _merged_rules(cwd=None):
    merged, origin = {}, {}
    for level, path in enumerate(dict_paths(cwd)):
        for term, suggestion, meaning in _iter_raw_entries(path):
            merged[term] = Rule(term, suggestion, meaning)
            origin[term] = level
    return merged, origin


def load_rules(cwd: str | None = None) -> list[Rule]:
    merged, _origin = _merged_rules(cwd)
    return list(merged.values())


def load_display_rules(cwd=None):
    """注入时优先展示项目资料，保留建议与含义；同层维持文件内顺序。"""
    merged, origin = _merged_rules(cwd)
    return sorted(merged.values(), key=lambda rule: -origin[rule.term])


def humanize_regex(pattern):
    """把正则渲染成人能读的形式：第\\s*\\d+\\s*刀 → 第N刀。"""
    try:
        p = pattern.replace("\\s*", "").replace("\\s+", " ")
        p = re.sub(r"\\d\+?", "N", p)
        return p.lstrip("^").rstrip("$") or pattern
    except Exception:
        return pattern


def mask_protected(text: str, fence: str = "") -> tuple[str, str]:
    """屏蔽代码与引号提及，保留原文位置。"""
    def mask(value):
        return "".join(char if char in "\r\n" else "\0" for char in value)

    lines = []
    inline = re.compile(
        r"(?<!`)(`+)(?!`)[^\n]*?(?<!`)\1(?!`)|「[^」\n]*」|“[^”\n]*”"
    )
    for line in text.splitlines(keepends=True):
        if fence:
            active = re.fullmatch(r"(>*)(`{3,}|~{3,})", fence)
            if active is None:
                raise ValueError("invalid code-fence state")
            marker = active[2]
            closing = (
                r"[ \t]*(?:>[ \t]*){%d}" % len(active[1])
                + re.escape(marker[0])
                + r"{%d,}[ \t]*(?:\r?\n)?" % len(marker)
            )
            if re.fullmatch(closing, line):
                fence = ""
            lines.append(mask(line))
            continue
        opening = re.match(
            r"[ \t]*(?P<quotes>(?:>[ \t]*)*)"
            r"(?:(?:[-+*]|\d+[.)])[ \t]+)?"
            r"(?P<marker>`{3,}|~{3,})(?P<info>[^\r\n]*)", line,
        )
        if opening and not (
            opening["marker"].startswith("`") and "`" in opening["info"]
        ):
            fence = ">" * opening["quotes"].count(">") + opening["marker"]
            lines.append(mask(line))
        else:
            lines.append(inline.sub(lambda match: mask(match[0]), line))
    return "".join(lines), fence


def strip_code(text):
    """屏蔽保护区但不拼接它们两侧的词语。"""
    return mask_protected(text)[0]


def draft_id(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sentence_context(text: str, masked: str, start: int, end: int
                     ) -> tuple[int, int, str]:
    # Newlines bound Markdown items; a period is a boundary only before whitespace/end.
    boundaries = list(re.finditer(r"[。！？!?]+|[.](?=\s|$)|\r?\n", masked))
    left, right = 0, len(text)
    for boundary in boundaries:
        if boundary.end() <= start:
            left = boundary.end()
        elif boundary.start() >= end:
            right = boundary.end()
            break
    while left < start and text[left].isspace():
        left += 1
    while right > end and text[right - 1].isspace():
        right -= 1
    paragraph_left, paragraph_right = 0, len(text)
    for boundary in re.finditer(r"\r?\n[ \t]*\r?\n", masked):
        if boundary.end() <= start:
            paragraph_left = boundary.end()
        elif boundary.start() >= end:
            paragraph_right = boundary.start()
            break
    return left, right, text[paragraph_left:paragraph_right].strip()


def lint_text(text: str, rules: Iterable[Rule] | None = None,
              cwd: str | None = None, *, masked_text: str | None = None
              ) -> list[Finding]:
    masked = mask_protected(text)[0] if masked_text is None else masked_text
    if len(masked) != len(text):
        raise ValueError("protected-region masking must preserve the original text length")
    version = draft_id(text)
    candidates = []
    for rule in load_rules(cwd) if rules is None else rules:
        if not rule.suggestion and not rule.meaning:
            continue
        pattern = rule.term[3:] if rule.term.startswith("re:") else re.escape(rule.term)
        try:
            matches = re.finditer(pattern, masked)
        except re.error as exc:
            print("zh-guard: invalid regex %s: %s" % (rule.term, exc), file=sys.stderr)
            continue
        for match in matches:
            start, end = match.span()
            if start == end or "\0" in masked[start:end]:
                continue
            sentence_start, sentence_end, context = sentence_context(text, masked, start, end)
            rule_id = "term-" + draft_id(rule.term)
            annotation_id = draft_id(json.dumps(
                [version, rule_id, rule.suggestion, rule.meaning, start, end],
                ensure_ascii=False,
            ))
            candidates.append(Finding(
                rule.term, text[start:end], rule.suggestion, rule.meaning,
                start, end, text.count("\n", 0, start) + 1,
                start - text.rfind("\n", 0, start),
                context, text[sentence_start:sentence_end], sentence_start, sentence_end,
                rule_id, annotation_id, version,
            ))
    candidates.sort(key=lambda hit: (hit.start, -(hit.end - hit.start)))
    hits, end = [], 0
    for hit in candidates:
        if hit.start >= end:
            hits.append(hit)
            end = hit.end
    return hits


def format_findings(findings: Iterable[Finding], limit: int = 10) -> str:
    parts = []
    for index, hit in enumerate(findings):
        if index >= limit:
            break
        details = {
            "annotation_id": hit.annotation_id,
            "关注表达": hit.text,
            "位置": "第%d行第%d列" % (hit.line, hit.column),
            "原句": hit.sentence, "段落": hit.context,
        }
        if hit.suggestion:
            details["建议写法（仅参考）"] = hit.suggestion
        if hit.meaning:
            details["含义或语境说明"] = hit.meaning
        parts.append(json.dumps(details, ensure_ascii=False))
    return "；".join(parts)


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
