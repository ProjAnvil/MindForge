#!/usr/bin/env python3
"""zh-guard 词典整理 / 体检工具。

用法：
    python3 tidy-dict.py                      # 体检（只读，打印报告）
    python3 tidy-dict.py --check              # 体检，有问题退出码非 0（可挂 pre-commit）
    python3 tidy-dict.py --write              # 体检 + 写回排版后的文件
    python3 tidy-dict.py --write --path FILE  # 指定文件，不用两边的默认路径

默认处理两个文件：自带字典（本目录）和用户字典（~/.claude/zh-guard/）。

做的事：
  1. 排版：三列按宽度对齐（补空格到 Tab 前），注释行原样保留；
  2. 归一化：去掉行首尾空白、清掉 BOM、统一行尾换行；
  3. 去重：同一第一列保留最后一次出现（与运行时「用户条目优先」一致），并报告；
  4. 体检：第一列以 re: 开头的词条尝试编译，坏正则报错但不改文件；
  5. 报错：缺第二列（只有直译词没写期望写法）的行。

fail-open 风格：单个文件读不动就跳过它，继续下一个。
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MAX_COL = 28  # 对齐时列宽上限，避免长词条把表格撑爆


def default_paths():
    paths = [os.path.join(HERE, "terminology.tsv")]
    home = os.environ.get(
        "ZH_GUARD_HOME",
        os.path.join(os.path.expanduser("~"), ".claude", "zh-guard"),
    )
    user = os.path.join(home, "terminology.tsv")
    if os.path.exists(user):
        paths.append(user)
    return paths


def read_lines(path):
    with open(path, encoding="utf-8-sig") as f:
        return f.read().splitlines()


def parse(lines):
    """把文件拆成 [(kind, payload)]，kind ∈ {comment, blank, row}。

    row 的 payload 是 [直译词, 期望写法, 说明]，缺的列补空串。
    """
    out = []
    for raw in lines:
        line = raw.rstrip("\n").lstrip("\ufeff")
        stripped = line.strip()
        if not stripped:
            out.append(("blank", ""))
            continue
        if stripped.startswith("#"):
            out.append(("comment", stripped))
            continue
        cells = [c.strip() for c in line.split("\t")]
        if len(cells) == 1:
            # 空格/多空格分隔的情况兜一层，方便手写时用空格对齐
            cells = [c.strip() for c in re.split(r"\s{2,}", line, 1)]
            if len(cells) == 2:
                cells += [""]
        # 手改时常用 Tab 缩进整行，丢掉行首的空单元格，别当成坏词条
        while cells and not cells[0]:
            cells.pop(0)
        if not cells:
            out.append(("blank", ""))
            continue
        while len(cells) < 3:
            cells.append("")
        out.append(("row", cells[:3]))
    return out


def check(items):
    """返回 (errors, warnings) 列表。"""
    errors, warnings = [], []
    seen = {}
    for i, (kind, payload) in enumerate(items, start=1):
        if kind != "row":
            continue
        term, target, note = payload
        if not term:
            errors.append("第 %d 行：第一列为空" % i)
            continue
        if not target:
            errors.append("第 %d 行：%s 缺第二列（期望写法）" % (i, term))
        if term.startswith("re:"):
            try:
                re.compile(term[3:])
            except re.error as exc:
                errors.append("第 %d 行：正则写坏了 %s（%s）" % (i, term, exc))
        if term in seen:
            warnings.append("第 %d 行：%s 重复（保留最后一次）→ 已在第 %d 行出现过"
                            % (i, term, seen[term]))
        seen[term] = i
    return errors, warnings


def dedupe(items):
    """同一第一列保留最后一次出现，位置留在最后一次出现处。"""
    last_index = {}
    for i, (kind, payload) in enumerate(items):
        if kind == "row" and payload[0]:
            last_index[payload[0]] = i
    keep = set(last_index.values())
    return [it for i, it in enumerate(items) if i in keep or it[0] != "row"]


def render(items):
    rows = [p for k, p in items if k == "row"]
    if not rows:
        return "\n".join(p if k == "comment" else "" for k, p in items) + "\n"

    def width(idx):
        cols = [r[idx] for r in rows]
        # 中文按两个字符宽算，视觉才对得齐
        return min(MAX_COL, max(display_width(c) for c in cols) + 2)

    w = [width(0), width(1)]
    lines = []
    for kind, payload in items:
        if kind == "comment":
            lines.append(payload)
        elif kind == "blank":
            lines.append("")
        else:
            term, target, note = payload
            pad0 = " " * max(0, w[0] - display_width(term))
            pad1 = " " * max(0, w[1] - display_width(target))
            # 三个分隔符始终保留：缺列的词条也要保持 TSV 结构，方便下次解析和手改
            lines.append(term + pad0 + "\t" + target + pad1 + "\t" + note)
    return "\n".join(lines) + "\n"


def display_width(text):
    return sum(2 if ord(c) > 0x2E80 else 1 for c in text)


def tidy(path, write=False):
    try:
        lines = read_lines(path)
    except Exception as exc:
        print("跳过（读不到）：%s | %s" % (path, exc))
        return True
    items = parse(lines)
    items = dedupe(items)
    errors, warnings = check(items)
    clean = render(items)

    print("── %s" % path)
    for w in warnings:
        print("   提示 %s" % w)
    for e in errors:
        print("   问题 %s" % e)
    status = "干净" if not errors and not warnings else ("%d 个问题" % len(errors))
    print("   %s，共 %d 条词条" % (
        status, len([1 for k, _ in items if k == "row"])))

    if clean != "\n".join(lines) + "\n":
        if write:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(clean)
                print("   已排版写回")
            except Exception as exc:
                print("   写回失败：%s" % exc)
                return False
        else:
            print("   排版有变化，加 --write 写回")
    return not errors


def main():
    ap = argparse.ArgumentParser(description="zh-guard 词典整理 / 体检")
    ap.add_argument("--write", action="store_true", help="写回排版后的文件")
    ap.add_argument("--check", action="store_true", help="有问题时退出码为 1")
    ap.add_argument("--path", help="只处理指定文件")
    args = ap.parse_args()

    paths = [args.path] if args.path else default_paths()
    ok = True
    for p in paths:
        if not os.path.exists(p):
            print("跳过（不存在）：%s" % p)
            continue
        ok = tidy(p, write=args.write) and ok
    if args.check and not ok:
        print("")
        print("存在必须修的错误")
        sys.exit(1)
    print("")
    print("体检通过" if ok else "体检发现问题")


if __name__ == "__main__":
    main()
