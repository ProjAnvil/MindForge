"""Comprehensive evaluate_skill report for the weakest lint-scored skill.

zh-cn/frontend-vue holds the lowest lint score in the repo (68.4, D). This
test runs smelt's full evaluation — behavior cases + writing review + lint +
improvement suggestions — and saves markdown/JSON reports under evals/reports/
for tracking across skill revisions. Also exercises the dimensions-mode judge
(one categorical judge call per dimension).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from smelt import evaluate_skill, llm_judge, new_case, output_contains, text

from conftest import REFERENCES_HINT, SKILL_ROOTS, requires_llm

pytestmark = [pytest.mark.llm, requires_llm]

SKILL_DIR = SKILL_ROOTS["zh-cn"] / "frontend-vue"
REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"


def test_evaluate_frontend_vue_zh(agent_llm, judge_llm):
    report = (
        evaluate_skill(SKILL_DIR, judge=judge_llm, agent_llm=agent_llm)
        .with_cases(
            new_case("vue-composition-api")
            .when(text("用 Vue 3 Composition API 写一个带加载状态的搜索框组件"))
            .then(output_contains("setup", "ref"))
            .then(
                llm_judge(
                    judge_llm,
                    dimensions=["domain correctness", "code quality", "chinese clarity"],
                    threshold=0.6,
                )
            ),
            new_case("vue-state-management")
            .when(text("Vue 项目里多个组件共享购物车状态应该怎么做？"))
            .then(output_contains("Pinia")),
        )
        .with_challenge(enabled=False)  # challenger probes run separately on demand
        .with_suggestions(max_items=5)
        .run()
    )

    REPORTS_DIR.mkdir(exist_ok=True)
    report.save(REPORTS_DIR / "zh-cn-frontend-vue.md")
    report.save(REPORTS_DIR / "zh-cn-frontend-vue.json")

    assert 0 <= report.overall_score <= 100
    assert report.grade in "ABCDF"
