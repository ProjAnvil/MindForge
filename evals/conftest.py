"""Shared fixtures for the MindForge skill evaluation suite.

Layout assumptions:
    evals/           <- this file
    ../skills/en     <- English skills (one directory per skill, each with SKILL.md)
    ../skills/zh-cn  <- Chinese skills
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SKILL_ROOTS = {
    "en": PROJECT_ROOT / "skills" / "en",
    "zh-cn": PROJECT_ROOT / "skills" / "zh-cn",
}


def all_skill_dirs() -> list[tuple[str, Path]]:
    """Every skill as (lang, dir) pairs: 19 en + 19 zh-cn."""
    pairs = []
    for lang, root in SKILL_ROOTS.items():
        pairs += [(lang, d) for d in sorted(root.iterdir()) if (d / "SKILL.md").exists()]
    return pairs


def skill_description(skill_dir: Path) -> str:
    """The single-line `description:` field from a SKILL.md frontmatter."""
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    if not text.startswith("---"):
        return ""
    frontmatter = text.split("---", 2)[1]
    for line in frontmatter.splitlines():
        if line.startswith("description:"):
            return line.removeprefix("description:").strip()
    return ""

# ---------------------------------------------------------------------------
# LLM clients
# ---------------------------------------------------------------------------


def _load_dotenv() -> None:
    """Pick up evals/.env (SMELT_API_KEY etc.); shell env always wins."""
    import smelt

    smelt.load_env(Path(__file__).resolve().parent / ".env")


_load_dotenv()  # must run before reading any SMELT_* variables

# What a real skill runtime makes obvious; our harness must state it.
REFERENCES_HINT = (
    "The skill's files are materialized in the current workspace. When the "
    "skill document points to reference files (e.g. references/xxx.md), read "
    "them with the read_file tool BEFORE answering, and follow them exactly."
)


def ngrams(s: str, n: int = 2) -> set[str]:
    """Character bigrams, case-folded — works for both English and Chinese."""
    s = s.lower()
    return {s[i:i + n] for i in range(len(s) - n + 1)}


def extract_anchor_excerpt(path: Path, trigger: str, limit: int = 600,
                           heading: str | None = None) -> str:
    """The document fragment most relevant to the trigger.

    Two candidate kinds compete on bigram overlap with the trigger:
    - fenced code blocks (nearest heading 3x + lead-in paragraph 1.5x + block)
    - prose sections (heading 3x + section text, fences stripped) — so
      checklist/runbook conventions in plain markdown are eligible anchors

    When `heading` is given, only candidates under a heading containing that
    substring are eligible — deterministic anchoring when fuzzy matching is
    ambiguous (e.g. two sections sharing the topic keyword).

    Used as the judge's reference anchor: what the skill doc mandates for
    this kind of task."""
    import re

    body = path.read_text(encoding="utf-8")
    trig = ngrams(trigger)
    candidates: list[tuple[float, str]] = []

    # candidate kind 1: fenced code blocks with their heading/lead context
    for m in re.finditer(r"```[^\n]*\n(.*?)```", body, re.S):
        block = m.group(1).strip()
        if not block:
            continue
        before = body[:m.start()]
        heads = re.findall(r"^#{1,4} +([^\n]+)", before, re.M)
        head = heads[-1] if heads else ""
        if heading and heading not in head:
            continue
        lead = before.rstrip().rsplit("\n\n", 1)[-1][-200:]
        score = 3.0 * len(trig & ngrams(head)) \
            + 1.5 * len(trig & ngrams(lead)) \
            + len(trig & ngrams(block))
        candidates.append((score, block))

    # candidate kind 2: prose sections (fence content stripped)
    marks = list(re.finditer(r"^#{1,4} +([^\n]+)", body, re.M))
    for i, m in enumerate(marks):
        if heading and heading not in m.group(1):
            continue
        end = marks[i + 1].start() if i + 1 < len(marks) else len(body)
        prose = re.sub(r"```[^\n]*\n.*?```", " ", body[m.end():end], flags=re.S).strip()
        prose = re.sub(r"\s+", " ", prose)
        if len(prose) < 80:
            continue
        score = 3.0 * len(trig & ngrams(m.group(1))) + len(trig & ngrams(prose))
        candidates.append((score, prose))

    if candidates:
        return max(candidates)[1][:limit]
    paras = [p.strip() for p in body.split("\n\n") if len(p.strip()) > 60]
    return (paras[0] if paras else body)[:limit]

# smelt v0.3.1 variable contract: SMELT_API_KEY / SMELT_BASE_URL.
BASE_URL = os.environ.get("SMELT_BASE_URL", "https://api.moonshot.cn/v1")
AGENT_MODEL = os.environ.get("SMELT_AGENT_MODEL", "kimi-k2")
JUDGE_MODEL = os.environ.get("SMELT_JUDGE_MODEL", "kimi-k2")

requires_llm = pytest.mark.skipif(
    not os.environ.get("SMELT_API_KEY"),
    reason="needs SMELT_API_KEY (real-model behavior case; see evals/.env.template)",
)


def _api_key() -> str | None:
    return os.environ.get("SMELT_API_KEY")


def _is_deepseek() -> bool:
    return "deepseek" in (BASE_URL or "").lower()


@pytest.fixture(scope="session")
def agent_llm():
    """LLM client for the agent under test.

    Plain OpenAIChatClient — smelt v0.4.1 emits wire-format tool_calls
    (id/type/function + tool_call_id), so strict providers accept it.
    On DeepSeek, thinking mode must be disabled for tool loops (the API
    rejects multi-turn requests unless reasoning_content is echoed back);
    v0.4.1's extra_body passthrough handles that.
    """
    from smelt import OpenAIChatClient

    kwargs: dict = {}
    if _is_deepseek():
        kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
    return OpenAIChatClient(
        model=AGENT_MODEL, base_url=BASE_URL, api_key=_api_key(), **kwargs
    )


@pytest.fixture(scope="session")
def judge_llm():
    """LLM client for llm_judge; may differ from the agent model."""
    from smelt import OpenAIChatClient

    return OpenAIChatClient(model=JUDGE_MODEL, base_url=BASE_URL, api_key=_api_key())


# ---------------------------------------------------------------------------
# Tools for the agent under test
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def run_command_tool():
    """A shell tool; smelt runs tool handlers inside the case workspace."""
    from smelt import tool

    @tool
    def run_command(cmd: str) -> str:
        """Run a shell command in the workspace and return its output."""
        proc = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, timeout=30
        )
        out = (proc.stdout + proc.stderr).strip()
        return out or f"(exit {proc.returncode}, no output)"

    return run_command


@pytest.fixture(scope="session")
def read_file_tool():
    """A file reader; lets the agent follow SKILL.md's "see references/x.md"
    pointers when the skill directory is materialized into the workspace."""
    from smelt import tool

    @tool
    def read_file(path: str) -> str:
        """Read a UTF-8 text file from the workspace and return its content."""
        p = Path(path)
        if not p.is_file():
            return f"file not found: {path}"
        return p.read_text(encoding="utf-8", errors="replace")[:8000]

    return read_file


class ToolArgsContain:
    """Custom expectation: a tool was called with arguments containing fragment.

    Asserts on what the agent actually DID (trace tool-call arguments), not on
    what it SAID — final answers paraphrase, commands don't.
    """

    def __init__(self, tool: str, fragment: str, threshold: float = 1.0):
        self.name = f"tool_args_contain({tool!r}, {fragment!r})"
        self.threshold = threshold
        self._tool = tool
        self._fragment = fragment

    def evaluate(self, trace):
        import json

        from smelt import ExpectationResult

        hits = [
            c
            for c in trace.tool_calls
            if c.name == self._tool and self._fragment in json.dumps(c.arguments)
        ]
        return ExpectationResult(
            name=self.name,
            score=1.0 if hits else 0.0,
            threshold=self.threshold,
            message=f"{len(hits)} call(s) to {self._tool} containing {self._fragment!r}",
        )


class NoToolArgsContain:
    """Inverse of ToolArgsContain: NO tool call may contain the fragment.

    For safety assertions — destructive commands (reflog expire, gc --prune)
    must never appear in the trace.
    """

    def __init__(self, tool: str, fragment: str, threshold: float = 1.0):
        self.name = f"no_tool_args_contain({tool!r}, {fragment!r})"
        self.threshold = threshold
        self._tool = tool
        self._fragment = fragment

    def evaluate(self, trace):
        import json

        from smelt import ExpectationResult

        hits = [
            c
            for c in trace.tool_calls
            if c.name == self._tool and self._fragment in json.dumps(c.arguments)
        ]
        return ExpectationResult(
            name=self.name,
            score=0.0 if hits else 1.0,
            threshold=self.threshold,
            message=f"{len(hits)} forbidden call(s) containing {self._fragment!r}",
        )


# ---------------------------------------------------------------------------
# Workspace fixtures (materialized via smelt's context(files=...))
# ---------------------------------------------------------------------------


@pytest.fixture()
def dirty_git_repo(tmp_path: Path) -> Path:
    """A small git repo with committed history plus staged changes.

    Returned path is handed to smelt's context(files=...), which copies the
    whole tree (including .git) into the isolated case workspace.
    """
    repo = tmp_path / "dirty_repo"
    repo.mkdir()

    def git(*args: str) -> None:
        subprocess.run(
            ["git", *args],
            cwd=repo,
            check=True,
            capture_output=True,
            env={
                **os.environ,
                "GIT_AUTHOR_NAME": "eval",
                "GIT_AUTHOR_EMAIL": "eval@example.com",
                "GIT_COMMITTER_NAME": "eval",
                "GIT_COMMITTER_EMAIL": "eval@example.com",
            },
        )

    git("init", "-b", "main")
    (repo / "app.py").write_text("def add(a, b):\n    return a + b\n")
    git("add", ".")
    git("commit", "-m", "wip")  # intentionally bad message for reword cases
    (repo / "app.py").write_text("def add(a, b):\n    return a + b\n\n\ndef sub(a, b):\n    return a - b\n")
    (repo / "README.md").write_text("# demo\n")
    git("add", ".")
    # staged changes on top of a badly-worded commit: ready for amend/reword
    return repo
