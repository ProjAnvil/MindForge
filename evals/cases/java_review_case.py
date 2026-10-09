"""enterprise-java code-review case for `smelt doctor` (module-level SmeltCase).

Anchored on the skill's mandated review format from
references/response-patterns.md — doctor's drop_reference mutant for that
file should be KILLED by the keyword assertion (that is the point of the
exercise: a discriminating case kills its mutant).

Usage (from evals/):
    uv run smelt run cases/java_review_case.py -v
    uv run smelt doctor --skill ../skills/en/enterprise-java cases/java_review_case.py
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import smelt
from smelt import (
    OpenAIChatClient,
    context,
    new_case,
    output_contains,
    reference_folder,
    smelt_agent,
    text,
    tool,
)

smelt.load_env(Path(__file__).resolve().parent.parent / ".env")

SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "en" / "enterprise-java"

REFERENCES_HINT = (
    "The skill's files are materialized in the current workspace. When the "
    "skill document points to reference files (e.g. references/xxx.md), read "
    "them with the read_file tool BEFORE answering, and follow them exactly."
)

REVIEW_SNIPPET = (
    "public List<User> getUsers() { return userRepository.findAll().stream()"
    ".filter(u -> u.getName() != null).collect(Collectors.toList()); }"
)


def _llm() -> OpenAIChatClient:
    kwargs: dict = {}
    if "deepseek" in os.environ.get("SMELT_BASE_URL", ""):
        kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
    return OpenAIChatClient(
        model=os.environ.get("SMELT_AGENT_MODEL", "deepseek-v4-flash"),
        base_url=os.environ.get("SMELT_BASE_URL", "https://api.deepseek.com"),
        api_key=os.environ["SMELT_API_KEY"],
        **kwargs,
    )


@tool
def read_file(path: str) -> str:
    """Read a UTF-8 text file from the workspace and return its content."""
    p = Path(path)
    if not p.is_file():
        return f"file not found: {path}"
    return p.read_text(encoding="utf-8", errors="replace")[:8000]


case_review = (
    new_case("java-code-review-format")
    .given(reference_folder(SKILL_DIR))
    .given(context(prompt=REFERENCES_HINT))
    .given(smelt_agent(SKILL_DIR, llm=_llm(), tools=[read_file]))
    .when(text(f"Review this Java code: {REVIEW_SNIPPET}"))
    .then(output_contains("Code Review Summary", "Issues Found", "✅", "💡", threshold=0.75))
)

cases = [case_review]
