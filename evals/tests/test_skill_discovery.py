"""Deterministic checks for Smelt 0.7.0 discovery primitives.

No API key needed. The tests cover catalog construction, query labels,
assertions, and metric aggregation with a scripted LLM. The real-model
suite lives in test_skill_discovery_llm.py.
"""

from __future__ import annotations

import importlib

import pytest
from smelt import (
    LLMResponse,
    ScriptedLLM,
    discovery_query,
    discovery_suite,
    fixed_agent,
    new_case,
    no_skill_selected,
    skill_not_selected,
    skill_rank,
    skill_recall,
    skill_selected,
    text,
)

from discovery import DISTRACTOR_ROOTS, K, SKILL_ROOTS, build_catalog

LANGS = ("en", "zh-cn")
QUERY_MODULES = {
    "en": "discovery.en_queries",
    "zh-cn": "discovery.zh_cn_queries",
}


@pytest.mark.parametrize("lang", LANGS)
def test_catalog_covers_every_skill_and_distractor(lang):
    catalog = build_catalog(lang)
    disk = {p.name for p in SKILL_ROOTS[lang].iterdir() if (p / "SKILL.md").is_file()}
    distractors = {p.name for p in DISTRACTOR_ROOTS[lang].iterdir() if (p / "SKILL.md").is_file()}

    assert set(catalog.names()) == disk | distractors
    assert tuple(catalog.names()) == tuple(sorted(catalog.names()))
    assert catalog.k == K
    assert len(catalog.candidates) == len(disk) + len(distractors)


@pytest.mark.parametrize("lang", LANGS)
def test_catalog_render_has_no_skill_body(lang):
    catalog = build_catalog(lang)
    rendered = catalog.render()
    for candidate in catalog.candidates:
        skill_file = candidate.path if candidate.path.is_file() else candidate.path / "SKILL.md"
        body = skill_file.read_text(encoding="utf-8")
        assert "### " + candidate.name in rendered
        assert " ".join(candidate.description.split()) in rendered
        for line in body.splitlines():
            if line.startswith("## "):
                assert line not in rendered


@pytest.mark.parametrize("lang", LANGS)
def test_query_set_is_labelled_and_balanced(lang):
    catalog = build_catalog(lang)
    queries = importlib.import_module(QUERY_MODULES[lang]).queries
    gold = {name for query in queries for name in query.gold}

    assert all(query.name for query in queries)
    assert len({query.name for query in queries}) == len(queries)
    assert {query.split for query in queries} == {"train", "test"}
    assert {query.kind for query in queries} >= {"positive", "paraphrase", "near-miss", "none"}
    assert gold == {p.name for p in SKILL_ROOTS[lang].iterdir() if (p / "SKILL.md").is_file()}
    for query in queries:
        query.validate_gold(catalog)
        if query.kind in ("near-miss", "none"):
            assert query.gold == ()


def test_discovery_assertions_read_ranked_tool_calls():
    ranked = ["frontend-vue", "frontend-svelte", "frontend-react"]
    case = (
        new_case("discovery-assertion-smoke")
        .given(fixed_agent("done", tool_calls=[
            {"name": "select_skill", "arguments": {"skills": ranked}},
        ]))
        .when(text("Build a SvelteKit form"))
        .then(skill_selected("frontend-svelte", k=2))
        .then(skill_rank("frontend-svelte", max_rank=2))
        .then(skill_recall(["frontend-svelte", "frontend-vue"], k=3))
        .then(skill_not_selected("testing"))
    )
    case.report(quiet=True).assert_passed()

    empty = (
        new_case("discovery-empty-selection")
        .given(fixed_agent("done", tool_calls=[
            {"name": "select_skill", "arguments": {"skills": []}},
        ]))
        .when(text("What is the weather?"))
        .then(no_skill_selected())
    )
    empty.report(quiet=True).assert_passed()


def test_discovery_suite_metrics_and_gates():
    catalog = build_catalog("en")
    positive = discovery_query(
        "A background worker outlives its request because cancellation is ignored.",
        gold=["go-development"], kind="positive", split="test", name="metric-hit",
    )
    miss = discovery_query(
        "What is the weather in Shanghai tomorrow?",
        kind="none", split="test", name="metric-none",
    )
    llm = ScriptedLLM([
        LLMResponse.call("select_skill", {"skills": ["go-development"]}),
        LLMResponse.say("done"),
        LLMResponse.call("select_skill", {"skills": []}),
        LLMResponse.say("done"),
    ])

    report = discovery_suite(catalog=catalog, queries=[positive, miss], llm=llm, repeat=1).run()

    assert report.hit_at_1 == 1.0
    assert report.recall_at_k == 1.0
    assert report.mrr_at_10 == 1.0
    assert report.false_trigger_rate == 0.0
    assert report.to_dict()["k"] == K
    assert report.assert_metrics(hit_at_1=1.0, recall_at_k=1.0, false_trigger_rate=0.0) is report
    with pytest.raises(AssertionError):
        report.assert_metrics(hit_at_1=1.0, recall_at_k=1.0, false_trigger_rate=-0.01)
