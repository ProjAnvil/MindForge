"""Real-model L1 discovery metrics for every MindForge skill.

The main agent sees only name + description from the full catalog plus three
hard distractors. It returns an ordered select_skill list. The report gates
Hit@1, Recall@k, MRR@10 and the False-Trigger Rate on the held-out test split.

Requires SMELT_API_KEY; skipped in deterministic CI.
"""

from __future__ import annotations

import importlib

import pytest

from conftest import requires_llm
from discovery import build_catalog

pytestmark = [pytest.mark.llm, requires_llm]

QUERY_MODULES = {
    "en": "discovery.en_queries",
    "zh-cn": "discovery.zh_cn_queries",
}


@pytest.mark.parametrize("lang", ("en", "zh-cn"))
def test_full_library_discovery_metrics(lang, agent_llm):
    from smelt import discovery_suite

    catalog = build_catalog(lang)
    queries = importlib.import_module(QUERY_MODULES[lang]).queries
    report = discovery_suite(
        catalog=catalog,
        queries=queries,
        llm=agent_llm,
        repeat=2,
    ).run()

    metrics = report.metrics()
    print(f"\n{lang} discovery metrics: {metrics}")
    print(report.to_markdown())

    report.assert_metrics(
        hit_at_1=0.80,
        recall_at_k=0.90,
        false_trigger_rate=0.25,
        low_overlap_hit_at_1=0.80,
    )
    assert metrics["mrr_at_10"] >= 0.80
    assert metrics["recall_at_k"] >= metrics["hit_at_1"]
    assert metrics["queries"] == sum(1 for q in queries if q.split == "test")
