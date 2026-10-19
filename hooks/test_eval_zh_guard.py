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
    check("python 解释器启动基准为正数（%.1f ms）" % startup, startup > 0)
    base = eval_zh_guard.baseline()
    check("基线（没装 hook）注入 token 为 0", base["tokens"] == 0)
    check("基线（没装 hook）耗时为 0", base["ms"] == 0.0)


def test_empty_dict_still_costs_rules_text():
    d = tmpdir()
    try:
        empty = eval_zh_guard.empty_dict(os.path.join(d, "empty.tsv"))
        cost = eval_zh_guard.inject_cost(empty)
        check("空字典词条数为 0", cost["entries"] == 0, str(cost))
        check("空字典仍然注入规则文本（%d token）" % cost["tokens"],
              cost["tokens"] > 0, str(cost))
        check("规则文本里含「禁止字面直译」", "禁止字面直译" in cost["ctx"],
              cost["ctx"][:200])
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_dictionary_has_measurable_marginal_cost():
    d = tmpdir()
    try:
        empty = eval_zh_guard.empty_dict(os.path.join(d, "empty.tsv"))
        full = eval_zh_guard.full_dict(os.path.join(d, "full.tsv"))
        ce, cf = eval_zh_guard.inject_cost(empty), eval_zh_guard.inject_cost(full)
        check("完整字典注入 token 高于空字典（%d → %d）" % (ce["tokens"], cf["tokens"]),
              cf["tokens"] > ce["tokens"])
        check("两份字典都会被注入至少一个词条以上的清单",
              cf["entries"] >= 30, str(cf["entries"]))
        check("注入 hook 本身正常退出", ce["rc"] == 0 and cf["rc"] == 0)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_verdicts_follow_the_dictionary():
    d = tmpdir()
    try:
        empty = eval_zh_guard.empty_dict(os.path.join(d, "e.tsv"))
        full = eval_zh_guard.full_dict(os.path.join(d, "f.tsv"))
        check("空字典：不该拦的全放行",
              eval_zh_guard.verdict(empty, FLAGGED) == 0
              and eval_zh_guard.verdict(empty, CLEAN) == 0)
        check("完整字典：命中直译词就拦",
              eval_zh_guard.verdict(full, FLAGGED) == 2)
        check("完整字典：干净中文放行",
              eval_zh_guard.verdict(full, CLEAN) == 0)
        check("完整字典：引号提及豁免",
              eval_zh_guard.verdict(full, EXEMPT) == 0)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_interception_cost_is_measured():
    d = tmpdir()
    try:
        full = eval_zh_guard.full_dict(os.path.join(d, "f.tsv"))
        ic = eval_zh_guard.interception_cost(full)
        check("完整字典确实会拦截（用于量代价）", ic["blocked"] is True, str(ic))
        check("单次拦截代价含重写回复的 token（%d）" % ic["cost_per_block_tokens"],
              ic["cost_per_block_tokens"] > ic["instruction_tokens"] > 0)
        check("最坏窗口按 10 分钟 3 次折算",
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
            check("%s 为正数（%.1f ms）" % (key, timing[key]), timing[key] > 0)
        net = eval_zh_guard.net_ms(timing["inspect_hit_ms"], startup)
        check("扣掉解释器启动后净耗时更小且非负（%.1f ms）" % net,
              0 <= net < timing["inspect_hit_ms"])
    finally:
        shutil.rmtree(d, ignore_errors=True)


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        try:
            t()
        except Exception as exc:
            check(t.__name__ + "（异常）", False, repr(exc))
    print("")
    if FAILURES:
        print("失败 %d 项：%s" % (len(FAILURES), ", ".join(FAILURES)))
        sys.exit(1)
    print("全部通过（%d 项测试）" % len(tests))
    sys.exit(0)


if __name__ == "__main__":
    main()
