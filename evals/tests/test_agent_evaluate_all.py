"""Full evaluate_agent for every MindForge subagent definition, bilingual.

One parametrized test per (lang, agent): runs smelt's comprehensive agent
evaluation (behavior + agent writing review + lint + suggestions) and saves
markdown/JSON reports to evals/reports/agent-{lang}-{name}.{md,json}.

Behavior cases come from test_agent_behavior.py (single source of truth);
evaluate_agent auto-binds each case to a subagent() over the file under
review with the harness's Claude Code tools.

The challenger (adversarial routing probes) runs for one agent per language
— the descriptions are shared per roster, so probe results generalize; the
skill suite runs challengers the same way, separately and on demand.

Single-sample (.with_times(1)) to keep cost sane across 18 evaluations.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from smelt import context, evaluate_agent

from conftest import AGENT_ROOTS, requires_llm
from test_agent_behavior import ALL_AGENTS, build_behavior_case, materialize_files

pytestmark = [pytest.mark.llm, requires_llm]

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"

# agents whose evaluate run includes adversarial routing probes
CHALLENGE_AGENTS = {"code-reviewer"}


@pytest.mark.parametrize("lang", ["en", "zh-cn"])
@pytest.mark.parametrize("agent", ALL_AGENTS, ids=[a.removesuffix(".md") for a in ALL_AGENTS])
def test_evaluate_agent_full(lang, agent, agent_llm, judge_llm, claude_tools, tmp_path):
    files, case = build_behavior_case(lang, agent, judge_llm=judge_llm)
    if files:
        case = case.given(context(files=materialize_files(files, tmp_path / "ws")))

    report = (
        evaluate_agent(AGENT_ROOTS[lang] / agent, judge=judge_llm, agent_llm=agent_llm,
                       tools=claude_tools)
        .with_cases(case)
        .with_times(1)
        .with_challenge(enabled=agent.removesuffix(".md") in CHALLENGE_AGENTS)
        .with_suggestions(max_items=3)
        .run()
    )

    REPORTS_DIR.mkdir(exist_ok=True)
    stem = agent.removesuffix(".md")
    report.save(REPORTS_DIR / f"agent-{lang}-{stem}.md")
    report.save(REPORTS_DIR / f"agent-{lang}-{stem}.json")

    assert 0 <= report.overall_score <= 100
    assert report.grade in "ABCDF"
