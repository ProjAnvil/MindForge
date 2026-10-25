#!/usr/bin/env python3
"""评测工具（eval-zh-guard.py）自身的测试。

量的是整套翻译腔防御方案的成本，测试要盯住三件事：
基线必须为零、空字典也要算规则文本的账、字典的边际成本要能被单独量出来。

运行：python3 test_eval_zh_guard.py
"""
import importlib.util
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLED = os.path.join(HERE, "terminology.tsv")

_spec = importlib.util.spec_from_file_location(
    "eval_zh_guard", os.path.join(HERE, "eval-zh-guard.py"))
eval_zh_guard = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eval_zh_guard)

FAILURES = []

FLAGGED = "这次我们又做了一遍病灶实验，结论没变。"
CLEAN = "重试次数从 24 次降到 7 次，抖动消失了。"
EXEMPT = "字典里写着：「病灶实验」→消融实验，这条要避开。"


def check(name, condition, detail=""):
    if condition:
        print("PASS  " + name)
    else:
        print("FAIL  " + name + ("  | " + detail if detail else ""))
        FAILURES.append(name)


def tmpdir():
    return tempfile.mkdtemp(prefix="eval-zg-")


def test_baseline_is_zero_startup_is_positive():
    startup = eval_zh_guard.python_startup_ms(rounds=5)
    check("Python startup baseline is positive (%.1f ms)" % startup, startup > 0)
    base = eval_zh_guard.baseline()
    check("Baseline without hooks injects zero tokens", base["tokens"] == 0)
    check("Baseline without hooks has zero overhead", base["ms"] == 0.0)


def test_empty_dict_still_costs_rules_text():
    d = tmpdir()
    try:
        empty = eval_zh_guard.empty_dict(os.path.join(d, "empty.tsv"))
        cost = eval_zh_guard.inject_cost(empty)
        check("Empty dictionary has zero entries", cost["entries"] == 0, str(cost))
        check("Empty dictionary still injects writing rules (%d tokens)" % cost["tokens"],
              cost["tokens"] > 0, str(cost))
        check("Injected rules include translationese guidance", "禁止字面直译" in cost["ctx"],
              cost["ctx"][:200])
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_dictionary_has_measurable_marginal_cost():
    d = tmpdir()
    try:
        empty = eval_zh_guard.empty_dict(os.path.join(d, "empty.tsv"))
        full = eval_zh_guard.full_dict(os.path.join(d, "full.tsv"))
        ce, cf = eval_zh_guard.inject_cost(empty), eval_zh_guard.inject_cost(full)
        check("Full dictionary injects more tokens than empty dictionary (%d -> %d)" % (ce["tokens"], cf["tokens"]),
              cf["tokens"] > ce["tokens"])
        check("Full dictionary exposes the expected entry list",
              cf["entries"] >= 30, str(cf["entries"]))
        check("Injection hook exits successfully", ce["rc"] == 0 and cf["rc"] == 0)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_verdicts_follow_the_dictionary():
    d = tmpdir()
    try:
        empty = eval_zh_guard.empty_dict(os.path.join(d, "e.tsv"))
        full = eval_zh_guard.full_dict(os.path.join(d, "f.tsv"))
        check("Empty dictionary allows all tested messages",
              eval_zh_guard.verdict(empty, FLAGGED) == 0
              and eval_zh_guard.verdict(empty, CLEAN) == 0)
        check("Full dictionary blocks matching expressions",
              eval_zh_guard.verdict(full, FLAGGED) == 2)
        check("Full dictionary allows clean text",
              eval_zh_guard.verdict(full, CLEAN) == 0)
        check("Full dictionary exempts quoted mentions",
              eval_zh_guard.verdict(full, EXEMPT) == 0)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_interception_cost_is_measured():
    d = tmpdir()
    try:
        full = eval_zh_guard.full_dict(os.path.join(d, "f.tsv"))
        ic = eval_zh_guard.interception_cost(full)
        check("Full dictionary blocks the cost-measurement sample", ic["blocked"] is True, str(ic))
        check("Block cost includes response regeneration (%d tokens)" % ic["cost_per_block_tokens"],
              ic["cost_per_block_tokens"] > ic["instruction_tokens"] > 0)
        check("Worst-case window includes three blocks per ten minutes",
              ic["worst_window_tokens"] == 3 * ic["cost_per_block_tokens"])
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_timing_splits_startup_from_logic():
    d = tmpdir()
    try:
        full = eval_zh_guard.full_dict(os.path.join(d, "f.tsv"))
        timing = eval_zh_guard.timing(full, rounds=5)
        startup = eval_zh_guard.python_startup_ms(rounds=5)
        for key in ("inject_ms", "inspect_clean_ms", "inspect_hit_ms"):
            check("%s is positive (%.1f ms)" % (key, timing[key]), timing[key] > 0)
        net = eval_zh_guard.net_ms(timing["inspect_hit_ms"], startup)
        check("Net timing excludes startup and remains nonnegative (%.1f ms)" % net,
              0 <= net < timing["inspect_hit_ms"])
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        try:
            t()
        except Exception as exc:
            check(t.__name__ + " (exception)", False, repr(exc))
    print("")
    if FAILURES:
        print("Failed %d checks: %s" % (len(FAILURES), ", ".join(FAILURES)))
        sys.exit(1)
    print("All passed (%d tests)" % len(tests))
    sys.exit(0)


if __name__ == "__main__":
    main()
