"""Doctor-ready routing cases for the Chinese agent roster.

Usage:
    uv run smelt run cases/zh-cn_agent_routing_cases.py -v
    uv run smelt doctor --agent ../agents/zh-cn/code-reviewer.md cases/zh-cn_agent_routing_cases.py

Description-mutants must break the routing cases (they guard the roster's
descriptions); body-mutants must not.
"""
from __future__ import annotations

import os
from pathlib import Path

import smelt
from smelt import (
    OpenAIChatClient,
    delegates_to,
    new_case,
    no_delegation,
    no_delegation_to,
    router_agent,
    text,
)

smelt.load_env(Path(__file__).resolve().parent.parent / ".env")

AGENTS_DIR = Path(__file__).resolve().parent.parent.parent / "agents" / "zh-cn"


def _llm() -> OpenAIChatClient:
    kwargs: dict = {}
    if "deepseek" in os.environ.get("SMELT_BASE_URL", ""):
        kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
    return OpenAIChatClient(
        model=os.environ.get("SMELT_AGENT_MODEL", "deepseek-v4-flash"),
        base_url=os.environ.get("SMELT_BASE_URL", "https://api.deepseek.com"),
        api_key=os.environ["SMELT_API_KEY"],
        **kwargs,
    )


def _router_case(name: str, trigger: str):
    return (
        new_case(f"route-zh-cn-{name}")
        .given(router_agent(AGENTS_DIR, llm=_llm()))
        .when(text(trigger))
    )


case_review = (
    _router_case("delegate-code-review",
                 "提交之前帮我审查一下这段代码有没有架构问题和代码坏味道："
                 "class OrderService { void saveOrder(Order o) { validate(o); repo.save(o); "
                 "mailer.send(o); audit.log(o); cache.put(o); } }")
    .then(delegates_to("code-reviewer"))
)

case_product = (
    _router_case("delegate-product-planning",
                 "把这个粗略的想法整理成用户故事和功能拆解："
                 "'用户应该能通过邮件里的链接重置密码'")
    .then(delegates_to("product-manager"))
)

case_python_tests = (
    _router_case("sibling-python-not-java-tests",
                 "为这个函数写单元测试：def calc_total(items): return sum(i.price for i in items)")
    .then(delegates_to("python-test-engineer"))
    .then(no_delegation_to("java-unit-test"))
)

case_ios = (
    _router_case("delegate-ios-feature",
                 "给我的 iOS 应用做一个带深色模式开关的 SwiftUI 设置页面")
    .then(delegates_to("ios-developer"))
)

case_trivial = (
    _router_case("no-route-trivial",
                 "快速问一下，不涉及代码：一句话解释什么是「幂等」？")
    .then(no_delegation())
)

cases = [case_review, case_product, case_python_tests, case_ios, case_trivial]
