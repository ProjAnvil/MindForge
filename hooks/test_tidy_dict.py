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
    "缺列词\n"
    "re:第[刀\t第 N 处\t坏正则\n"
    "地面真实\t真值\t评测语境\n"
)


def test_parse_and_dedupe():
    items = tidy_dict.parse(SAMPLE.splitlines())
    items = tidy_dict.dedupe(items)
    rows = [p for k, p in items if k == "row"]
    keys = [r[0] for r in rows]
    check("去重后病灶实验只剩一条", keys.count("病灶实验") == 1, str(keys))
    check("去重保留最后一次出现（后来居上）",
          rows[keys.index("病灶实验")][1] == "用户改写的说法")
    check("注释行不被当成词条", len([1 for k, _ in items if k == "comment"]) == 2)
    _, warnings = tidy_dict.check(tidy_dict.parse(SAMPLE.splitlines()))
    check("重复词条有提示", any("重复" in w for w in warnings))


def test_missing_target_and_bad_regex():
    items = tidy_dict.parse(SAMPLE.splitlines())
    errors, _ = tidy_dict.check(items)
    joined = " | ".join(errors)
    check("缺第二列报错", any("缺第二列" in e for e in errors), joined)
    check("坏正则报错", any("正则写坏了" in e for e in errors), joined)
    check("正常词条不报错",
          not any("消融实验" in e or "真值" in e for e in errors), joined)


def test_render_alignment_and_idempotent():
    items = tidy_dict.dedupe(tidy_dict.parse(SAMPLE.splitlines()))
    first = tidy_dict.render(items)
    check("排版后仍是合法 TSV（三列都在）",
          all(len(line.split("\t")) == 3 for line in first.splitlines()
              if line and not line.startswith("#")))
    again = tidy_dict.dedupe(tidy_dict.parse(first.splitlines()))
    check("排版幂等（再跑一次不变）", tidy_dict.render(again) == first,
          "\n" + first + "---\n" + tidy_dict.render(again))
    check("注释原样保留", "# 注释要保留" in first)
    check("补了空格做列对齐", "病灶实验 " in first or "缺列词 " in first)


def test_check_exit_code():
    """--check 在有错时退出码为 1，干净文件时为 0。"""
    d = tempfile.mkdtemp(prefix="tidy-test-")
    try:
        bad = os.path.join(d, "bad.tsv")
        with open(bad, "w", encoding="utf-8") as f:
            f.write(SAMPLE)
        p1 = subprocess.run([PY, os.path.join(HERE, "tidy-dict.py"), "--check", "--path", bad],
                            capture_output=True, timeout=20)
        check("有问题的字典 --check 退出码为 1", p1.returncode == 1, "rc=%d" % p1.returncode)

        good = os.path.join(d, "good.tsv")
        with open(good, "w", encoding="utf-8") as f:
            f.write("# 分组\n地面真实\t真值\t评测语境\n next\tX\tY\n".replace(" next", "下一个"))
        p2 = subprocess.run([PY, os.path.join(HERE, "tidy-dict.py"), "--check", "--path", good],
                            capture_output=True, timeout=20)
        check("干净的字典 --check 退出码为 0", p2.returncode == 0, "rc=%d" % p2.returncode)

        # --write 之后文件应当已经幂等（再跑一次不再提示排版有变化）
        subprocess.run([PY, os.path.join(HERE, "tidy-dict.py"), "--write", "--path", good],
                       capture_output=True, timeout=20)
        p3 = subprocess.run([PY, os.path.join(HERE, "tidy-dict.py"), "--path", good],
                            capture_output=True, timeout=20)
        check("写回后再体检不再提示排版变化",
              "排版有变化" not in p3.stdout.decode("utf-8"), p3.stdout.decode("utf-8")[:200])
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_real_dict_is_clean():
    """仓库自带字典本身必须体检干净。"""
    real = os.path.join(HERE, "terminology.tsv")
    items = tidy_dict.dedupe(tidy_dict.parse(tidy_dict.read_lines(real)))
    errors, warnings = tidy_dict.check(items)
    rows = [1 for k, _ in items if k == "row"]
    check("自带字典体检无错误", not errors, " | ".join(errors))
    check("自带字典无重复词条", not warnings, " | ".join(warnings))
    check("自带字典词条数不少于 30（%d 条）" % len(rows), len(rows) >= 30)
    rendered = tidy_dict.render(items)
    with open(real, encoding="utf-8") as f:
        check("自带字典已排版（无需再写回）",
              f.read() == rendered)


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
