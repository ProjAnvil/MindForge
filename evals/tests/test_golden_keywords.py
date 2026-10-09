"""Golden-keyword behavior cases for every skill domain, bilingual (real model).

All 19 skills x 2 languages: each row pins one canonical trigger per language
with output fragments that any competent answer from that skill must contain.
These complement the judge-based smoke suite with cheap, precise assertions
(one model call per case, no judge needed).
"""

from __future__ import annotations

import pytest
from smelt import new_case, output_contains, smelt_agent, text

from conftest import SKILL_ROOTS, requires_llm

pytestmark = [pytest.mark.llm, requires_llm]

# (skill, {lang: trigger}, expected fragments)
# Fragments are chosen to be near-deterministic for the skill's domain:
# code constructs (@RestController, useState), product names (PostgreSQL,
# Pinia), and format conventions ("As a", "作为") survive paraphrasing.
CASES = [
    (
        "testing",
        {
            "en": "Write unit tests for a function that calculates shopping-cart discounts",
            # testing skill teaches clarify-first; be explicit to force code output
            "zh-cn": "帮我为一个计算购物车折扣的函数写单元测试，直接给出 pytest 代码",
        },
        ("def test_",),
    ),
    (
        "python-development",
        {
            "en": "Write a Python function that checks whether a string is a palindrome",
            "zh-cn": "写一个判断字符串是否为回文的 Python 函数",
        },
        ("def ", "return"),
    ),
    (
        "api-design",
        {
            "en": "Design the REST endpoints for a blog's comment resource",
            "zh-cn": "为博客的评论资源设计 REST 接口",
        },
        ("GET", "POST"),
    ),
    (
        "database-design",
        {
            "en": "Design the database schema for an e-commerce order system",
            "zh-cn": "设计一个电商订单系统的数据库表结构",
        },
        ("CREATE TABLE",),
    ),
    (
        "design-pattern",
        {
            "en": "When should I use the Strategy pattern instead of a pile of if-else? Show a minimal code example",
            "zh-cn": "什么时候应该用策略模式替代一堆 if-else？给一个最小代码示例",
        },
        ("Strategy",),
    ),
    (
        "enterprise-java",
        {
            "en": "Create a minimal Spring Boot REST controller for a user resource",
            "zh-cn": "写一个最小的 Spring Boot 用户资源 REST 控制器",
        },
        ("@RestController",),
    ),
    (
        "frontend-react",
        {
            "en": "Write a React counter component with a useState hook",
            "zh-cn": "用 useState 写一个 React 计数器组件",
        },
        ("useState",),
    ),
    (
        "frontend-svelte",
        {
            "en": "Write a minimal Svelte component with a reactive counter",
            "zh-cn": "写一个最小的 Svelte 响应式计数器组件",
        },
        ("<script",),
    ),
    (
        "frontend-vue",
        {
            "en": "Write a Vue 3 Composition API counter component",
            "zh-cn": "用 Vue 3 Composition API 写一个计数器组件",
        },
        ("setup", "ref"),
    ),
    (
        "go-development",
        {
            "en": "Write a minimal Fiber hello-world HTTP server in Go",
            "zh-cn": "用 Fiber 写一个最小的 Go HTTP 服务",
        },
        ("fiber",),
    ),
    (
        "javascript-typescript",
        {
            "en": "Write a TypeScript generic function that returns the first element of an array",
            "zh-cn": "写一个 TypeScript 泛型函数，返回数组的第一个元素",
        },
        ("function", "<T"),
    ),
    (
        "product-management",
        {
            "en": "Write a one-sentence user story for a password reset feature",
            "zh-cn": "为密码重置功能写一条用户故事",
        },
        ("As a",),  # zh-cn answer conventionally starts “作为……”, checked below
    ),
    (
        "session-summary",
        {
            "en": "Summarize this session for handover: we fixed a login bug and decided to migrate to Postgres",
            "zh-cn": "总结一下这个会话用于交接：我们修复了登录 bug，并决定迁移到 Postgres",
        },
        ("Postgres",),
    ),
    (
        "swift-development",
        {
            "en": "Write a Swift User struct with id and name, and fetch it with async/await",
            "zh-cn": "写一个 Swift 的 User 数据模型，并用 async/await 获取它",
        },
        ("struct", "async"),
    ),
    (
        "swiftui-development",
        {
            "en": "Write a SwiftUI view with a NavigationStack showing a list of items",
            "zh-cn": "写一个用 NavigationStack 展示列表的 SwiftUI 视图",
        },
        ("NavigationStack",),
    ),
    (
        "system-architecture",
        {
            "en": "Write an architecture decision record for choosing PostgreSQL over MongoDB",
            "zh-cn": "写一份选择 PostgreSQL 而非 MongoDB 的架构决策记录",
        },
        ("PostgreSQL", "MongoDB"),
    ),
    (
        "tech-documentation",
        {
            "en": "Write the outline of an API documentation page for a /users endpoint",
            "zh-cn": "为 /users 接口写一份 API 文档大纲",
        },
        ("/users",),
    ),
    (
        "xcode-management",
        {
            "en": "What is the .pbxproj file and why does it cause merge conflicts?",
            "zh-cn": ".pbxproj 文件是做什么的？为什么容易产生合并冲突？",
        },
        ("pbxproj",),
    ),
]

# Language-specific fragment overrides: a few conventions differ by language
# (e.g. user stories open with "As a" in English but "作为" in Chinese).
LANG_FRAGMENTS = {
    ("product-management", "zh-cn"): ("作为",),
}

_CASES = [
    pytest.param(
        skill,
        lang,
        trigger,
        LANG_FRAGMENTS.get((skill, lang), expected),
        id=f"{lang}/{skill}",
    )
    for skill, triggers, expected in CASES
    for lang, trigger in triggers.items()
]


@pytest.mark.parametrize(("skill", "lang", "trigger", "expected"), _CASES)
def test_golden_keywords(skill, lang, trigger, expected, agent_llm):
    result = (
        new_case(f"golden-{lang}-{skill}")
        .given(smelt_agent(SKILL_ROOTS[lang] / skill, llm=agent_llm))
        .when(text(trigger))
        .then(output_contains(*expected))
        .report(quiet=True)  # runs the case and writes a per-case HTML report
    )
    result.assert_passed()
