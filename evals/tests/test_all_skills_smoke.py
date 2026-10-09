"""Behavior smoke test for every skill, both languages (real model).

Each of the 38 skills (19 en + 19 zh-cn) is loaded into smelt_agent, triggered
with its own frontmatter description (always in the skill's language), and
graded by llm_judge for domain relevance and language consistency.

Deterministic CI stays green without credentials: the whole module skips when
SMELT_API_KEY is unset.
"""

from __future__ import annotations

import pytest
from smelt import llm_judge, new_case, smelt_agent, text

from conftest import SKILL_ROOTS, all_skill_dirs, requires_llm, skill_description

pytestmark = [pytest.mark.llm, requires_llm]

JUDGE_CRITERIA = (
    "The response must be substantively about the skill domain implied by the "
    "user's request, must be concrete and helpful (not a generic disclaimer), "
    "and must be written in the same language as the user's message "
    "(Chinese trigger -> Chinese answer, English trigger -> English answer)."
)

_CASES = [
    pytest.param(lang, skill_dir, id=f"{lang}/{skill_dir.name}")
    for lang, skill_dir in all_skill_dirs()
]


@pytest.mark.parametrize(("lang", "skill_dir"), _CASES)
def test_skill_trigger_smoke(lang, skill_dir, agent_llm, judge_llm):
    trigger = skill_description(skill_dir)
    assert trigger, f"{skill_dir}: no frontmatter description to trigger on"
    result = (
        new_case(f"smoke-{lang}-{skill_dir.name}")
        .given(smelt_agent(skill_dir, llm=agent_llm))
        .when(text(trigger))
        .then(llm_judge(judge_llm, criteria=JUDGE_CRITERIA, threshold=0.6))
        .report(quiet=True)  # runs the case and writes a per-case HTML report
    )
    result.assert_passed()
