"""git-guru case file for `smelt run` / `smelt doctor` (module-level SmeltCase).

Usage (from evals/):
    uv run smelt run cases/git_guru_cases.py -v
    uv run smelt doctor --skill ../skills/en/git-guru cases/git_guru_cases.py
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from smelt import (
    OpenAIChatClient,
    context,
    new_case,
    output_contains,
    smelt_agent,
    text,
    tool,
    tool_call,
)

import smelt

smelt.load_env(Path(__file__).resolve().parent.parent / ".env")

SKILL_DIR = Path(__file__).resolve().parent.parent.parent / "skills" / "en" / "git-guru"


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
def run_command(cmd: str) -> str:
    """Run a shell command in the workspace and return its output."""
    proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    out = (proc.stdout + proc.stderr).strip()
    return out or f"(exit {proc.returncode}, no output)"


case_bisect = (
    new_case("git-guru-bisect-explainer")
    .given(smelt_agent(SKILL_DIR, llm=_llm(), tools=[run_command]))
    .when(text("How do I find which commit introduced a bug? Just explain."))
    .then(output_contains("bisect"))
)


cases = [case_bisect]
