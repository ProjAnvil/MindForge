"""Ablation probe: does loading the SKILL.md actually change the score?

Runs the same trigger twice — once with the real skill as system prompt,
once with a bare "helpful assistant" prompt — under identical assertions.
If both score the same, the assertion layer measures the base model's
competence, not the skill's contribution (i.e. the metric has no
discriminating power for skill quality).

Usage: uv run python scripts/ablation.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))  # for conftest

import smelt  # noqa: E402
from smelt import llm_judge, new_case, output_contains, smelt_agent, text  # noqa: E402

from conftest import AGENT_MODEL, BASE_URL, JUDGE_MODEL, SKILL_ROOTS  # noqa: E402

smelt.load_env(Path(__file__).resolve().parent.parent / ".env")

BARE_PROMPT = "You are a helpful assistant."

JUDGE_CRITERIA = (
    "The response must be substantively about the skill domain implied by the "
    "user's request, must be concrete and helpful (not a generic disclaimer), "
    "and must be written in the same language as the user's message."
)

# (label, skill_dir_or_None, trigger, keyword-fragments)
CASES = [
    ("react-counter", SKILL_ROOTS["en"] / "frontend-react",
     "Write a React counter component with a useState hook", ("useState",)),
    ("vue-counter-zh", SKILL_ROOTS["zh-cn"] / "frontend-vue",
     "用 Vue 3 Composition API 写一个计数器组件", ("setup", "ref")),
    ("db-schema", SKILL_ROOTS["en"] / "database-design",
     "Design the database schema for an e-commerce order system", ("CREATE TABLE",)),
    ("adr", SKILL_ROOTS["en"] / "system-architecture",
     "Write an architecture decision record for choosing PostgreSQL over MongoDB",
     ("PostgreSQL", "MongoDB")),
]


def make_llms():
    from smelt import OpenAIChatClient

    kwargs: dict = {}
    if "deepseek" in (BASE_URL or ""):
        # v0.4.1 wire-format tool loops work; thinking mode must be off
        kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
    agent = OpenAIChatClient(
        model=AGENT_MODEL, base_url=BASE_URL,
        api_key=os.environ["SMELT_API_KEY"], **kwargs,
    )
    judge = OpenAIChatClient(
        model=JUDGE_MODEL, base_url=BASE_URL, api_key=os.environ["SMELT_API_KEY"]
    )
    return agent, judge


def main() -> None:
    agent_llm, judge_llm = make_llms()
    print(f"{'case':16s} {'with-skill':>12s} {'no-skill':>10s} {'judge w/':>9s} {'judge w/o':>10s}")
    for label, skill_dir, trigger, fragments in CASES:
        scores = {}
        for mode in ("skill", "bare"):
            agent = (
                smelt_agent(skill_dir, llm=agent_llm)
                if mode == "skill"
                else smelt_agent(llm=agent_llm, system_prompt=BARE_PROMPT)
            )
            result = (
                new_case(f"ablation-{label}-{mode}")
                .given(agent)
                .when(text(trigger))
                .then(output_contains(*fragments))
                .then(llm_judge(judge_llm, criteria=JUDGE_CRITERIA, threshold=0.6))
                .run()
            )
            kw = result.expectations[0].score
            jd = result.expectations[1].score
            scores[mode] = (kw, jd)
        print(
            f"{label:16s} {scores['skill'][0]:12.2f} {scores['bare'][0]:10.2f}"
            f" {scores['skill'][1]:9.2f} {scores['bare'][1]:10.2f}"
        )


if __name__ == "__main__":
    main()
