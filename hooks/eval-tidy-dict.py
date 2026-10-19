#!/usr/bin/env python3
"""tidy-dict 评测：整理前后到底变好了没有，拿数字说话。

它要回答三个问题：
  1. 行为等价吗 —— 同一批句子，整理前后判定必须一模一样（最重要的一条）；
  2. 省了吗     —— L1 注入的字符数 / token 数、词条数，整理后不能反弹；
  3. 贵不贵     —— hook 端到端耗时（毫秒级），整理前后对比。

用法：
    python3 eval-tidy-dict.py                 # 跑完整评测，打印对比表
    python3 eval-tidy-dict.py --json          # 输出机器可读的指标（CI 里 diff 用）
    python3 eval-tidy-dict.py --rounds 20     # 计时多跑几轮，压掉噪声
    python3 eval-tidy-dict.py --corpus X.tsv  # 换成自己的语料

「整理前」不是凭空想象：由当前字典程序化地生成一份脏副本（重复词条、参差
空白、BOM、多余空行），代表手改之后没整理的样子。整理后 = tidy-dict 的产出。

token 计数优先用 tiktoken（装了就更准），没装就用标注清楚的估算公式，
报告里会写明用的是哪个。
"""
import argparse
import importlib.util
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
INJECT = os.path.join(HERE, "inject.py")
INSPECT = os.path.join(HERE, "inspect.py")
BUNDLED = os.path.join(HERE, "terminology.tsv")
TIDY = os.path.join(HERE, "tidy-dict.py")

CJK = r"[\u3400-\u9fff\uf900-\ufaff]"

# 语料：(句子, 期望) —— block=应被拦（exit 2），pass=应放行（exit 0）
# 覆盖三类：真用了直译词、干净的中文、豁免区（引号提及 / 代码块）。
CORPUS = [
    ("这次我们又做了一遍病灶实验，结论和上次一致。", "block"),
    ("服务大面积超时，崩溃路径上的死因是连接池耗尽。", "block"),
    ("这块逻辑藏在引擎盖下的调度层，文档里没写。", "block"),
    ("上线之前先跑一遍健全性检查。", "block"),
    ("推理阶段会出现少量幽灵词元，需要在输出端拦掉。", "block"),
    ("外层需要一层范围守卫来保证资源一定被释放。", "block"),
    ("接口先锚定到 v2，等稳定后再往上抬。", "block"),
    ("按照计划，第36刀砍在推理预算上。", "block"),
    ("下一步先看下一刀动哪里，别急着改别的。", "block"),
    ("把这个版本的依赖版本钉死再合入主干。", "block"),
    ("这个 bug 的病症很明显：偶发超时加重试失败。", "block"),
    ("这个 token 的上限写死在配置里，不能覆盖。", "pass"),
    ("我们把重试次数从 24 次降到 7 次，抖动消失了。", "pass"),
    ("这一版还剩两个待办没处理，明天跟进。", "pass"),
    ("作用域守卫负责在函数退出时释放句柄。", "pass"),
    ("前端说的「锚点」指的是页内跳转，别动它。", "pass"),
    ("字典里写着：「病灶实验」→消融实验，这条要避开。", "pass"),
    ("排查脚本如下：\n```python\n# 死因分析\nfind_root_cause()\n```\n上面这段可以直接跑。", "pass"),
    ("小样本上的结论不稳，建议重跑三轮再定。", "pass"),
    ("我们把版本锁定到 v2，暂时不升级。", "pass"),
]


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_corpus(path=None):
    """读语料。外部文件格式：句子<TAB>block|pass。"""
    if path:
        rows = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.rstrip("\n")
                if not line.strip() or line.startswith("#"):
                    continue
                cells = line.split("\t")
                if len(cells) >= 2 and cells[1].strip() in ("block", "pass"):
                    rows.append((cells[0].strip(), cells[1].strip()))
        return rows
    return list(CORPUS)


def count_tokens(text):
    """返回 (token 数, 后端)。优先 tiktoken，没装就用清楚的估算。"""
    try:
        import tiktoken  # type: ignore
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text)), "tiktoken/cl100k_base"
    except Exception:
        # 估算：中文字符按 1 个 token，英文/数字词按 1 个词 1.3 个 token
        cjk_len = len(re.findall(CJK, text))
        words = re.findall(r"[A-Za-z0-9_]+", text)
        return int(cjk_len + len(words) * 1.3 + 0.999), "estimate(cjk+1.3*words)"


def build_dirty_copy(clean_text, dst):
    """从干净字典造一份「整理前」的脏副本：BOM + 重复 + 参差空白 + 空行。"""
    lines = clean_text.lstrip("\ufeff").splitlines()
    out = []
    dup_targets = {"病灶实验", "幽灵节点", "下一刀", "范围守卫"}
    seen = 0
    for i, line in enumerate(lines):
        out.append(line)
        if line and not line.startswith("#"):
            key = line.split("\t")[0].strip()
            if key in dup_targets and seen < 3:  # 故意留 3 条重复，模拟手改常见情况
                seen += 1
                out.append("  " + line + "   ")  # 前后脏空白
            elif i % 4 == 0:
                out.append("\t" + line)  # 行首多一个制表符
    text = "\n".join(out) + "\n\n   \n"
    with open(dst, "w", encoding="utf-8") as f:
        f.write("\ufeff" + text)  # 带上 BOM，编辑器手存过就是这副样子
    return dst


def run_tidy(src, dst):
    """跑一遍 tidy-dict 的整理流程，产出「整理后」"""
    tidy = _load_module("tidy_dict", TIDY)
    items = tidy.dedupe(tidy.parse(tidy.read_lines(src)))
    with open(dst, "w", encoding="utf-8") as f:
        f.write(tidy.render(items))
    return dst


def _env(dict_path):
    home = tempfile.mkdtemp(prefix="eval-home-")
    env = dict(os.environ)
    env["ZH_GUARD_HOME"] = home
    env["ZH_GUARD_DICT"] = dict_path
    env["ZH_GUARD_STATE_DIR"] = tempfile.mkdtemp(prefix="eval-state-")
    env.pop("ZH_GUARD_OFF", None)
    return env, home


def _run_inject(dict_path, payload):
    env, home = _env(dict_path)
    try:
        proc = subprocess.run(
            [sys.executable, INJECT],
            input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            capture_output=True, env=env, timeout=20,
        )
        try:
            ctx = json.loads(proc.stdout.decode("utf-8"))["hookSpecificOutput"]["additionalContext"]
        except Exception:
            ctx = ""
        return proc.returncode, ctx
    finally:
        shutil.rmtree(home, ignore_errors=True)


def injection_cost(dict_path):
    """L1 注入成本：字符数、估算 token 数、生效词条数。"""
    rc, ctx = _run_inject(dict_path, {"prompt": "hi", "session_id": "eval-cost"})
    tokens, backend = count_tokens(ctx)
    tidy = _load_module("tidy_dict_" + str(abs(hash(dict_path)) % 9999), TIDY)
    items = tidy.dedupe(tidy.parse(tidy.read_lines(dict_path)))
    return {
        "chars": len(ctx),
        "tokens": tokens,
        "token_backend": backend,
        "entries": len([1 for k, _ in items if k == "row"]),
        "hook_exit": rc,
    }


def verdicts(corpus, dict_path):
    """对每条语料跑一次真实的 L2 hook，返回 [(句子, 退出码)]。

    每条语料用不同的 session_id，绕开防循环（同 hash 只断一次）的干扰。
    """
    out = []
    for i, (sentence, _expect) in enumerate(corpus):
        env, home = _env(dict_path)
        try:
            proc = subprocess.run(
                [sys.executable, INSPECT],
                input=json.dumps(
                    {"session_id": "eval-%d" % i, "last_assistant_message": sentence},
                    ensure_ascii=False,
                ).encode("utf-8"),
                capture_output=True, env=env, timeout=20,
            )
            out.append((sentence, proc.returncode))
        finally:
            shutil.rmtree(home, ignore_errors=True)
    return out


def score(corpus, verdicts_out):
    """按语料标注算混淆矩阵。"""
    tp = fp = fn = tn = 0
    for (sentence, expect), (_s, rc) in zip(corpus, verdicts_out):
        predicted = "block" if rc == 2 else "pass"
        if expect == "block" and predicted == "block":
            tp += 1
        elif expect == "pass" and predicted == "pass":
            tn += 1
        elif expect == "pass" and predicted == "block":
            fp += 1
        else:
            fn += 1
    precision = tp / (tp + fp) if (tp + fp) else 1.0
    recall = tp / (tp + fn) if (tp + fn) else 1.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3)}


def parse_cost(dict_path, rounds=200):
    """字典本身的解析耗时（微秒级）：hook 端到端会被解释器启动盖住，单独量。"""
    tidy = _load_module("tidy_dict_pc", TIDY)
    lines = tidy.read_lines(dict_path)

    def once():
        items = tidy.parse(lines)
        return tidy.dedupe(items)

    once()  # 预热，避免第一次的 import/缓存效应
    samples = []
    for _ in range(rounds):
        start = time.perf_counter()
        once()
        samples.append((time.perf_counter() - start) * 1000)
    base = statistics.mean(samples)
    # 顺手记一下光读文件的成本，方便看出大头在哪
    read_samples = []
    for _ in range(rounds):
        start = time.perf_counter()
        tidy.read_lines(dict_path)
        read_samples.append((time.perf_counter() - start) * 1000)
    return {
        "rounds": rounds,
        "parse_mean_ms": base,
        "parse_min_ms": min(samples),
        "read_mean_ms": statistics.mean(read_samples),
    }


def runtime_cost(dict_path, rounds=10):
    """hook 端到端耗时：分别注入干净句和待拦句，取均值与最小值。"""
    inject_payload = {"prompt": "hi", "session_id": "eval-time"}
    inspect_payload = {"session_id": "eval-time-2",
                       "last_assistant_message": "先检查一边通气情况再决定。"}

    def bench(script, payload):
        samples = []
        for i in range(rounds):
            env, home = _env(dict_path)
            payload = dict(payload)
            payload["session_id"] = payload.get("session_id", "s") + "-%d" % i
            start = time.perf_counter()
            try:
                subprocess.run(
                    [sys.executable, script],
                    input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                    capture_output=True, env=env, timeout=20,
                )
            finally:
                shutil.rmtree(home, ignore_errors=True)
            samples.append((time.perf_counter() - start) * 1000)
        return {"mean": statistics.mean(samples), "min": min(samples),
                "stdev": statistics.pstdev(samples)}

    inj = bench(INJECT, inject_payload)
    ins = bench(INSPECT, inspect_payload)
    return {
        "rounds": rounds,
        "inject_mean_ms": inj["mean"],
        "inject_min_ms": inj["min"],
        "inject_stdev_ms": inj["stdev"],
        "inspect_mean_ms": ins["mean"],
        "inspect_min_ms": ins["min"],
        "inspect_stdev_ms": ins["stdev"],
    }


def file_stats(path):
    with open(path, "rb") as raw:
        head = raw.read(3)
    tidy = _load_module("tidy_dict_fs", TIDY)
    items = tidy.parse(tidy.read_lines(path))
    rows = [p for k, p in items if k == "row"]
    keys = [r[0] for r in rows]
    errors, warnings = tidy.check(items)
    return {
        "bytes": os.path.getsize(path),
        "lines": len(rows),
        "unique_keys": len(set(keys)),
        "duplicates": len(keys) - len(set(keys)),
        "has_bom": head == b"\xef\xbb\xbf",
        "lint_errors": len(errors),
        "lint_warnings": len(warnings),
    }


def delta(before, after):
    return after - before


def row(label, before, after, unit="", better="lower"):
    if before == after:
        mark = "一致" if better == "same" else "持平"
    elif better == "same":
        mark = "应为一致（实际不一致）"
    elif (better == "lower") == (after < before):
        mark = "OK"
    else:
        mark = "变差"
    judge = "" if after == before else ("↓" if after < before else "↑")
    return "%-22s %12s %12s %10s  %s" % (
        label, "%s%s" % (before, unit), "%s%s" % (after, unit), "%+d%s %s" % (
            delta(before, after), unit, judge), mark)


def main():
    ap = argparse.ArgumentParser(description="tidy-dict 前后对比评测")
    ap.add_argument("--json", action="store_true", help="输出 JSON 指标而不是表格")
    ap.add_argument("--rounds", type=int, default=10, help="计时轮数（默认 10）")
    ap.add_argument("--corpus", help="外部语料文件：句子<TAB>block|pass")
    ap.add_argument("--source", default=BUNDLED, help="基准字典（默认自带字典）")
    args = ap.parse_args()

    corpus = load_corpus(args.corpus)
    tmp = tempfile.mkdtemp(prefix="eval-dict-")
    try:
        with open(args.source, encoding="utf-8") as f:
            clean_text = f.read()
        before_path = build_dirty_copy(clean_text, os.path.join(tmp, "before.tsv"))
        after_path = run_tidy(before_path, os.path.join(tmp, "after.tsv"))

        fs_before, fs_after = file_stats(before_path), file_stats(after_path)
        co_before, co_after = injection_cost(before_path), injection_cost(after_path)
        v_before, v_after = verdicts(corpus, before_path), verdicts(corpus, after_path)
        sc_before, sc_after = score(corpus, v_before), score(corpus, v_after)
        rt_before = runtime_cost(before_path, rounds=args.rounds)
        rt_after = runtime_cost(after_path, rounds=args.rounds)
        pc_before = parse_cost(before_path)
        pc_after = parse_cost(after_path)

        identical = [v[1] for v in v_before] == [v[1] for v in v_after]

        if args.json:
            print(json.dumps({
                "corpus_size": len(corpus),
                "file": {"before": fs_before, "after": fs_after},
                "injection": {"before": co_before, "after": co_after},
                "detection": {"before": sc_before, "after": sc_after,
                              "identical": identical},
                "runtime_ms": {"before": rt_before, "after": rt_after},
                "parse_ms": {"before": pc_before, "after": pc_after},
            }, ensure_ascii=False, indent=2))
            return

        print("tidy-dict 评测：整理前 vs 整理后")
        print("语料 %d 条（%d 该拦 / %d 该放行），计时 %d 轮，token 后端：%s"
              % (len(corpus),
                 len([c for c in corpus if c[1] == "block"]),
                 len([c for c in corpus if c[1] == "pass"]),
                 args.rounds, co_after["token_backend"]))
        print("")
        print("%-22s %12s %12s %s" % ("指标", "整理前", "整理后", "变化"))
        print("-" * 68)
        print(row("字典行数", fs_before["lines"], fs_after["lines"], better="lower"))
        print(row("唯一词条", fs_before["unique_keys"], fs_after["unique_keys"], better="same"))
        print(row("重复词条", fs_before["duplicates"], fs_after["duplicates"], better="lower"))
        print(row("体检错/警告", fs_before["lint_errors"] + fs_before["lint_warnings"],
                  fs_after["lint_errors"] + fs_after["lint_warnings"], better="lower"))
        print(row("文件字节", fs_before["bytes"], fs_after["bytes"]))
        print("-" * 68)
        print(row("注入字符", co_before["chars"], co_after["chars"], better="lower"))
        print(row("注入 token", co_before["tokens"], co_after["tokens"], better="lower"))
        print(row("注入词条", co_before["entries"], co_after["entries"], better="lower"))
        print("-" * 68)
        print(row("L1 耗时均值 ms", round(rt_before["inject_mean_ms"], 1),
                  round(rt_after["inject_mean_ms"], 1), better="lower"))
        print(row("L1 耗时最快 ms", round(rt_before["inject_min_ms"], 1),
                  round(rt_after["inject_min_ms"], 1), better="lower"))
        print(row("L2 耗时均值 ms", round(rt_before["inspect_mean_ms"], 1),
                  round(rt_after["inspect_mean_ms"], 1), better="lower"))
        print(row("L2 耗时最快 ms", round(rt_before["inspect_min_ms"], 1),
                  round(rt_after["inspect_min_ms"], 1), better="lower"))
        print(row("字典解析均值 ms", round(pc_before["parse_mean_ms"], 3),
                  round(pc_after["parse_mean_ms"], 3), better="lower"))
        print("（端到端含 python 解释器启动，噪声 ±%.0f ms，看成组对比；"
              "字典解析才是整理真正影响的那部分）"
              % max(rt_before["inject_stdev_ms"], rt_after["inject_stdev_ms"]))
        print("-" * 68)
        print("%-22s %12s %12s" % ("准确率 precision", sc_before["precision"], sc_after["precision"]))
        print("%-22s %12s %12s" % ("召回 recall", sc_before["recall"], sc_after["recall"]))
        print("%-22s %12s %12s" % ("F1", sc_before["f1"], sc_after["f1"]))
        print("%-22s %12s" % ("逐条判定完全一致", "—"), end=" ")
        print("是" if identical else "否")
        print("")
        ok = identical and co_after["tokens"] <= co_before["tokens"]
        print("结论：整理 %s。行为%s等价，注入成本%s，字典解析 %.3f→%.3f ms。"
              % ("通过" if ok else "需要修",
                 "完全" if identical else "不",
                 "不反弹" if co_after["tokens"] <= co_before["tokens"] else "反而变大",
                 pc_before["parse_mean_ms"], pc_after["parse_mean_ms"]))
        print("负结果也记一下：想靠去重省 token 是省不出来的——加载层本来就按唯一键合并，"
              "整理改的是文件卫生和可读性，不是运行开销。")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
