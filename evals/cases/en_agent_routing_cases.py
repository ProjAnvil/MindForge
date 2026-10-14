"""Doctor-ready routing cases for the English agent roster.

Usage:
    uv run smelt run cases/en_agent_routing_cases.py -v
    uv run smelt doctor --agent ../agents/en/code-reviewer.md cases/en_agent_routing_cases.py

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

AGENTS_DIR = Path(__file__).resolve().parent.parent.parent / "agents" / "en"


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
        new_case(f"route-en-{name}")
        .given(router_agent(AGENTS_DIR, llm=_llm()))
        .when(text(trigger))
    )


case_review = (
    _router_case("delegate-code-review",
                 "Review this code for architecture problems and code smells before I commit it: "
                 "class OrderService { void saveOrder(Order o) { validate(o); repo.save(o); "
                 "mailer.send(o); audit.log(o); cache.put(o); } }")
    .then(delegates_to("code-reviewer"))
)

case_product = (
    _router_case("delegate-product-planning",
                 "Turn this rough idea into user stories and a feature breakdown: "
                 "'users should be able to reset their password via an emailed link'")
    .then(delegates_to("product-manager"))
)

case_python_tests = (
    _router_case("sibling-python-not-java-tests",
                 "Write unit tests for this function: "
                 "def calc_total(items): return sum(i.price for i in items)")
    .then(delegates_to("python-test-engineer"))
    .then(no_delegation_to("java-unit-test"))
)

case_ios = (
    _router_case("delegate-ios-feature",
                 "Build a SwiftUI settings screen with a dark-mode toggle for my iOS app")
    .then(delegates_to("ios-developer"))
)

case_trivial = (
    _router_case("no-route-trivial",
                 "Quick question, no code involved: what does 'idempotent' mean, in one sentence?")
    .then(no_delegation())
)

cases = [case_review, case_product, case_python_tests, case_ios, case_trivial]
