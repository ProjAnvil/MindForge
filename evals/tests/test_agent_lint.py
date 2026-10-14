"""Static quality lint for every agent definition file (deterministic, no LLM).

smelt 0.6.0 treats Claude Code agent markdown as a first-class document kind:
AgentFrontmatterCheck (load contract), DelegationCheck (description routes),
plus the shared metadata/structure/clarity checks in agent mode.

Baseline measured 2026-10-14 with smelt 0.6.0: all 18 files score 100.
"""

from __future__ import annotations

import pytest
from smelt.lint import build_report, run_checks
from smelt.lint.loader import load_agent

from conftest import AGENT_ROOTS

AGENT_LINT_FLOOR = 95.0

_CASES = [
    pytest.param(path, id=f"{lang}/{path.name}")
    for lang, root in AGENT_ROOTS.items()
    for path in sorted(root.glob("*.md"))
]


@pytest.mark.parametrize("agent_path", _CASES)
def test_agent_lint(agent_path):
    doc = load_agent(agent_path)
    report = build_report(doc, run_checks(doc))
    assert report.passed, f"{agent_path}: lint checks failed"
    assert report.total_score >= AGENT_LINT_FLOOR, (
        f"{agent_path}: lint score {report.total_score:.1f} below floor {AGENT_LINT_FLOOR}"
    )
