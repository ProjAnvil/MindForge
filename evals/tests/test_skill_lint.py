"""Static quality lint for every SKILL.md in the repo (deterministic, no LLM).

Baseline measured 2026-10-06 with smelt 0.2.0:
    en    83.2 ~ 92.0  (all pass)
    zh-cn 68.4 ~ 91.2  (all pass)
The floor below catches regressions without failing the current baseline.
"""

from __future__ import annotations

import pytest
from smelt.lint import build_report, discover_skills, load_skill, run_checks

from conftest import SKILL_ROOTS

LINT_FLOOR = 60.0

_CASES = [
    pytest.param(path, id=f"{lang}/{path.name}")
    for lang, root in SKILL_ROOTS.items()
    for path in sorted(discover_skills(root))
]


@pytest.mark.parametrize("skill_path", _CASES)
def test_skill_lint(skill_path):
    report = build_report(load_skill(skill_path), run_checks(load_skill(skill_path)))
    assert report.passed, f"{skill_path}: lint checks failed"
    assert report.total_score >= LINT_FLOOR, (
        f"{skill_path}: lint score {report.total_score:.1f} below floor {LINT_FLOOR}"
    )
