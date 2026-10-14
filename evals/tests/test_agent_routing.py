"""Delegation routing cases for the MindForge agent rosters (real model).

smelt's router_agent() simulates the Claude Code main agent: it sees the
roster (name + description of every agents/<lang>/*.md) and may delegate via
a stubbed Task tool. These cases pin the routing contract the descriptions
promise: in-specialty tasks get delegated to the right subagent, sibling
specialties must not steal them, and trivial tasks stay with the main agent.
"""

from __future__ import annotations

import pytest
from smelt import delegates_to, new_case, no_delegation, no_delegation_to, router_agent, text

from conftest import AGENT_ROOTS, requires_llm

pytestmark = [pytest.mark.llm, requires_llm]

# (case name, trigger per language, expectation kind, target agent)
# Triggers must be self-contained: the router prompt delegates "a task with a
# self-contained prompt", so anything the task references (code, the idea
# itself) has to be inline — otherwise the main agent asks for it instead.
ROUTING_CASES = [
    (
        "delegate-code-review",
        {
            "en": (
                "Review this code for architecture problems and code smells before I commit it: "
                "class OrderService { void saveOrder(Order o) { validate(o); repo.save(o); "
                "mailer.send(o); audit.log(o); cache.put(o); } }"
            ),
            "zh-cn": (
                "提交之前帮我审查一下这段代码有没有架构问题和代码坏味道："
                "class OrderService { void saveOrder(Order o) { validate(o); repo.save(o); "
                "mailer.send(o); audit.log(o); cache.put(o); } }"
            ),
        },
        "delegate",
        "code-reviewer",
    ),
    (
        "delegate-product-planning",
        {
            "en": (
                "Turn this rough idea into user stories and a feature breakdown: "
                "'users should be able to reset their password via an emailed link'"
            ),
            "zh-cn": (
                "把这个粗略的想法整理成用户故事和功能拆解："
                "'用户应该能通过邮件里的链接重置密码'"
            ),
        },
        "delegate",
        "product-manager",
    ),
    (
        "sibling-python-not-java-tests",
        {
            "en": "Write unit tests for this function: def calc_total(items): return sum(i.price for i in items)",
            "zh-cn": "为这个函数写单元测试：def calc_total(items): return sum(i.price for i in items)",
        },
        "sibling",
        "python-test-engineer",
    ),
    (
        "delegate-ios-feature",
        {
            "en": "Build a SwiftUI settings screen with a dark-mode toggle for my iOS app",
            "zh-cn": "给我的 iOS 应用做一个带深色模式开关的 SwiftUI 设置页面",
        },
        "delegate",
        "ios-developer",
    ),
    (
        "no-route-trivial",
        {
            "en": "Quick question, no code involved: what does 'idempotent' mean, in one sentence?",
            "zh-cn": "快速问一下，不涉及代码：一句话解释什么是「幂等」？",
        },
        "no_delegate",
        None,
    ),
]

SIBLING_VIOLATORS = {
    "sibling-python-not-java-tests": ("java-unit-test",),
}


@pytest.mark.parametrize("lang", ["en", "zh-cn"])
@pytest.mark.parametrize(
    "name,triggers,kind,target",
    [pytest.param(n, t, k, tg, id=n) for n, t, k, tg in ROUTING_CASES],
)
def test_agent_routing(lang, name, triggers, kind, target, agent_llm):
    case = (
        new_case(f"route-{lang}-{name}")
        .given(router_agent(AGENT_ROOTS[lang], llm=agent_llm))
        .when(text(triggers[lang]))
    )
    if kind == "delegate":
        case = case.then(delegates_to(target))
    elif kind == "sibling":
        case = case.then(delegates_to(target))
        for violator in SIBLING_VIOLATORS[name]:
            case = case.then(no_delegation_to(violator))
    else:
        case = case.then(no_delegation())
    result = case.report(quiet=True)
    result.assert_passed()
