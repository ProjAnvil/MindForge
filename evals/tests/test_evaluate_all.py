"""Full evaluate_skill + Reference Coverage for every skill, bilingual.

One parametrized test per (lang, skill): runs smelt's full evaluation
(behavior + writing + lint + suggestions) and saves markdown/JSON reports to
evals/reports/<lang>-<skill>.{md,json}.

Skills with references/ get one behavior case per reference file, each
asserting reference_read — the coverage table must show every targeted file
reached (an unreached targeted file means the SKILL.md pointer is not
discoverable). graphql-patterns.md style blind spots become test failures,
not silent dead docs.

Skills without references get one generic behavior case (golden keyword).

Single-sample (.with_times(1)) to keep cost sane across 38 evaluations;
flaky coverage shows up as a failure worth investigating, not retry-hiding.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from smelt import (
    context,
    evaluate_skill,
    new_case,
    output_contains,
    reference_folder,
    reference_read,
    text,
)

from conftest import REFERENCES_HINT, SKILL_ROOTS, requires_llm

pytestmark = [pytest.mark.llm, requires_llm]

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"

# ---------------------------------------------------------------------------
# skill -> [(reference file, {lang: trigger}), ...]
# ---------------------------------------------------------------------------
REF_CASES = {
    "api-design": [
        ("references/pagination-rate-limiting.md", {
            "en": "Design a paginated REST endpoint for a real-time feed of posts",
            "zh-cn": "为一个实时帖子动态流设计分页 REST 接口",
        }),
        ("references/openapi-template.md", {
            "en": "Write an OpenAPI 3.0 spec skeleton for a users API",
            "zh-cn": "为一个用户 API 写一份 OpenAPI 3.0 规范骨架",
        }),
        ("references/common-patterns.md", {
            "en": "Design a webhook for order status notifications",
            "zh-cn": "设计一个订单状态变更的 webhook",
        }),
        ("references/graphql-patterns.md", {
            "en": "Design a GraphQL schema for a blog with posts, authors and comments",
            "zh-cn": "为一个包含帖子、作者和评论的博客设计 GraphQL schema",
        }),
    ],
    "database-design": [
        ("references/migration-backup.md", {
            "en": "How do I add a column to a 100M-row users table with zero downtime?",
            "zh-cn": "如何给一张一亿行的用户表零停机加列？",
        }),
        ("references/query-optimization.md", {
            "en": "This query takes 30 seconds: SELECT * FROM orders o JOIN users u ON o.user_id = u.id WHERE u.city = 'Shanghai' ORDER BY o.created_at DESC — how do I optimize it?",
            "zh-cn": "这条查询要 30 秒：SELECT * FROM orders o JOIN users u ON o.user_id = u.id WHERE u.city = '上海' ORDER BY o.created_at DESC，怎么优化？",
        }),
        ("references/sharding-strategies.md", {
            "en": "Our orders table just hit 500M rows — design a sharding strategy",
            "zh-cn": "订单表已经 5 亿行了，设计一个分库分表方案",
        }),
    ],
    "design-pattern": [
        ({"en": "references/pattern-implementations.md",
          "zh-cn": "references/pattern-examples.md"}, {
            "en": "Implement the Strategy pattern for a payment system supporting credit card and PayPal",
            "zh-cn": "用策略模式实现一个支持信用卡和 PayPal 的支付系统",
        }),
    ],
    "enterprise-java": [
        ({"en": "references/class-templates.md",
          "zh-cn": "references/code-examples.md"}, {
            "en": "Create a Spring Service class for creating orders (OrderService.createOrder)",
            "zh-cn": "写一个创建订单的 Spring Service 类（OrderService，方法 createOrder）",
        }),
        # en only: second reference file
        ({"en": "references/response-patterns.md"}, {
            "en": "Review this Java code: public List<User> getUsers() { return userRepository.findAll(); }",
        }),
    ],
    "frontend-svelte": [
        ("references/api-patterns.md", {
            "en": "How do I load data for a SvelteKit page from an API?",
            "zh-cn": "SvelteKit 页面如何从 API 加载数据？",
        }),
        ("references/deployment-patterns.md", {
            "en": "How do I deploy my SvelteKit app to production?",
            "zh-cn": "如何把 SvelteKit 应用部署到生产环境？",
        }),
        ("references/forms-styling.md", {
            "en": "Build a contact form with validation in SvelteKit",
            "zh-cn": "用 SvelteKit 做一个带校验的联系表单",
        }),
        ("references/testing-performance-a11y.md", {
            "en": "Write tests for a Svelte component and review its accessibility",
            "zh-cn": "为一个 Svelte 组件写测试并检查它的可访问性",
        }),
    ],
    "git-guru": [
        ("references/advanced-features.md", {
            "en": "I lost a commit after a hard reset — how do I recover it with reflog?",
            "zh-cn": "我 hard reset 之后丢了一个提交，怎么用 reflog 找回来？",
        }),
        ("references/workflows-scenarios.md", {
            "en": "Walk me through cleaning up a messy feature branch before merging",
            "zh-cn": "带我梳理一下：合并之前如何整理一个凌乱的特性分支",
        }),
    ],
    "go-development": [
        ("references/file-templates.md", {
            "en": "Create a Fiber handler for registering users, following clean architecture",
            "zh-cn": "按整洁架构写一个 Fiber 的用户注册 handler",
        }),
    ],
    "javascript-typescript": [
        ("references/express-api-patterns.md", {
            "en": "Build an Express REST API for managing tasks",
            "zh-cn": "用 Express 写一个任务管理的 REST API",
        }),
        ("references/react-patterns.md", {
            "en": "Write a custom React hook for fetching data with loading and error states",
            "zh-cn": "写一个带加载和错误状态的 React 数据获取自定义 Hook",
        }),
        ("references/testing-patterns.md", {
            "en": "Write Jest tests for a debounce utility function",
            "zh-cn": "为一个 debounce 工具函数写 Jest 测试",
        }),
    ],
    "python-development": [
        ("references/django-patterns.md", {
            "en": "Create a Django model and list view for blog posts",
            "zh-cn": "创建一个博客文章的 Django 模型和列表视图",
        }),
        ("references/fastapi-patterns.md", {
            "en": "Create a FastAPI endpoint for creating items with validation",
            "zh-cn": "写一个带参数校验的 FastAPI 创建条目接口",
        }),
        ("references/testing-patterns.md", {
            "en": "Write pytest tests with fixtures for a user service",
            "zh-cn": "用 fixture 为用户服务写 pytest 测试",
        }),
    ],
    "system-architecture": [
        ("references/architecture-templates.md", {
            "en": "Write an architecture overview document for a payment processing system",
            "zh-cn": "为一个支付处理系统写架构概述文档",
        }),
    ],
    "tech-documentation": [
        ("references/api-doc-template.md", {
            "en": "Write API documentation for a POST /login endpoint",
            "zh-cn": "为 POST /login 接口写一份 API 文档",
        }),
        ("references/architecture-template.md", {
            "en": "Write an architecture design document for a chat application",
            "zh-cn": "为一个聊天应用写架构设计文档",
        }),
        ("references/deployment-template.md", {
            "en": "Write a deployment guide for a Node.js web app",
            "zh-cn": "为一个 Node.js Web 应用写部署指南",
        }),
    ],
    "testing": [
        ("references/language-specific-patterns.md", {
            "en": "Write unit tests for a discount calculator in both Python and JavaScript",
            "zh-cn": "用 Python 和 JavaScript 分别为折扣计算器写单元测试",
        }),
    ],
}

# ---------------------------------------------------------------------------
# skills without references/: one generic behavior case each
# ---------------------------------------------------------------------------
GENERIC_CASES = {
    "frontend-react": (
        {"en": "Write a React counter component with a useState hook",
         "zh-cn": "用 useState 写一个 React 计数器组件"},
        ("useState",),
    ),
    "frontend-vue": (
        {"en": "Write a Vue 3 Composition API counter component",
         "zh-cn": "用 Vue 3 Composition API 写一个计数器组件"},
        ("setup", "ref"),
    ),
    "product-management": (
        {"en": "Write a one-sentence user story for a password reset feature",
         "zh-cn": "为密码重置功能写一条用户故事"},
        ("As a",),  # zh-cn override below
    ),
    "session-summary": (
        {"en": "Summarize this session for handover: we fixed a login bug and decided to migrate to Postgres",
         "zh-cn": "总结一下这个会话用于交接：我们修复了登录 bug，并决定迁移到 Postgres"},
        ("Postgres",),
    ),
    "swift-development": (
        {"en": "Write a Swift User struct with id and name, and fetch it with async/await",
         "zh-cn": "写一个 Swift 的 User 数据模型，并用 async/await 获取它"},
        ("struct", "async"),
    ),
    "swiftui-development": (
        {"en": "Write a SwiftUI view with a NavigationStack showing a list of items",
         "zh-cn": "写一个用 NavigationStack 展示列表的 SwiftUI 视图"},
        ("NavigationStack",),
    ),
    # scripts/ are meant to be EXECUTED, not read — so the generic case asserts
    # the agent points the user at the script instead of reference_read-ing it
    "xcode-management": (
        {"en": "I have new Swift files on disk that aren't in my Xcode project — how do I add them automatically?",
         "zh-cn": "我磁盘上有几个新建的 Swift 文件还没加入 Xcode 工程，怎么自动加进去？"},
        ("add_files_to_xcode.py",),
    ),
}

GENERIC_FRAGMENTS_OVERRIDE = {
    ("product-management", "zh-cn"): ("作为",),
}

_ALL_SKILLS = sorted({d.name for root in SKILL_ROOTS.values() for d in root.iterdir() if (d / "SKILL.md").exists()})


def _ref_for(ref_spec, lang):
    """A ref entry is either a plain path or a per-language mapping."""
    if isinstance(ref_spec, dict):
        return ref_spec.get(lang)
    return ref_spec


@pytest.mark.parametrize("lang", ["en", "zh-cn"])
@pytest.mark.parametrize("skill", _ALL_SKILLS)
def test_evaluate_skill_full(lang, skill, agent_llm, judge_llm, read_file_tool):
    skill_dir = SKILL_ROOTS[lang] / skill
    targeted_refs: list[str] = []
    cases = []

    for ref_spec, triggers in REF_CASES.get(skill, []):
        ref = _ref_for(ref_spec, lang)
        trigger = triggers.get(lang)
        if ref is None or trigger is None:
            continue  # this reference file exists only in the other language
        targeted_refs.append(ref)
        cases.append(
            new_case(f"ref-{Path(ref).stem}")
            .given(reference_folder(skill_dir))
            .given(context(prompt=REFERENCES_HINT))
            .when(text(trigger))
            .then(reference_read(ref))
        )

    if not cases:
        triggers, fragments = GENERIC_CASES[skill]
        fragments = GENERIC_FRAGMENTS_OVERRIDE.get((skill, lang), fragments)
        cases.append(
            new_case("generic")
            .when(text(triggers[lang]))
            .then(output_contains(*fragments))
        )

    report = (
        evaluate_skill(skill_dir, judge=judge_llm, agent_llm=agent_llm,
                       tools=[read_file_tool])
        .with_cases(*cases)
        .with_times(1)
        .with_challenge(enabled=False)  # challenger probes run separately on demand
        .with_suggestions(max_items=3)
        .run()
    )

    REPORTS_DIR.mkdir(exist_ok=True)
    report.save(REPORTS_DIR / f"{lang}-{skill}.md")
    report.save(REPORTS_DIR / f"{lang}-{skill}.json")

    assert 0 <= report.overall_score <= 100
    assert report.grade in "ABCDF"

    if targeted_refs:
        coverage = {c["path"]: c["reached"] for c in (report.reference_coverage or [])}
        unreached = [r for r in targeted_refs if coverage.get(r, 0) < 1]
        assert not unreached, (
            f"{lang}/{skill}: targeted references never read — "
            f"SKILL.md pointers are not discoverable: {unreached}"
        )
