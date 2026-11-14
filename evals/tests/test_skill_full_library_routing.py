"""Full-library skill routing cases (real model).

The static guards in test_skill_trigger_disambiguation.py check the listing
text. This module checks the selection itself: the model sees every skill's
name + description at once, then must name the single skill that matches the
request. That is the failure mode measured in arXiv 2605.24050v2.

Requires SMELT_API_KEY; skipped in deterministic CI.
"""

from __future__ import annotations

import pytest
from smelt import new_case, output_contains, smelt_agent, text

from conftest import SKILL_ROOTS, requires_llm, skill_description

pytestmark = [pytest.mark.llm, requires_llm]

TRIGGERS: dict[str, list[tuple[str, str]]] = {
    "en": [
        ("frontend-svelte", "Build a SvelteKit route with a .svelte form component"),
        ("frontend-react", "Add a Next.js React Server Component with shadcn/ui"),
        ("frontend-vue", "Use Pinia for state in a Nuxt 3 application"),
        ("javascript-typescript", "Refactor this ES6+ module into strict TypeScript"),
        ("go-development", "Why does this goroutine keep running after context cancellation?"),
        ("python-development", "This generator yields nothing on the second iteration"),
        ("enterprise-java", "Virtual threads stall when a task enters a synchronized block"),
        ("api-design", "Design a GraphQL schema with OpenAPI versioning and idempotency"),
        ("tech-documentation", "Write deployment guides and an operations manual"),
        ("testing", "Set up test automation with TDD/BDD and mocking"),
    ],
    "zh-cn": [
        ("frontend-svelte", "用 SvelteKit 写一个 .svelte 表单组件"),
        ("frontend-react", "用 Next.js 加一个 React Server Component"),
        ("frontend-vue", "在 Nuxt 3 里用 Pinia 管理状态"),
        ("javascript-typescript", "把这个 ES6+ 模块重构成严格 TypeScript"),
        ("go-development", "context 取消之后这个协程为什么还在跑？"),
        ("python-development", "生成器第二次迭代为什么没有产出值"),
        ("enterprise-java", "虚拟线程进入 synchronized 之后为什么会卡住"),
        ("api-design", "设计带 OpenAPI 版本控制和幂等性的 GraphQL schema"),
        ("tech-documentation", "写部署指南和运维手册"),
        ("testing", "用 TDD/BDD 和 Mock 策略搭建测试自动化"),
    ],
}

_CASES = [
    (lang, expected, trigger)
    for lang in ("en", "zh-cn")
    for expected, trigger in TRIGGERS[lang]
]


def _listing(lang: str) -> str:
    lines = [
        "You route requests to installed skills.",
        "Reply with exactly one skill name from the list below. No explanation.",
        "Available skills:",
    ]
    for path in sorted(SKILL_ROOTS[lang].iterdir()):
        if (path / "SKILL.md").exists():
            lines.append(f"- {path.name}: {skill_description(path)}")
    return "\n".join(lines)


@pytest.mark.parametrize(("lang", "expected", "trigger"), _CASES)
def test_full_library_routing(lang, expected, trigger, agent_llm):
    result = (
        new_case(f"full-library-route-{lang}-{expected}")
        .given(smelt_agent(llm=agent_llm, system_prompt=_listing(lang)))
        .when(text(trigger))
        .then(output_contains(expected))
        .report(quiet=True)
    )
    result.assert_passed()
