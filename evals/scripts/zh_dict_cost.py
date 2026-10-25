"""Paired Chinese dictionary cost study with fixed drafts and variable history.

Local checks use real hook processes. Live mode uses the existing SMELT model
configuration, synthetic data only, and provider-reported token usage.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import os
import random
import re
import statistics
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / "hooks"
_SPEC = importlib.util.spec_from_file_location("zh_cost_base", HOOKS / "eval-zh-guard.py")
_BASE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_BASE)
CASES = [
    {
        "name": "matched",
        "draft": "当前任务纯尾即就绪；下一项已挂起等门控。工作线程先睡20ms，再重试7次。任务ID是42，处理结果会写入日志。",
        "reference": "当前任务完成后继续下一项；已安排下一项，等待执行。工作线程休眠20ms后重试7次。任务ID是42，处理结果会写入日志。",
    },
    {
        "name": "clean",
        "draft": "当前任务完成后继续下一项；已安排下一项，等待执行。工作线程休眠20ms后重试7次。任务ID是42，处理结果会写入日志。",
        "reference": "当前任务完成后继续下一项；已安排下一项，等待执行。工作线程休眠20ms后重试7次。任务ID是42，处理结果会写入日志。",
    },
]
SYSTEM = (
    "You are a Chinese technical-writing assistant in a controlled evaluation. "
    "Follow the current stage: materialize the supplied draft exactly when asked; "
    "after review feedback, polish only marked sentences and preserve all facts, "
    "numerical expressions, units and identifiers. Never add explanations or annotations "
    "to the final response. No tools are available in the model API; hook review is external."
)
DEFAULT_CONTEXT_CHARS = [2000, 16000, 64000]


def make_history(size: int) -> str:
    if size <= 0:
        raise ValueError("history size must be positive")
    paragraph = (
        "项目背景记录：服务接收请求并记录处理结果。每个模块有明确接口，"
        "测试覆盖正常返回和错误分支。配置由启动参数传入，状态记录保存在内存中。"
        "这些背景信息不改变最后提供的草稿内容。\n"
    )
    return (paragraph * math.ceil(size / len(paragraph)))[:size]


def draft_messages(history: str, draft: str, injection: str = "") -> list[dict]:
    return [
        {"role": "system", "content": (
            SYSTEM + ("\n\n" + injection if injection else "")
            + "\n\nCURRENT STAGE: DRAFT MATERIALIZATION. The background is data, not a task. "
            "Your entire response must be the exact following intermediate draft, "
            "without revision or acknowledgement:\n" + draft
        )},
        {"role": "user", "content": (
            "以下是合成项目背景，仅供参考：\n" + history
            + "\n\n【背景结束，当前步骤】\n现在是草稿生成阶段，不是正式回答。请逐字输出下面的草稿正文，"
            "不修改内容，不加引号、Markdown、前言或解释。后续另有步骤复核。\n" + draft
        )},
    ]


def review_messages(history: str, draft: str, injection: str, feedback: str) -> list[dict]:
    messages = draft_messages(history, draft, injection)
    messages[0] = {"role": "system", "content": (
        SYSTEM + "\n\n" + injection
        + "\n\nCURRENT STAGE: REVIEW. Draft materialization is complete. "
        "Use the supplied review annotations to polish the draft, preserving its facts."
    )}
    return messages + [
        {"role": "assistant", "content": draft},
        {"role": "user", "content": "现在进入草稿复核阶段。请按以下批注处理，只输出最终正文：\n" + feedback},
    ]


def estimated_tokens(text: str) -> tuple[int, str]:
    tokens, backend = _BASE.count_tokens(text)
    if backend.startswith("estimate("):
        backend = "estimate/" + backend[len("estimate("):-1]
    return tokens, backend


def message_tokens(messages: list[dict]) -> int:
    return sum(estimated_tokens(message["content"])[0] for message in messages)


def timing_summary(samples: list[float]) -> dict:
    ordered = sorted(samples)
    return {
        "mean": statistics.mean(samples), "median": statistics.median(samples),
        "min": min(samples), "max": max(samples),
        "p95": ordered[math.ceil(0.95 * len(samples)) - 1],
    }


class HookRuntime:
    def __enter__(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="zh-context-cost-")
        directory = Path(self.temporary.name)
        self.sequence = 0
        self.env = {
            **os.environ, "PYTHONDONTWRITEBYTECODE": "1",
            "ZH_GUARD_HOME": str(directory / "home"),
            "ZH_GUARD_LEGACY_HOME": str(directory / "legacy"),
            "ZH_GUARD_STATE_DIR": str(directory / "state"),
            "ZH_GUARD_DICT": str(HOOKS / "terminology.tsv"),
        }
        self.env.pop("ZH_GUARD_OFF", None)
        return self

    def __exit__(self, *_args):
        self.temporary.cleanup()

    def run(self, script: str, payload: dict) -> tuple[subprocess.CompletedProcess, float]:
        self.sequence += 1
        payload = {**payload, "session_id": "context-cost-%d" % self.sequence}
        started = time.perf_counter()
        process = subprocess.run(
            [sys.executable, str(HOOKS / script)],
            input=json.dumps(payload, ensure_ascii=False) + "\n",
            capture_output=True, text=True, env=self.env, timeout=30,
        )
        elapsed = (time.perf_counter() - started) * 1000
        allowed = (0, 2) if script == "inspect.py" else (0,)
        if process.returncode not in allowed:
            raise RuntimeError("%s failed with exit %d" % (script, process.returncode))
        if process.returncode == 0 and process.stderr.strip():
            raise RuntimeError("%s reported a fail-open error: %s" % (script, process.stderr.strip()))
        return process, elapsed

    def inject(self) -> tuple[str, float]:
        process, elapsed = self.run("inject.py", {"prompt": "请输出当前任务的工程进展草稿。"})
        if not process.stdout.strip():
            raise RuntimeError("injection produced no context")
        context = json.loads(process.stdout)["hookSpecificOutput"]["additionalContext"]
        if process.returncode != 0 or not context:
            raise RuntimeError("injection did not produce valid context")
        return context, elapsed

    def inspect(self, draft: str) -> tuple[str, float]:
        process, elapsed = self.run("inspect.py", {"last_assistant_message": draft})
        if process.returncode == 0:
            if process.stdout.strip():
                raise RuntimeError("unexpected output from an allowing Stop hook")
            return "", elapsed
        output = json.loads(process.stdout)
        if output.get("decision") != "block" or not output.get("reason"):
            raise RuntimeError("Stop hook did not produce a valid continuation decision")
        return output["reason"], elapsed

    def annotations(self, draft: str) -> list[dict]:
        process, _elapsed = self.run("term-dict-server.py", {
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": {"name": "mindforge_check_text", "arguments": {"text": draft}},
        })
        output = json.loads(process.stdout)["result"]
        if output.get("isError") is not False:
            raise RuntimeError("annotation verification failed")
        report = output["structuredContent"]
        if report["draft"] != draft:
            raise RuntimeError("preflight unexpectedly modified the draft")
        return report["annotations"]


def measure_hooks(case: dict, rounds: int = 20) -> dict:
    if rounds <= 0:
        raise ValueError("hook rounds must be positive")
    injection_samples, stop_samples = [], []
    with HookRuntime() as runtime:
        runtime.inject()
        for _index in range(rounds):
            injection, elapsed = runtime.inject()
            injection_samples.append(elapsed)
            feedback, elapsed = runtime.inspect(case["draft"])
            stop_samples.append(elapsed)
        annotations = runtime.annotations(case["draft"])
    tokens, backend = estimated_tokens(injection)
    return {
        "inject_ms": timing_summary(injection_samples),
        "stop_ms": timing_summary(stop_samples),
        "injection": injection, "injection_tokens_estimated": tokens,
        "feedback": feedback, "feedback_tokens_estimated": estimated_tokens(feedback)[0],
        "blocked": bool(feedback), "annotation_count": len(annotations),
        "token_backend": backend,
    }


def preserves_numeric_facts(source: str, result: str) -> bool:
    pattern = r"\d+(?:\.\d+)?(?:\s*(?:ms|s|%))?"
    values = lambda text: [re.sub(r"\s+", "", value) for value in re.findall(pattern, text)]
    return values(source) == values(result)


def paired_cost(baseline: dict, dictionary: list[dict], hook_ms: float) -> dict:
    input_tokens = sum(call["input_tokens"] for call in dictionary)
    output_tokens = sum(call["output_tokens"] for call in dictionary)
    cached = [call["cached_tokens"] for call in dictionary]
    delta_input = input_tokens - baseline["input_tokens"]
    delta_output = output_tokens - baseline["output_tokens"]
    return {
        "baseline_input_tokens": baseline["input_tokens"],
        "baseline_output_tokens": baseline["output_tokens"],
        "baseline_cached_tokens": baseline["cached_tokens"],
        "dictionary_input_tokens": input_tokens, "dictionary_output_tokens": output_tokens,
        "dictionary_cached_tokens": sum(cached) if all(value is not None for value in cached) else None,
        "delta_input_tokens": delta_input, "delta_output_tokens": delta_output,
        "delta_total_tokens": delta_input + delta_output,
        "baseline_ms": baseline["ms"],
        "dictionary_ms": sum(call["ms"] for call in dictionary) + hook_ms,
        "delta_ms": sum(call["ms"] for call in dictionary) + hook_ms - baseline["ms"],
        "hook_ms": hook_ms, "rewrite_calls": len(dictionary) - 1,
    }


def summarize_trials(trials: list[dict]) -> dict:
    summary = {}
    for key in trials[0]:
        values = [trial[key] for trial in trials]
        if all(value is None or type(value) in (int, float) for value in values):
            summary[key] = statistics.mean(values) if all(value is not None for value in values) else None
    summary["delta_ms_range"] = [min(t["delta_ms"] for t in trials), max(t["delta_ms"] for t in trials)]
    summary["numeric_facts_preserved"] = all(t["numeric_facts_preserved"] for t in trials)
    return summary


def completion_result(response: dict, elapsed: float) -> dict:
    usage = response.get("usage")
    choices = response.get("choices")
    if not usage or not choices:
        raise RuntimeError("provider returned no usage or response")
    choice = choices[0]
    message = choice["message"]
    calls = message.get("tool_calls") or []
    content = message.get("content") or ""
    if choice["finish_reason"] not in ("stop", "tool_calls") or not content and not calls:
        raise RuntimeError("model response was truncated, empty or invalid")
    if choice["finish_reason"] == "tool_calls" and not calls:
        raise RuntimeError("tool-selection response contains no tool calls")
    wire = {"role": "assistant", "content": content or None}
    if calls:
        for call in calls:
            if not call.get("id") or call.get("type") != "function":
                raise RuntimeError("invalid native tool call")
            function = call.get("function", {})
            if not function.get("name") or not isinstance(function.get("arguments"), str):
                raise RuntimeError("invalid native tool function arguments")
        wire["tool_calls"] = calls
    cached = usage.get("prompt_cache_hit_tokens")
    if cached is None:
        cached = (usage.get("prompt_tokens_details") or {}).get("cached_tokens")
    return {
        "text": content.strip(), "model": response["model"],
        "input_tokens": usage["prompt_tokens"], "output_tokens": usage["completion_tokens"],
        "cached_tokens": cached, "ms": elapsed,
        "tool_calls": calls, "assistant_message": wire, "finish_reason": choice["finish_reason"],
    }


class LiveModel:
    def __init__(self):
        import smelt
        from openai import APIError, OpenAI

        smelt.load_env(ROOT / "evals/.env")
        key = os.environ.get("SMELT_API_KEY")
        if not key:
            raise ValueError("SMELT_API_KEY is required for --live")
        base = os.environ.get("SMELT_BASE_URL", "https://api.moonshot.cn/v1")
        self.name = os.environ.get("SMELT_AGENT_MODEL", "kimi-k2")
        self.host = urlsplit(base).hostname
        self.api_error = APIError
        self.client = OpenAI(api_key=key, base_url=base, timeout=120, max_retries=0)
        self.extra = {"thinking": {"type": "disabled"}} if self.host and "deepseek" in self.host else {}

    def close(self):
        self.client.close()

    def complete(self, messages: list[dict], *, tools=None, tool_choice=None) -> dict:
        options = {}
        if tools is not None:
            options["tools"] = tools
        if tool_choice is not None:
            options["tool_choice"] = tool_choice
        started = time.perf_counter()
        try:
            response = self.client.chat.completions.create(
                model=self.name, messages=messages, temperature=0, max_tokens=512,
                extra_body=self.extra, **options,
            )
        except self.api_error as error:
            raise RuntimeError(
                "Model request failed (%s, HTTP %s); provider details omitted to protect credentials"
                % (type(error).__name__, getattr(error, "status_code", None))
            ) from None
        elapsed = (time.perf_counter() - started) * 1000
        return completion_result(response.model_dump(), elapsed)


def run_pair(model: LiveModel, history: str, case: dict, dictionary_first: bool) -> dict:
    def baseline_arm():
        return model.complete(draft_messages(history, case["draft"]))

    def dictionary_arm():
        with HookRuntime() as runtime:
            injection, inject_ms = runtime.inject()
            messages = draft_messages(history, case["draft"], injection)
            initial = model.complete(messages)
            if initial["text"] != case["draft"]:
                raise RuntimeError("dictionary draft materialization drifted; comparison is invalid: %r" % initial["text"])
            feedback, stop_ms = runtime.inspect(initial["text"])
            calls = [initial]
            if feedback:
                calls.append(model.complete(review_messages(history, initial["text"], injection, feedback)))
            remaining = runtime.annotations(calls[-1]["text"])
        return calls, inject_ms + stop_ms, [hit["term"] for hit in remaining]

    if dictionary_first:
        calls, hook_ms, remaining = dictionary_arm()
        baseline = baseline_arm()
    else:
        baseline = baseline_arm()
        calls, hook_ms, remaining = dictionary_arm()
    if baseline["text"] != case["draft"]:
        raise RuntimeError("baseline draft materialization drifted; comparison is invalid: %r" % baseline["text"])
    return {
        **paired_cost(baseline, calls, hook_ms),
        "dictionary_first": dictionary_first,
        "models": sorted({call["model"] for call in [baseline, *calls]}),
        "final_text": calls[-1]["text"], "remaining_terms": remaining,
        "numeric_facts_preserved": preserves_numeric_facts(case["draft"], calls[-1]["text"]),
    }


def run_study(context_chars=None, hook_rounds=20, model=None, model_rounds=3) -> dict:
    sizes = DEFAULT_CONTEXT_CHARS if context_chars is None else context_chars
    if len(sizes) != 3 or any(size <= 0 for size in sizes) or model_rounds <= 0:
        raise ValueError("provide three positive context sizes and positive model rounds")
    local = {case["name"]: measure_hooks(case, hook_rounds) for case in CASES}
    scenarios = []
    for label, size in zip(["short", "medium", "long"], sizes):
        history = make_history(size)
        for case in CASES:
            hook = local[case["name"]]
            baseline_messages = draft_messages(history, case["draft"])
            dictionary_messages = draft_messages(history, case["draft"], hook["injection"])
            dictionary_input = message_tokens(dictionary_messages)
            if hook["blocked"]:
                dictionary_input += message_tokens(review_messages(
                    history, case["draft"], hook["injection"], hook["feedback"],
                ))
            scenarios.append({
                "context": label, "history_chars": size, "case": case["name"],
                "draft_chars": len(case["draft"]),
                "estimated_content_tokens": {
                    "baseline_input": message_tokens(baseline_messages),
                    "baseline_output": estimated_tokens(case["draft"])[0],
                    "dictionary_input": dictionary_input,
                    "dictionary_output": estimated_tokens(case["draft"])[0] + (
                        estimated_tokens(case["reference"])[0] if hook["blocked"] else 0
                    ),
                },
                "live_trials": [], "summary": None,
            })
    if model is not None:
        for round_index in range(model_rounds):
            indices = list(range(len(scenarios)))
            random.Random(round_index).shuffle(indices)
            for index in indices:
                scenario = scenarios[index]
                case = next(case for case in CASES if case["name"] == scenario["case"])
                trial = run_pair(
                    model, make_history(scenario["history_chars"]), case,
                    dictionary_first=(round_index + index) % 2 == 0,
                )
                scenario["live_trials"].append(trial)
                print("Completed live trial: %s/%s round %d" % (
                    scenario["context"], scenario["case"], round_index + 1,
                ), file=sys.stderr, flush=True)
        for scenario in scenarios:
            scenario["summary"] = summarize_trials(scenario["live_trials"])
    return {
        "created_at": datetime.now(timezone.utc).isoformat(), "live": model is not None,
        "requested_model": model.name if model else None,
        "provider_host": model.host if model else None,
        "hook_rounds": hook_rounds, "model_rounds": model_rounds if model else 0,
        "methodology": {
            "path": "controlled draft generation, actual Stop feedback, model polishing",
            "draft_length_is_fixed": True, "context_unit": "Unicode characters",
            "stage_control": "draft target is explicit in the system prompt; review replaces that stage constraint",
            "baseline": "same history and draft, no terminology injection or Stop hook",
            "local_ms": "process wall time, including interpreter startup, excluding fixture cleanup",
            "estimated_tokens": "message text only; excludes message framing and hidden reasoning",
            "live_tokens": "provider usage; all generation and continuation requests included",
            "latency": "non-streaming request wall time plus actual hook time; not time-to-first-token",
            "cache": "reported separately; total input tokens are not the same as uncached billable tokens",
            "quality": "numeric preservation and remaining annotations, not a semantic quality score",
            "sample_scope": "retained paired trials only; protocol probes, warm-ups and invalid draft trials are excluded",
        },
        "local_hooks": local, "scenarios": scenarios,
    }


def render_report(report: dict) -> str:
    lines = [
        "# Chinese dictionary context-cost study", "",
        "Controlled fixed drafts; history varies independently of answer length.",
        "Matched cases deliberately trigger review; they do not estimate the frequency of real-world matches.",
        "Paired request order is balanced. Cache hits are recorded; tokens are not a monetary cost estimate.", "",
        "Only retained paired trials are reported; warm-ups, protocol probes and invalid draft trials are excluded.",
        "Input/output/cache counters aggregate the generation and continuation requests in each arm.", "",
        "| Case | Injection mean ms | Stop mean ms | Annotations | Estimated injection tokens |",
        "|---|---:|---:|---:|---:|",
    ]
    for case, metrics in report["local_hooks"].items():
        lines.append("| %s | %.2f | %.2f | %d | %d |" % (
            case, metrics["inject_ms"]["mean"], metrics["stop_ms"]["mean"],
            metrics["annotation_count"], metrics["injection_tokens_estimated"],
        ))
    lines += ["", "Local token backend: `%s`." % next(iter(report["local_hooks"].values()))["token_backend"], ""]
    if report["live"]:
        lines += [
            "Live requested model: `%s`; provider: `%s`." % (report["requested_model"], report["provider_host"]),
            "Actual response models: " + ", ".join(sorted({
                model for scenario in report["scenarios"] for trial in scenario["live_trials"] for model in trial["models"]
            })), "",
            "| Context | History chars | Case | Baseline input/output | Dict input/output | Extra tokens | Baseline ms | Dict ms | Extra ms (range) |",
            "|---|---:|---|---:|---:|---:|---:|---:|---:|",
        ]
        for scenario in report["scenarios"]:
            summary = scenario["summary"]
            low, high = summary["delta_ms_range"]
            lines.append("| %s | %d | %s | %.0f / %.0f | %.0f / %.0f | %.0f | %.1f | %.1f | %.1f (%.1f..%.1f) |" % (
                scenario["context"], scenario["history_chars"], scenario["case"],
                summary["baseline_input_tokens"], summary["baseline_output_tokens"],
                summary["dictionary_input_tokens"], summary["dictionary_output_tokens"],
                summary["delta_total_tokens"], summary["baseline_ms"], summary["dictionary_ms"],
                summary["delta_ms"], low, high,
            ))
        lines += ["", "## Model outputs and preservation", ""]
        for scenario in report["scenarios"]:
            lines += [
                "### %s / %s" % (scenario["context"], scenario["case"]),
                "Numeric facts preserved in every trial: %s." % scenario["summary"]["numeric_facts_preserved"],
                "Last final response:", "", scenario["live_trials"][-1]["final_text"], "",
            ]
    else:
        lines += [
            "Model latency and provider usage: **not measured**. Run with `--live`.",
            "Content token counts below are estimated, not provider usage.", "",
            "| Context | History chars | Case | Baseline estimated input | Dict estimated input |",
            "|---|---:|---|---:|---:|",
        ]
        for scenario in report["scenarios"]:
            tokens = scenario["estimated_content_tokens"]
            lines.append("| %s | %d | %s | %d | %d |" % (
                scenario["context"], scenario["history_chars"], scenario["case"],
                tokens["baseline_input"], tokens["dictionary_input"],
            ))
    lines += [
        "## Interpretation", "",
        "Stop sees only the last response, not the entire history. Local checking therefore need not grow with conversation history.",
        "A rewrite continuation sends the history again. Its input tokens, response tokens and network/generation latency are included above.",
        "No automatic string replacement is performed. Remaining annotations can be legitimate retained wording.",
        "These are synthetic, controlled samples from one provider; caching and network timing affect the observed deltas.",
    ]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="Use the existing eval model and record actual usage")
    parser.add_argument("--hook-rounds", type=int, default=20)
    parser.add_argument("--model-rounds", type=int, default=3)
    parser.add_argument("--context-chars", type=int, nargs=3, default=DEFAULT_CONTEXT_CHARS)
    parser.add_argument("--output", type=Path, help="JSON report path; Markdown is saved alongside it")
    args = parser.parse_args()
    model = LiveModel() if args.live else None
    try:
        report = run_study(args.context_chars, args.hook_rounds, model, args.model_rounds)
    finally:
        if model is not None:
            model.close()
    markdown = render_report(report)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        args.output.with_suffix(".md").write_text(markdown, encoding="utf-8")
    print(markdown)


if __name__ == "__main__":
    main()
