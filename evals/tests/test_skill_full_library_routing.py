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
        ("database-design", "Draw an ER diagram and plan sharding for a large table"),
        ("design-pattern", "Apply SOLID principles to remove code smells in a refactor"),
        ("git-guru", "Use interactive rebase and bisect to clean up commit history"),
        ("product-management", "Draft a PRD and define the MVP for a new feature"),
        ("session-summary", "Write a handover document for the next session"),
        ("swift-development", "Fix a data race under Swift 6 strict concurrency"),
        ("swiftui-development", "Build a SwiftUI view with NavigationStack and SwiftData"),
        ("system-architecture", "Write an architecture decision record for distributed systems"),
        ("xcode-management", "Resolve a .pbxproj merge conflict in an Xcode project"),
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
        ("database-design", "画 ER 图并规划大表的分片方案"),
        ("design-pattern", "用 SOLID 原则重构代码并消除代码异味"),
        ("git-guru", "用交互式变基和 bisect 清理提交历史"),
        ("product-management", "为新功能撰写 PRD 并定义 MVP"),
        ("session-summary", "生成一份会话交接文档"),
        ("swift-development", "修复 Swift 6 严格并发下的数据竞争"),
        ("swiftui-development", "用 NavigationStack 和 SwiftData 构建 SwiftUI 视图"),
        ("system-architecture", "为分布式系统写一份架构决策记录"),
        ("xcode-management", "解决 Xcode 项目里的 .pbxproj 合并冲突"),
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
