#!/usr/bin/env python3
"""tidy-dict.py 测试套件。

运行：python3 test_tidy_dict.py
覆盖：解析归一化、去重（后来居上）、坏正则与缺列报错、排版幂等、注释保留。
"""
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
PY = sys.executable

_spec = importlib.util.spec_from_file_location("tidy_dict", os.path.join(HERE, "tidy-dict.py"))
tidy_dict = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tidy_dict)

FAILURES = []


def check(name, condition, detail=""):
    if condition:
        print("PASS  " + name)
    else:
        print("FAIL  " + name + ("  | " + detail if detail else ""))
        FAILURES.append(name)


SAMPLE = (
    "# 注释要保留\n"
    "病灶实验\t消融实验\t社区定译\n"
    "#\n"
    "病灶实验\t用户改写的说法\t覆盖前一条\n"
    "多余列\t建议\t说明\tunexpected\n"
    "re:第[刀\t第 N 处\t坏正则\n"
    "地面真实\t真值\t评测语境\n"
)


def test_parse_and_dedupe():
    items = tidy_dict.parse(SAMPLE.splitlines())
    items = tidy_dict.dedupe(items)
    rows = [p for k, p in items if k == "row"]
    keys = [r[0] for r in rows]
    check("Deduplication keeps one occurrence of the repeated term", keys.count("病灶实验") == 1, str(keys))
    check("Deduplication keeps the last entry",
          rows[keys.index("病灶实验")][1] == "用户改写的说法")
    check("Comments are not parsed as entries", len([1 for k, _ in items if k == "comment"]) == 2)
    _, warnings = tidy_dict.check(tidy_dict.parse(SAMPLE.splitlines()))
    check("Duplicate entries produce a warning", any("duplicate" in w for w in warnings))


def test_extra_columns_and_bad_regex():
    items = tidy_dict.parse(SAMPLE.splitlines())
    errors, _ = tidy_dict.check(items)
    joined = " | ".join(errors)
    check("Extra columns produce an error", any("three columns" in e for e in errors), joined)
    check("Invalid regex produces an error", any("invalid regex" in e for e in errors), joined)
    check("Valid entries produce no errors",
          not any("消融实验" in e or "真值" in e for e in errors), joined)


def test_render_alignment_and_idempotent():
    items = tidy_dict.dedupe(tidy_dict.parse(SAMPLE.splitlines()))
    first = tidy_dict.render(items)
    check("Formatting preserves TSV cells",
          all(len(line.split("\t")) >= 3 for line in first.splitlines()
              if line and not line.startswith("#")))
    again = tidy_dict.dedupe(tidy_dict.parse(first.splitlines()))
    check("Formatting is idempotent", tidy_dict.render(again) == first,
          "\n" + first + "---\n" + tidy_dict.render(again))
    check("Comments are preserved unchanged", "# 注释要保留" in first)
    check("Columns are aligned with padding", "病灶实验 " in first or "多余列 " in first)


def test_check_exit_code():
    """--check 在有错时退出码为 1，干净文件时为 0。"""
    d = tempfile.mkdtemp(prefix="tidy-test-")
    try:
        bad = os.path.join(d, "bad.tsv")
        with open(bad, "w", encoding="utf-8") as f:
            f.write(SAMPLE)
        p1 = subprocess.run([PY, os.path.join(HERE, "tidy-dict.py"), "--check", "--path", bad],
                            capture_output=True, timeout=20)
        check("Invalid dictionary exits with status 1 under --check", p1.returncode == 1, "rc=%d" % p1.returncode)

        good = os.path.join(d, "good.tsv")
        with open(good, "w", encoding="utf-8") as f:
            f.write("# 分组\n地面真实\t真值\t评测语境\n next\tX\tY\n".replace(" next", "下一个"))
        p2 = subprocess.run([PY, os.path.join(HERE, "tidy-dict.py"), "--check", "--path", good],
                            capture_output=True, timeout=20)
        check("Valid dictionary exits with status 0 under --check", p2.returncode == 0, "rc=%d" % p2.returncode)

        # --write 之后文件应当已经幂等（再跑一次不再提示排版有变化）
        subprocess.run([PY, os.path.join(HERE, "tidy-dict.py"), "--write", "--path", good],
                       capture_output=True, timeout=20)
        p3 = subprocess.run([PY, os.path.join(HERE, "tidy-dict.py"), "--path", good],
                            capture_output=True, timeout=20)
        check("Checking formatted output reports no further changes",
              "Formatting changes" not in p3.stdout.decode("utf-8"), p3.stdout.decode("utf-8")[:200])
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_real_dict_is_clean():
    """仓库自带字典本身必须体检干净。"""
    real = os.path.join(HERE, "terminology.tsv")
    items = tidy_dict.dedupe(tidy_dict.parse(tidy_dict.read_lines(real)))
    errors, warnings = tidy_dict.check(items)
    rows = [1 for k, _ in items if k == "row"]
    check("Bundled dictionary passes validation", not errors, " | ".join(errors))
    check("Bundled dictionary has no duplicate entries", not warnings, " | ".join(warnings))
    check("Bundled dictionary has at least 30 entries (%d found)" % len(rows), len(rows) >= 30)
    rendered = tidy_dict.render(items)
    with open(real, encoding="utf-8") as f:
        check("Bundled dictionary is already formatted",
              f.read() == rendered)


def test_three_columns_and_extra_column_validation():
    source = "旧词\t候选写法\t说明\n机械胳膊\t\t身体部件\n"
    items = tidy_dict.parse(source.splitlines())
    rendered = tidy_dict.render(items)
    rows = [line.split("\t") for line in rendered.splitlines()]
    check("Three-column format preserves empty suggestions", len(rows[0]) == 3 and len(rows[1]) == 3
          and rows[1][1].strip() == "", rendered)
    check("Three-column formatting is idempotent", tidy_dict.render(tidy_dict.parse(rendered.splitlines())) == rendered)
    for row in [
        "旧词\t新词\t说明\tunknown",
        "re:旧词\t新词\t说明\treplace",
        "旧词\t候选一 / 候选二\t说明\treplace",
        "旧词\t新词\t说明\trewrite\t多余列",
    ]:
        errors, _ = tidy_dict.check(tidy_dict.parse([row]))
        check("Invalid extra-column input reports an error (%s)" % row, bool(errors), str(errors))


def test_glossary_and_meaning_only_entries_round_trip():
    source = "星环\n机械胳膊\t\t科幻人物的身体部件\n旧词\t偏好写法\n"
    items = tidy_dict.parse(source.splitlines())
    errors, _ = tidy_dict.check(items)
    check("Glossary and meaning-only entries do not require suggestions", not errors, str(errors))
    rendered = tidy_dict.render(items)
    rows = [[cell.strip() for cell in line.split("\t")] for line in rendered.splitlines()]
    check("Empty second cells and two-column suggestions retain their positions", rows == [
        ["星环", "", ""], ["机械胳膊", "", "科幻人物的身体部件"], ["旧词", "偏好写法", ""],
    ], str(rows))
    check("Optional-cell formatting is idempotent", tidy_dict.render(tidy_dict.parse(rendered.splitlines())) == rendered)
    directory = tempfile.mkdtemp(prefix="tidy-glossary-")
    try:
        path = os.path.join(directory, "project.tsv")
        with open(path, "w", encoding="utf-8") as stream:
            stream.write(source)
        process = subprocess.run(
            [PY, os.path.join(HERE, "tidy-dict.py"), "--check", "--write", "--path", path],
            capture_output=True, timeout=20,
        )
        check("Glossary and meaning entries can be validated and written", process.returncode == 0, process.stdout.decode())
    finally:
        shutil.rmtree(directory)


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
