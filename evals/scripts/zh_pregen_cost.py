"""Live A/B study: concise rules versus context lookup before final generation."""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_SPEC = importlib.util.spec_from_file_location(
    "zh_generation_base", Path(__file__).with_name("zh_dict_cost.py"),
)
base = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(base)
SIMPLE_RULES = (base.HOOKS / "style-rules-zh.md").read_text(encoding="utf-8").strip()
LOOKUP_INSTRUCTION = (
    "\n生成最终回答前，先调用 mindforge_lookup_term，"
    "query 必须是“纯尾即就绪”，获取它在当前词典中的含义。"
    "拿到工具结果后结合问题中的事实回答；调用工具前不要写回答草稿。"
)
QUESTION = (
    "调度面板显示：任务42尚未完成，状态标注为“纯尾即就绪”；"
    "下一项已经安排，但尚未执行。请用两句自然中文向用户说明后续顺序，"
    "保留42，不复述生硬状态串，不要声称任务已完成，不超过100字。"
)
TOOL_NAME = "mindforge_lookup_term"


def messages(history: str, use_lookup: bool) -> list[dict]:
    return [
        {"role": "system", "content": SIMPLE_RULES + (LOOKUP_INSTRUCTION if use_lookup else "")},
        {"role": "user", "content": "合成背景材料（不是本轮问题）：\n" + history + "\n\n本轮问题：\n" + QUESTION},
    ]


class LookupRuntime:
    def __enter__(self):
        self.runtime = base.HookRuntime()
        self.runtime.__enter__()
        try:
            process, _elapsed = self.runtime.run("term-dict-server.py", {
                "jsonrpc": "2.0", "id": 1, "method": "tools/list",
            })
            tools = json.loads(process.stdout)["result"]["tools"]
            declaration = next(tool for tool in tools if tool["name"] == TOOL_NAME)
            self.tool = {"type": "function", "function": {
                "name": declaration["name"], "description": declaration["description"],
                "parameters": declaration["inputSchema"],
            }}
            return self
        except Exception:
            self.runtime.__exit__(None, None, None)
            raise

    def __exit__(self, *args):
        self.runtime.__exit__(*args)

    def lookup(self, call: dict) -> tuple[dict, float]:
        if call["function"]["name"] != TOOL_NAME:
            raise RuntimeError("unexpected tool selected in pre-generation experiment")
        arguments = json.loads(call["function"]["arguments"])
        process, elapsed = self.runtime.run("term-dict-server.py", {
            "jsonrpc": "2.0", "id": 2, "method": "tools/call",
            "params": {"name": TOOL_NAME, "arguments": arguments},
        })
        result = json.loads(process.stdout)["result"]
        if result.get("isError") is not False:
            raise RuntimeError("actual MCP lookup failed")
        text = "\n".join(item["text"] for item in result["content"] if item["type"] == "text")
        if "纯尾即就绪" not in text or "等这个任务完成之后，就继续下一项" not in text:
            raise RuntimeError("lookup did not retrieve the required meaning")
        return {"role": "tool", "tool_call_id": call["id"], "content": text}, elapsed


def usage_record(call: dict) -> dict:
    return {key: call.get(key) for key in [
        "model", "input_tokens", "output_tokens", "cached_tokens", "ms", "finish_reason",
    ]}


def run_pair(model, history: str, lookup_first: bool) -> dict:
    def simple_arm():
        call = model.complete(messages(history, use_lookup=False))
        if call.get("tool_calls"):
            raise RuntimeError("simple-rule arm unexpectedly requested a tool")
        return call

    def lookup_arm():
        with LookupRuntime() as runtime:
            initial_messages = messages(history, use_lookup=True)
            selection = model.complete(
                initial_messages, tools=[runtime.tool],
                tool_choice={"type": "function", "function": {"name": TOOL_NAME}},
            )
            if len(selection.get("tool_calls", [])) != 1 or selection.get("text"):
                raise RuntimeError("lookup arm must retrieve context once before generating any draft")
            call = selection["tool_calls"][0]
            tool_result, tool_ms = runtime.lookup(call)
            final = model.complete(
                initial_messages + [selection["assistant_message"], tool_result],
                tools=[runtime.tool], tool_choice="none",
            )
            if final.get("tool_calls") or not final.get("text"):
                raise RuntimeError("lookup arm did not finish with a text answer")
            return selection, final, tool_result, tool_ms, call

    if lookup_first:
        selection, final, result, tool_ms, tool_call = lookup_arm()
        simple = simple_arm()
    else:
        simple = simple_arm()
        selection, final, result, tool_ms, tool_call = lookup_arm()
    pair = base.paired_cost(simple, [selection, final], tool_ms)
    simple_total = pair["baseline_input_tokens"] + pair["baseline_output_tokens"]
    lookup_total = pair["dictionary_input_tokens"] + pair["dictionary_output_tokens"]
    facts = "42" in simple["text"] and "42" in final["text"]
    return {
        "simple_input_tokens": pair["baseline_input_tokens"],
        "simple_output_tokens": pair["baseline_output_tokens"],
        "simple_cached_tokens": pair["baseline_cached_tokens"],
        "lookup_input_tokens": pair["dictionary_input_tokens"],
        "lookup_output_tokens": pair["dictionary_output_tokens"],
        "lookup_cached_tokens": pair["dictionary_cached_tokens"],
        "extra_input_tokens": pair["delta_input_tokens"],
        "extra_output_tokens": pair["delta_output_tokens"],
        "extra_total_tokens": lookup_total - simple_total,
        "simple_ms": pair["baseline_ms"], "lookup_ms": pair["dictionary_ms"],
        "delta_ms": pair["delta_ms"], "lookup_local_ms": tool_ms,
        "total_token_ratio": lookup_total / simple_total,
        "model_requests": {"simple": 1, "lookup": 2},
        "post_generation_model_requests": 0, "lookup_calls": 1,
        "lookup_first": lookup_first, "facts_preserved": facts, "numeric_facts_preserved": facts,
        "simple_text": simple["text"], "lookup_text": final["text"],
        "tool_query": json.loads(tool_call["function"]["arguments"]), "tool_result": result["content"],
        "request_usage": {"simple": usage_record(simple), "lookup": [usage_record(selection), usage_record(final)]},
    }


def run_study(model, context_chars=None, rounds=3) -> dict:
    sizes = base.DEFAULT_CONTEXT_CHARS if context_chars is None else context_chars
    if len(sizes) != 3 or any(size <= 0 for size in sizes) or rounds <= 0:
        raise ValueError("provide three positive context sizes and positive rounds")
    scenarios = [{"context": label, "history_chars": size, "trials": []}
                 for label, size in zip(["short", "medium", "long"], sizes)]
    for round_index in range(rounds):
        for index in range(len(scenarios)):
            scenario = scenarios[(index + round_index) % len(scenarios)]
            trial = run_pair(
                model, base.make_history(scenario["history_chars"]),
                lookup_first=(round_index + index) % 2 == 0,
            )
            scenario["trials"].append(trial)
            print("Completed pre-generation pair: %s round %d" % (
                scenario["context"], round_index + 1,
            ), file=sys.stderr, flush=True)
    for scenario in scenarios:
        summary = base.summarize_trials(scenario["trials"])
        simple_total = summary["simple_input_tokens"] + summary["simple_output_tokens"]
        lookup_total = summary["lookup_input_tokens"] + summary["lookup_output_tokens"]
        summary["total_token_ratio"] = lookup_total / simple_total
        scenario["summary"] = summary
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "requested_model": model.name, "provider_host": model.host, "rounds": rounds,
        "methodology": {
            "arm_a": "concise writing guidance, no tool schema, one final-generation request",
            "arm_b": "same guidance plus lookup instruction and actual MCP schema, one native lookup then final generation",
            "tool_choice": "first request constrained to lookup; measures fulfilled requirement, not voluntary compliance rate",
            "question": QUESTION, "simple_rules": SIMPLE_RULES, "lookup_instruction": LOOKUP_INSTRUCTION,
            "answer_budget": "two sentences, at most 100 Chinese characters, same in both arms",
            "history": "same synthetic history in both arms; sizes are Unicode characters",
            "tokens": "actual provider input/output usage across all requests, including tool serialization",
            "lookup": "actual mindforge_lookup_term, not draft preflight and not a fabricated result",
            "tool_execution_time": "local MCP subprocess including interpreter startup; production persistent MCP may be faster",
            "post_generation_review": "none: no Stop, SubagentStop, draft regeneration or semantic judge",
            "pricing": "cache counters are recorded; processed tokens are not a monetary bill",
            "sample_scope": "retained paired trials only; setup/probe calls are excluded",
        },
        "scenarios": scenarios,
    }


def render_report(report: dict) -> str:
    lines = [
        "# Pre-generation Chinese context lookup: token comparison", "",
        "A: concise writing rules, direct answer. B: the same rules, real context lookup, then answer.",
        "No Stop hook, full-draft preflight or post-generation polishing is included.",
        "One readonly MCP tool is exposed. Native tool choice ensures the required lookup occurs;",
        "this experiment does not measure whether an unconstrained agent obeys a tool-use prompt.", "",
        "Requested model: `%s`; provider: `%s`; %d paired rounds per context." % (
            report["requested_model"], report["provider_host"], report["rounds"],
        ), "",
        "| Context | History chars | A input/output | B input/output | Extra tokens | B/A | A ms | B ms |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for scenario in report["scenarios"]:
        summary = scenario["summary"]
        lines.append("| %s | %d | %.0f / %.0f | %.0f / %.0f | %.0f | %.2fx | %.1f | %.1f |" % (
            scenario["context"], scenario["history_chars"],
            summary["simple_input_tokens"], summary["simple_output_tokens"],
            summary["lookup_input_tokens"], summary["lookup_output_tokens"],
            summary["extra_total_tokens"], summary["total_token_ratio"],
            summary["simple_ms"], summary["lookup_ms"],
        ))
    lines += [
        "", "Input includes cached tokens. API token counts are not monetary costs.",
        "Table values are paired-trial means, rounded for display; ratios use the mean totals.",
        "B includes both model requests, schema overhead, tool-call arguments and actual lookup results.",
        "The local lookup measurement includes MCP process startup; the measured token counts are unaffected.",
        "Only synthetic background is submitted. Samples are small and latency depends on cache/network conditions.", "",
        "## Sample answers", "",
    ]
    for scenario in report["scenarios"]:
        trial = scenario["trials"][-1]
        lines += [
            "### " + scenario["context"],
            "A: " + trial["simple_text"], "",
            "B: " + trial["lookup_text"], "",
            "Actual lookup result: " + trial["tool_result"], "",
            "Task ID preserved in every paired trial: %s." % scenario["summary"]["numeric_facts_preserved"], "",
        ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Explicitly enable real model requests")
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--context-chars", type=int, nargs=3, default=base.DEFAULT_CONTEXT_CHARS)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if not args.live:
        parser.error("this study requires --live; use deterministic tests for offline validation")
    model = base.LiveModel()
    try:
        report = run_study(model, args.context_chars, args.rounds)
    finally:
        model.close()
    markdown = render_report(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        args.output.with_suffix(".md").write_text(markdown + "\n", encoding="utf-8")
    print(markdown)


if __name__ == "__main__":
    main()
