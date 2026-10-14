"""Behavior cases for every MindForge subagent definition (real model).

smelt's subagent() runs the agent file as the system under test: the markdown
body is the system prompt (description is routing metadata and is NOT
injected, matching Claude Code), and the `tools:` frontmatter allowlist is
hard-enforced against the provided tools. The harness provides the six core
Claude Code tools (Read/Grep/Glob/Bash/Edit/Write) backed by the case
workspace, so agents that declare them can actually inspect and write files.

One case per (lang, agent): the trigger exercises the agent's core specialty;
assertions pin what the BODY mandates (process steps, output artifacts) via
language-independent code vocabulary wherever possible.

The case builders are importable so test_agent_evaluate_all.py can feed the
same cases into the full evaluate_agent pipeline (single source of truth).
"""

from __future__ import annotations

import pytest
from smelt import (
    context,
    llm_judge,
    new_case,
    output_contains,
    subagent,
    text,
)

from conftest import AGENT_ROOTS, ToolArgsContain, requires_llm

pytestmark = [pytest.mark.llm, requires_llm]

ALL_AGENTS = sorted(p.name for p in AGENT_ROOTS["en"].glob("*.md"))

# ---------------------------------------------------------------------------
# Workspace fixtures: small inputs the tasks refer to
# ---------------------------------------------------------------------------

MESSY_SERVICE_PY = '''\
"""Order handling."""
import logging


class OrderService:
    """Creates, charges and notifies for orders."""

    def process_order(self, order, user, payment_gateway, mailer, audit, cache):
        if not order:
            return False
        if order.total < 0:
            return False
        if user is None:
            return False
        try:
            payment_gateway.charge(order.total, user.card_token)
        except Exception:
            pass
        try:
            mailer.send(user.email, "order confirmed")
        except Exception:
            pass
        cache.put("last_order", order.id)
        audit.write("order " + str(order.id))
        logging.info("processed" + str(order.id) + "for" + user.email)
        for item in order.items:
            if item.qty > 0:
                if item.price > 0:
                    if item.sku:
                        logging.info(item.sku)
        return True
'''

CALCULATOR_JAVA = """\
public class Calculator {
    public int add(int a, int b) {
        return a + b;
    }

    public int divide(int a, int b) {
        return a / b;
    }
}
"""

APP_PY = """\
def add(a, b):
    return a + b


def format_name(first, last):
    return first + " " + last
"""

# ---------------------------------------------------------------------------
# Per-agent behavior table: (workspace files, bilingual trigger, assertions)
# ---------------------------------------------------------------------------

REVIEW_CRITERIA = (
    "The response is a structured code review that names concrete problems "
    "in the given code — such as the silently swallowed exceptions, the "
    "oversized multi-responsibility method, poor naming/readability, or "
    "missing test coverage — and suggests actionable fixes, ideally "
    "prioritized by severity."
)

REVIEW_CRITERIA_ZH = (
    "回复是一份结构化的代码评审：指出了给定代码的具体问题——例如被静默吞掉的异常、"
    "职责过多的大方法、命名或可读性缺陷、缺少测试等——并给出可执行的修复建议，"
    "最好按严重程度排序。"
)


def _behavior_spec(lang: str, agent: str):
    """(files, trigger, then-builder) for one (lang, agent) behavior case.

    then-builder receives judge_llm (may be None when no judge is needed)."""
    stem = agent.removesuffix(".md")

    if stem == "code-reviewer":
        def then(judge_llm):
            return (
                llm_judge(judge_llm, criteria=REVIEW_CRITERIA if lang == "en" else REVIEW_CRITERIA_ZH,
                          threshold=0.6, include_trace=True),
            )
        return {"service.py": MESSY_SERVICE_PY}, (
            {
                "en": "Review service.py in this workspace and tell me what to fix",
                "zh-cn": "审查一下工作区里的 service.py，告诉我需要修复什么",
            }[lang]
        ), then

    if stem == "frontend-engineer":
        return {"package.json": '{\n  "name": "demo",\n  "devDependencies": {}\n}\n'}, (
            {
                "en": "Create a Svelte 5 counter component in src/Counter.svelte",
                "zh-cn": "在 src/Counter.svelte 里创建一个 Svelte 5 计数器组件",
            }[lang]
        ), lambda judge_llm: (
            ToolArgsContain("Write", "Counter.svelte"),
            output_contains(".svelte"),
        )

    if stem == "golang-backend-engineer":
        return {"go.mod": "module demo\n\ngo 1.22\n"}, (
            {
                "en": "Add a /healthz HTTP endpoint to this Go module in main.go",
                "zh-cn": "给这个 Go 模块加一个 /healthz HTTP 端点，写在 main.go 里",
            }[lang]
        ), lambda judge_llm: (
            ToolArgsContain("Write", "main.go"),
            ToolArgsContain("Write", "healthz"),
        )

    if stem == "ios-developer":
        return {}, (
            {
                "en": "Create a SwiftUI view in SettingsView.swift showing a dark-mode toggle",
                "zh-cn": "创建 SettingsView.swift，用 SwiftUI 实现一个深色模式开关",
            }[lang]
        ), lambda judge_llm: (
            ToolArgsContain("Write", "SettingsView.swift"),
            ToolArgsContain("Write", "SwiftUI"),
        )

    if stem == "java-backend-engineer":
        return {"pom.xml": "<project></project>\n"}, (
            {
                "en": "Write a Spring OrderService in src/main/java/demo/OrderService.java",
                "zh-cn": "在 src/main/java/demo/OrderService.java 写一个 Spring 的 OrderService",
            }[lang]
        ), lambda judge_llm: (
            ToolArgsContain("Write", "OrderService.java"),
            ToolArgsContain("Write", "@Service"),
        )

    if stem == "java-unit-test":
        return {"Calculator.java": CALCULATOR_JAVA}, (
            {
                "en": "Write JUnit tests for Calculator.java in this workspace",
                "zh-cn": "为工作区里的 Calculator.java 写 JUnit 测试",
            }[lang]
        ), lambda judge_llm: (
            ToolArgsContain("Read", "Calculator.java"),
            ToolArgsContain("Write", "@Test"),
        )

    if stem == "product-manager":
        return {}, (
            {
                "en": "Write user stories with acceptance criteria for a password-reset feature",
                "zh-cn": "为密码重置功能写带验收标准的用户故事",
            }[lang]
        ), lambda judge_llm: (
            output_contains("As a" if lang == "en" else "作为"),
        )

    if stem == "python-test-engineer":
        return {"app.py": APP_PY}, (
            {
                "en": "Write pytest tests for the functions in app.py",
                "zh-cn": "为 app.py 里的函数写 pytest 测试",
            }[lang]
        ), lambda judge_llm: (
            ToolArgsContain("Read", "app.py"),
            ToolArgsContain("Write", "def test_"),
        )

    if stem == "system-architect":
        return {}, (
            {
                "en": "Write an architecture overview for a payment processing system",
                "zh-cn": "为一个支付处理系统写一份架构概述",
            }[lang]
        ), lambda judge_llm: (
            output_contains("Architecture" if lang == "en" else "架构"),
        )

    raise ValueError(f"no behavior spec for agent {agent!r}")


def build_behavior_case(lang: str, agent: str, *, judge_llm):
    """A behavior case for one agent, agent NOT bound (caller binds).

    Returns (files, case): files is the {relpath: content} workspace dict."""
    files, trigger, then_builder = _behavior_spec(lang, agent)
    case = (
        new_case(f"behavior-{lang}-{agent.removesuffix('.md')}")
        .when(text(trigger))
    )
    for expectation in then_builder(judge_llm):
        case = case.then(expectation)
    return files, case


def materialize_files(files: dict[str, str], base) -> "Path":
    """Write a {relpath: content} dict under base; returns base for context(files=...)."""
    from pathlib import Path

    base = Path(base)
    base.mkdir(parents=True, exist_ok=True)
    for rel, content in files.items():
        p = base / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
    return base


# ---------------------------------------------------------------------------
# The tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("lang", ["en", "zh-cn"])
@pytest.mark.parametrize("agent", ALL_AGENTS, ids=[a.removesuffix(".md") for a in ALL_AGENTS])
def test_agent_behavior(lang, agent, agent_llm, judge_llm, claude_tools, tmp_path):
    files, case = build_behavior_case(lang, agent, judge_llm=judge_llm)
    if files:
        case = case.given(context(files=materialize_files(files, tmp_path / "ws")))
    case = case.given(subagent(AGENT_ROOTS[lang] / agent, llm=agent_llm, tools=claude_tools))
    result = case.report(quiet=True)
    result.assert_passed()
