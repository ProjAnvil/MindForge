"""Compare concise guidance with real context lookup before generation."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "zh_pregen_cost.py"


@pytest.fixture
def study():
    spec = importlib.util.spec_from_file_location("zh_pregen_cost", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_two_arms_share_question_history_and_simple_rules(study):
    history = study.base.make_history(2000)
    simple = study.messages(history, use_lookup=False)
    lookup = study.messages(history, use_lookup=True)
    assert simple[1:] == lookup[1:]
    assert simple[-1]["content"].endswith(study.QUESTION)
    assert study.SIMPLE_RULES in simple[0]["content"]
    assert study.SIMPLE_RULES in lookup[0]["content"]
    assert "mindforge_lookup_term" not in simple[0]["content"]
    assert "mindforge_lookup_term" in lookup[0]["content"]


def test_context_is_obtained_from_actual_mcp_tool(study):
    with study.LookupRuntime() as runtime:
        assert runtime.tool["function"]["name"] == "mindforge_lookup_term"
        result, elapsed = runtime.lookup({
            "id": "fixture-lookup", "type": "function",
            "function": {"name": "mindforge_lookup_term", "arguments": '{"query":"纯尾即就绪"}'},
        })
    assert result["role"] == "tool"
    assert result["tool_call_id"] == "fixture-lookup"
    assert "等这个任务完成之后，就继续下一项" in result["content"]
    assert elapsed > 0


def test_pipeline_has_no_post_generation_review_and_counts_both_requests(study):
    lookup_call = {
        "id": "fixture-lookup", "type": "function",
        "function": {"name": "mindforge_lookup_term", "arguments": json.dumps({"query": "纯尾即就绪"})},
    }
    responses = iter([
        {"text": "任务42完成后继续下一项。", "model": "fixture", "input_tokens": 100,
         "output_tokens": 10, "cached_tokens": None, "ms": 10.0, "tool_calls": []},
        {"text": "", "model": "fixture", "input_tokens": 150, "output_tokens": 20,
         "cached_tokens": None, "ms": 11.0, "tool_calls": [lookup_call],
         "assistant_message": {"role": "assistant", "content": None, "tool_calls": [lookup_call]}},
        {"text": "任务42完成后继续下一项。", "model": "fixture", "input_tokens": 250,
         "output_tokens": 12, "cached_tokens": None, "ms": 12.0, "tool_calls": []},
    ])

    class FixedResponses:
        def complete(self, _messages, **_options):
            return next(responses)

    result = study.run_pair(FixedResponses(), study.base.make_history(200), lookup_first=False)
    assert result["simple_input_tokens"] == 100
    assert result["lookup_input_tokens"] == 400
    assert result["extra_input_tokens"] == 300
    assert result["extra_output_tokens"] == 22
    assert result["model_requests"] == {"simple": 1, "lookup": 2}
    assert result["post_generation_model_requests"] == 0
    assert result["lookup_calls"] == 1
    assert result["facts_preserved"] is True
    assert len(result["request_usage"]["lookup"]) == 2


def test_pretending_to_get_context_without_a_call_is_rejected(study):
    class NoLookup:
        def complete(self, _messages, **_options):
            return {"text": "任务42已安排。", "tool_calls": []}

    with pytest.raises(RuntimeError, match="lookup"):
        study.run_pair(NoLookup(), study.base.make_history(200), lookup_first=True)
