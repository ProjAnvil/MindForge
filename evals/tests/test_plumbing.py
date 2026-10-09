"""Harness self-tests (deterministic, no LLM API).

These cases pin the evaluation plumbing itself: ScriptedLLM replay through
SmeltAgent with a real SKILL.md as system prompt, and fixed_agent for pure
assertion behavior. They must pass in CI even without model credentials.
"""

from __future__ import annotations

import pytest
from smelt import (
    LLMResponse,
    ScriptedLLM,
    fixed_agent,
    new_case,
    no_tool_call,
    output_contains,
    smelt_agent,
    text,
    text_similar,
    tool_budget,
    tool_call,
    turns_used,
    wall_time,
)

from conftest import SKILL_ROOTS

GIT_GURU = SKILL_ROOTS["en"] / "git-guru"


def test_scripted_llm_replay_through_real_skill(run_command_tool):
    """ScriptedLLM drives the tool loop against the real git-guru SKILL.md."""
    llm = ScriptedLLM(
        [
            LLMResponse.call("run_command", {"cmd": "git status"}),
            LLMResponse.say("Working tree inspected; ready to amend."),
        ]
    )
    result = (
        new_case("git-guru-plumbing")
        .given(smelt_agent(GIT_GURU, llm=llm, tools=[run_command_tool]))
        .when(text("check the repo state before we rewrite history"))
        .then(tool_call("run_command", args={"cmd": "git status"}))
        .then(output_contains("amend"))
        .run()
    )
    result.assert_passed()


def test_fixed_agent_negative_assertion():
    """fixed_agent replays a trace with no tool calls; no_tool_call must pass."""
    result = (
        new_case("no-git-on-chat")
        .given(fixed_agent("Sure — here is how interactive rebase works."))
        .when(text("explain rebase, do not touch my repo"))
        .then(no_tool_call("run_command"))
        .then(text_similar("explanation of interactive rebase", threshold=0.3))
        .run()
    )
    result.assert_passed()


def test_missing_agent_is_a_failure_not_a_crash():
    """Guardrail: a case without an agent fails cleanly with 'missing agent'."""
    result = new_case("no-agent").when(text("hi")).then(output_contains("x")).run()
    with pytest.raises(AssertionError):
        result.assert_passed()


def test_repeat_sampling_runs_n_times():
    """repeat(n): deterministic agents replay cleanly; pass^k reliability is 1."""
    result = (
        new_case("repeat-sampling")
        .given(fixed_agent("stable answer"))
        .when(text("say something"))
        .then(output_contains("stable"))
        .repeat(3)
        .run()
    )
    assert result.runs == 3
    assert result.pass_hat == 1.0
    result.assert_passed()


def test_compare_flags_regression_and_clean_upgrade():
    """compare(): score drops beyond the band and pass^k drops are regressions."""
    from smelt import compare

    def payload(skill: str, case: str, score: float, pass_hat: bool) -> dict:
        return {
            "skill": {"name": skill},
            "overall": {"score": score * 100},
            "behavior": [{"case": case, "score": score, "pass_hat": pass_hat}],
        }

    baseline = payload("git-guru@v1", "amend", 0.9, True)

    # same scores -> no regression
    compare(baseline, payload("git-guru@v2", "amend", 0.9, True)).assert_no_regression()

    # large score drop -> regression beyond the significance band
    dropped = compare(baseline, payload("git-guru@v2", "amend", 0.3, True))
    assert dropped.has_regression
    with pytest.raises(AssertionError):
        dropped.assert_no_regression()

    # pass^k True -> False within the noise band -> reliability regression
    flaky = compare(baseline, payload("git-guru@v2", "amend", 0.88, False))
    assert flaky.has_regression


def test_budget_assertions_pass_and_fail():
    """v0.3.0 budget assertions: turns / tool calls / wall time."""
    result = (
        new_case("budget-ok")
        .given(fixed_agent("done in one turn, no tools"))
        .when(text("q"))
        .then(turns_used(max=2))
        .then(tool_budget("run_command", max=0))
        .then(wall_time(max_seconds=30))
        .run()
    )
    result.assert_passed()

    over_budget = (
        new_case("budget-blown")
        .given(fixed_agent("done"))
        .when(text("q"))
        .then(turns_used(max=0))  # any answer needs at least one turn
        .run()
    )
    with pytest.raises(AssertionError):
        over_budget.assert_passed()


def test_reference_assertions_replay(tmp_path):
    """v0.4.0 reference assertions: read / restraint, tool-name-agnostic."""
    from smelt import no_reference_read, reference_read

    trace = [{"name": "read_file", "arguments": {"path": "references/endpoints.md"}}]
    result = (
        new_case("ref-read")
        .given(fixed_agent("done", tool_calls=trace))
        .when(text("q"))
        .then(reference_read("references/endpoints.md"))
        .then(no_reference_read("references/performance.md"))
        .run()
    )
    result.assert_passed()

    missed = (
        new_case("ref-missed")
        .given(fixed_agent("done"))
        .when(text("q"))
        .then(reference_read("references/endpoints.md"))
        .run()
    )
    with pytest.raises(AssertionError):
        missed.assert_passed()


def test_mock_tool_content_substitution():
    """v0.4.0 mock_tool: canned content per argument, base tool otherwise."""
    from smelt import mock_tool, tool

    @tool
    def read_file(path: str) -> str:
        """Read a file."""
        return f"real:{path}"

    mocked = mock_tool(read_file, {"references/x.md": "corrupted!"})
    assert mocked.invoke({"path": "references/x.md"}) == "corrupted!"
    assert mocked.invoke({"path": "other.md"}) == "real:other.md"
