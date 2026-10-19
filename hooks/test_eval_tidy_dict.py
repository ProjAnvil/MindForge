#!/usr/bin/env python3
"""eval_tidy_dict.py 测试套件。

评测工具自己也要有测试，否则没人敢信它报出来的数。
覆盖：脏字典构造、行为等价、注入开销不反弹、计时与 token 计数可用性。

运行：python3 test_eval_tidy_dict.py
"""
import importlib.util
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
BUNDLED = os.path.join(HERE, "terminology.tsv")

_spec = importlib.util.spec_from_file_location(
    "eval_tidy_dict", os.path.join(HERE, "eval-tidy-dict.py"))
eval_tidy_dict = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(eval_tidy_dict)

FAILURES = []


def check(name, condition, detail=""):
    if condition:
        print("PASS  " + name)
    else:
        print("FAIL  " + name + ("  | " + detail if detail else ""))
        FAILURES.append(name)


def temp_home():
    return tempfile.mkdtemp(prefix="eval-home-")


def clean_rows():
    with open(BUNDLED, encoding="utf-8") as f:
        return f.read()


def test_corpus_is_balanced():
    corpus = eval_tidy_dict.load_corpus(None)
    blocks = [c for c in corpus if c[1] == "block"]
    passes = [c for c in corpus if c[1] == "pass"]
    check("语料两类都有样本（%d 拦 / %d 放行）" % (len(blocks), len(passes)),
          len(blocks) >= 8 and len(passes) >= 8, str(corpus)[:200])
    check("语料覆盖引号豁免场景",
          any("「" in c[0] and c[1] == "pass" for c in corpus))
    check("语料覆盖代码块豁免场景",
          any("```" in c[0] and c[1] == "pass" for c in corpus))


def test_dirty_dict_has_duplicates_and_noise():
    d = tempfile.mkdtemp(prefix="eval-dirty-")
    try:
        dirty = eval_tidy_dict.build_dirty_copy(clean_rows(), os.path.join(d, "dirty.tsv"))
        with open(dirty, encoding="utf-8") as f:
            text = f.read()
        rows = [l for l in text.splitlines() if l.strip() and not l.strip().startswith("#")]
        keys = [r.split("\t")[0].strip() for r in rows]
        check("脏字典里确实有重复词条", len(keys) != len(set(keys)),
              "%d 行 / %d 唯一" % (len(keys), len(set(keys))))
        check("脏字典带 BOM（模拟手改过的文件）", text.startswith("\ufeff"))
        check("脏字典存在参差不齐的空白",
              any("   " in r for r in rows) or any(r != r.strip() for r in rows))
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_tidy_is_behaviour_preserving():
    """核心断言：整理前后，每条句子的判定必须完全一样。"""
    d = tempfile.mkdtemp(prefix="eval-equiv-")
    try:
        before = eval_tidy_dict.build_dirty_copy(clean_rows(), os.path.join(d, "before.tsv"))
        after = os.path.join(d, "after.tsv")
        eval_tidy_dict.run_tidy(before, after)
        corpus = eval_tidy_dict.load_corpus(None)
        v_before = eval_tidy_dict.verdicts(corpus, before)
        v_after = eval_tidy_dict.verdicts(corpus, after)
        diff = [(s, a, b) for (s, a), (s2, b) in zip(v_before, v_after) if a != b]
        check("整理前后判定完全一致（%d 条语料）" % len(corpus), not diff, str(diff[:3]))
        hits = sum(1 for _, v in v_after if v == 2)
        check("该拦的句子确实被拦了（%d 条命中）" % hits,
              hits >= 8, str(v_after))
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_injection_cost_does_not_regress():
    d = tempfile.mkdtemp(prefix="eval-cost-")
    try:
        before = eval_tidy_dict.build_dirty_copy(clean_rows(), os.path.join(d, "before.tsv"))
        after = os.path.join(d, "after.tsv")
        eval_tidy_dict.run_tidy(before, after)
        cb = eval_tidy_dict.injection_cost(before)
        ca = eval_tidy_dict.injection_cost(after)
        check("注入字符数整理后不增加（%d → %d）" % (cb["chars"], ca["chars"]),
              ca["chars"] <= cb["chars"])
        check("注入词条数整理后不增加（%d → %d）" % (cb["entries"], ca["entries"]),
              ca["entries"] <= cb["entries"])
        check("注入 token 数整理后不增加（%s → %s）" % (cb["tokens"], ca["tokens"]),
              ca["tokens"] <= cb["tokens"])
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_tokenizer_and_timing_are_usable():
    n, backend = eval_tidy_dict.count_tokens("请把这段话切成 token 看看有多长。")
    check("token 计数返回正数（%d，后端 %s）" % (n, backend), n > 0)
    d = tempfile.mkdtemp(prefix="eval-time-")
    try:
        path = os.path.join(d, "t.tsv")
        eval_tidy_dict.build_dirty_copy(clean_rows(), path)
        t = eval_tidy_dict.runtime_cost(path, rounds=3)
        for key in ("inject_mean_ms", "inject_min_ms", "inspect_mean_ms"):
            check("计时项 %s 为正数（%.1f ms）" % (key, t[key]), t[key] > 0)
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
