"""Deterministic contracts for the Chinese dictionary cost benchmark."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "zh_dict_cost.py"


@pytest.fixture
def study():
    spec = importlib.util.spec_from_file_location("zh_dict_cost", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_history_sizes_do_not_change_the_reply_fixture(study):
    histories = [study.make_history(size) for size in [200, 2000, 16000]]
    assert [len(history) for history in histories] == [200, 2000, 16000]
    case = study.CASES[0]
    for history in histories:
        messages = study.draft_messages(history, case["draft"])
        assert messages[-1]["content"].endswith(case["draft"])
        assert history in messages[1]["content"]
    assert len(case["draft"]) < 500
    with pytest.raises(ValueError):
        study.make_history(0)


def test_review_replaces_the_draft_stage_but_retains_context(study):
    history = study.make_history(500)
    draft = study.CASES[0]["draft"]
    initial = study.draft_messages(history, draft, "dictionary guidance")
    review = study.review_messages(history, draft, "dictionary guidance", "review annotations")
    assert initial[0] != review[0]
    assert initial[1:] == review[1:-2]
    assert review[-2] == {"role": "assistant", "content": draft}
    assert review[-1]["content"].endswith("review annotations")


def test_usage_delta_includes_continuation_input_not_just_rewritten_output(study):
    baseline = {"input_tokens": 1000, "output_tokens": 80, "cached_tokens": 900, "ms": 100.0}
    dictionary = [
        {"input_tokens": 1400, "output_tokens": 80, "cached_tokens": 900, "ms": 120.0},
        {"input_tokens": 1800, "output_tokens": 70, "cached_tokens": 1000, "ms": 140.0},
    ]
    result = study.paired_cost(baseline, dictionary, hook_ms=25.0)
    assert result["baseline_input_tokens"] == 1000
    assert result["dictionary_input_tokens"] == 3200
    assert result["delta_input_tokens"] == 2200
    assert result["delta_output_tokens"] == 70
    assert result["delta_total_tokens"] == 2270
    assert result["delta_ms"] == 185.0
    assert result["dictionary_cached_tokens"] == 1900


def test_missing_cache_data_is_not_reported_as_zero(study):
    call = {"input_tokens": 10, "output_tokens": 2, "cached_tokens": None, "ms": 10.0}
    result = study.paired_cost(call, [call], hook_ms=2.0)
    assert result["dictionary_cached_tokens"] is None
    assert result["delta_ms"] == 2.0


def test_trial_summary_preserves_unknown_cache_data(study):
    trials = [
        {"dictionary_cached_tokens": 20, "delta_ms": -5.0, "numeric_facts_preserved": True},
        {"dictionary_cached_tokens": None, "delta_ms": 15.0, "numeric_facts_preserved": True},
    ]
    summary = study.summarize_trials(trials)
    assert summary["dictionary_cached_tokens"] is None
    assert summary["delta_ms"] == 5.0
    assert summary["delta_ms_range"] == [-5.0, 15.0]


def test_hook_path_exercises_actual_annotation_feedback(study):
    matched = study.measure_hooks(study.CASES[0], rounds=2)
    clean = study.measure_hooks(study.CASES[1], rounds=2)
    assert matched["blocked"] is True
    assert matched["annotation_count"] == 3
    assert matched["feedback"]
    assert matched["inject_ms"]["mean"] > 0
    assert matched["stop_ms"]["mean"] > 0
    assert clean["blocked"] is False
    assert clean["annotation_count"] == 0
    assert clean["feedback"] == ""
    assert matched["token_backend"].startswith(("estimate/", "tiktoken/"))


def test_hook_errors_are_not_reported_as_zero_cost(study):
    with study.HookRuntime() as runtime:
        with pytest.raises(RuntimeError):
            runtime.run("nonexistent-hook.py", {})
        runtime.env["ZH_GUARD_OFF"] = "1"
        with pytest.raises(RuntimeError):
            runtime.inject()


def test_paired_pipeline_uses_real_stop_decisions(study):
    case = study.CASES[0]
    responses = iter([
        {"text": case["draft"], "model": "fixture", "input_tokens": 100, "output_tokens": 20,
         "cached_tokens": None, "ms": 10.0},
        {"text": case["draft"], "model": "fixture", "input_tokens": 150, "output_tokens": 20,
         "cached_tokens": None, "ms": 11.0},
        {"text": case["reference"], "model": "fixture", "input_tokens": 200, "output_tokens": 18,
         "cached_tokens": None, "ms": 12.0},
    ])

    class FixedResponses:
        def complete(self, _messages):
            return next(responses)

    trial = study.run_pair(FixedResponses(), study.make_history(200), case, dictionary_first=False)
    assert trial["delta_input_tokens"] == 250
    assert trial["delta_output_tokens"] == 18
    assert trial["rewrite_calls"] == 1
    assert trial["remaining_terms"] == []
    assert trial["numeric_facts_preserved"] is True


def test_local_report_labels_estimates_and_never_invents_model_latency(study):
    report = study.run_study(context_chars=[100, 200, 300], hook_rounds=1)
    assert report["live"] is False
    assert len(report["scenarios"]) == 6
    assert report["methodology"]["draft_length_is_fixed"] is True
    for scenario in report["scenarios"]:
        assert scenario["live_trials"] == []
        assert scenario["summary"] is None
        assert scenario["estimated_content_tokens"]["baseline_input"] > 0
    output = study.render_report(report)
    assert "not measured" in output
    assert "estimated" in output.lower()


def test_fixture_preservation_is_checked_independently_of_word_removal(study):
    source = "线程睡20ms，再处理7个请求，任务ID为42。"
    good = "线程休眠20ms，然后处理7个请求，任务ID为42。"
    bad = "线程休眠20ms，然后处理8个请求，任务ID为42。"
    assert study.preserves_numeric_facts(source, good)
    assert not study.preserves_numeric_facts(source, bad)


def test_native_tool_selection_usage_and_wire_message_are_preserved(study):
    response = {
        "model": "fixture-model",
        "usage": {"prompt_tokens": 500, "completion_tokens": 25, "prompt_cache_hit_tokens": 400},
        "choices": [{
            "finish_reason": "tool_calls",
            "message": {"role": "assistant", "content": None, "tool_calls": [{
                "id": "call-1", "type": "function",
                "function": {"name": "mindforge_lookup_term", "arguments": '{"query":"term"}'},
            }]},
        }],
    }
    result = study.completion_result(response, 12.5)
    assert result["input_tokens"] == 500
    assert result["output_tokens"] == 25
    assert result["cached_tokens"] == 400
    assert result["text"] == ""
    assert result["tool_calls"][0]["id"] == "call-1"
    assert result["assistant_message"]["tool_calls"] == result["tool_calls"]
    assert result["ms"] == 12.5


def test_truncated_tool_response_is_not_accepted(study):
    with pytest.raises(RuntimeError):
        study.completion_result({
            "model": "fixture",
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
            "choices": [{"finish_reason": "length", "message": {"content": None}}],
        }, 1.0)
