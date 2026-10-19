#!/usr/bin/env python3
"""zh-guard 方案成本评测：装了它，多花多少 token、多等多少毫秒。

三个对照组：

    基线      完全没装这套东西：不注入、不检测，成本恒为 0
    空字典    hook 装了，但字典全空：量的是「规则文本 + hook 引擎」的成本
    完整字典  hook + 现在的字典：前两者的成本 + 字典本身的边际成本

这样拆开，才能回答「这份字典到底占了多少」——因为即使字典一张词条都没有，
L1 那 5 条规则文本每轮也照注入不误。

用法：
    python3 eval-zh-guard.py                  # 打印对比表
    python3 eval-zh-guard.py --json           # 机器可读（CI diff）
    python3 eval-zh-guard.py --rounds 20      # 计时轮数（默认 15）
    python3 eval-zh-guard.py --turns 10 50    # 折算成几轮对话的累计 token

token 计数优先 tiktoken，没装就用标注清楚的估算，表头写明用的是哪个。
耗时分成「端到端」和「净耗时」：端到端里绝大部分是 python 解释器启动，
净耗时 = 端到端 - 裸解释器启动基准。
"""
import argparse
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

CJK = r"[\u3400-\u9fff\uf900-\ufaff]"

FLAGGED = "这次我们又做了一遍病灶实验，结论没变。"
CLEAN_SAMPLE = "重试次数从 24 次降到 7 次，抖动消失了，不用再灰度观察。"

# 一次典型的技术类回答，用来估算「被拦之后重写整条回复」的代价
SAMPLE_REPLY = (
    "看了下这个模块的调用链，问题出在重试(tell me more)那段：失败后会立刻重发，"
    "没有退避，于是在下游抖动时把请求放大了三倍。改法有两点，一是加指数退避并带上抖动，"
    "二是在入口做幂等，重复的请求直接返回上一次的结果。改完本地压了三轮，"
    "错误率从 4.2% 降到 0.3%，p99 也从 800ms 回到 120ms。"
)
MAX_BLOCKS_PER_WINDOW = 3  # 与 inspect.py 的防循环上限一致：10 分钟最多拦 3 次


def count_tokens(text):
    """返回 (token 数, 后端)。"""
    try:
        import tiktoken  # type: ignore
        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text)), "tiktoken/cl100k_base"
    except Exception:
        cjk_len = len(re.findall(CJK, text))
        words = re.findall(r"[A-Za-z0-9_]+", text)
        return int(cjk_len + len(words) * 1.3 + 0.999), "estimate(cjk+1.3*words)"


def empty_dict(dst):
    """空字典：只有注释，一条词条都没有。"""
    with open(dst, "w", encoding="utf-8") as f:
        f.write("# 空对照组：一张词条都没有，用来量 hook 引擎本身的成本\n")
    return dst


def full_dict(dst):
    """完整字典：当前自带字典的原样副本。"""
    shutil.copyfile(BUNDLED, dst)
    return dst


def baseline():
    """没装这套东西时的成本：什么都不跑，恒为 0。"""
    return {"chars": 0, "tokens": 0, "entries": 0, "ms": 0.0,
            "ctx": "", "rc": 0}


def _home():
    return tempfile.mkdtemp(prefix="eval-zg-home-")


def _env(dict_path):
    env = dict(os.environ)
    env["ZH_GUARD_HOME"] = _home()
    env["ZH_GUARD_STATE_DIR"] = tempfile.mkdtemp(prefix="eval-zg-state-")
    env["ZH_GUARD_DICT"] = dict_path
    env.pop("ZH_GUARD_OFF", None)
    return env


def _run(script, payload, dict_path):
    env = _env(dict_path)
    home = env["ZH_GUARD_HOME"]
    start = time.perf_counter()
    try:
        proc = subprocess.run(
            [sys.executable, script],
            input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            capture_output=True, env=env, timeout=30,
        )
    finally:
        shutil.rmtree(home, ignore_errors=True)
    return proc, (time.perf_counter() - start) * 1000


def inject_cost(dict_path, rounds=1):
    """L1 注入成本：字符、token、词条数，以及一次执行的墙钟时间。"""
    samples = []
    ctx = ""
    rc = 0
    for i in range(max(1, rounds)):
        proc, ms = _run(INJECT, {"prompt": "hi", "session_id": "eval-%d" % i}, dict_path)
        samples.append(ms)
        rc = proc.returncode
        try:
            ctx = json.loads(proc.stdout.decode("utf-8"))["hookSpecificOutput"]["additionalContext"]
        except Exception:
            ctx = ""
    tokens, backend = count_tokens(ctx)
    return {
        "chars": len(ctx),
        "tokens": tokens,
        "token_backend": backend,
        "entries": len(_dict_keys(dict_path)),
        "ctx": ctx,
        "rc": rc,
        "ms": statistics.mean(samples),
        "ms_min": min(samples),
    }


def _dict_keys(dict_path):
    keys = []
    with open(dict_path, encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip().lstrip("\ufeff")
            if not line or line.startswith("#"):
                continue
            key = line.split("\t")[0].strip()
            if key:
                keys.append(key)
    return list(dict.fromkeys(keys))


def verdict(dict_path, sentence, session="v"):
    """跑一次真实的 L2 hook，返回退出码（0 放行 / 2 拦截）。"""
    proc, _ms = _run(INSPECT,
                     {"session_id": session, "last_assistant_message": sentence},
                     dict_path)
    return proc.returncode


def timing(dict_path, rounds=15):
    """hook 端到端耗时：L1 注入、L2 干净回复、L2 命中回复。"""
    def bench(script, payload, tag):
        samples = []
        for i in range(rounds):
            payload = dict(payload)
            payload["session_id"] = "%s-%d" % (tag, i)
            _proc, ms = _run(script, payload, dict_path)
            samples.append(ms)
        return statistics.mean(samples)

    return {
        "rounds": rounds,
        "inject_ms": bench(INJECT, {"prompt": "hi", "session_id": "i"}, "inj"),
        "inspect_clean_ms": bench(
            INSPECT, {"session_id": "c", "last_assistant_message": CLEAN_SAMPLE}, "cln"),
        "inspect_hit_ms": bench(
            INSPECT, {"session_id": "h", "last_assistant_message": FLAGGED}, "hit"),
    }


def interception_cost(dict_path):
    """单次拦截的代价：那条被退回的回复白写了，还得重写一遍。

    = 被丢弃的回复 + 重写的回复 + L2 返回的重写指令。这是方案里最贵的一项，
    比注入那几百 token 和几毫秒都重要，所以必须单独量。
    """
    env = _env(dict_path)
    home = env["ZH_GUARD_HOME"]
    try:
        proc = subprocess.run(
            [sys.executable, INSPECT],
            input=json.dumps({"session_id": "ic", "last_assistant_message": FLAGGED},
                             ensure_ascii=False).encode("utf-8"),
            capture_output=True, env=env, timeout=30,
        )
    finally:
        shutil.rmtree(home, ignore_errors=True)
    instruction = proc.stderr.decode("utf-8").strip()
    ins_tokens, _ = count_tokens(instruction)
    reply_tokens, _ = count_tokens(SAMPLE_REPLY)
    return {
        "blocked": proc.returncode == 2,
        "instruction_chars": len(instruction),
        "instruction_tokens": ins_tokens,
        "reply_tokens": reply_tokens,
        "cost_per_block_tokens": 2 * reply_tokens + ins_tokens,
        "worst_window_tokens": MAX_BLOCKS_PER_WINDOW * (2 * reply_tokens + ins_tokens),
    }


def python_startup_ms(rounds=15):
    """裸解释器启动基准：hook 端到端里扣掉它，剩下的才是我们自己的代码。"""
    samples = []
    for _ in range(rounds):
        start = time.perf_counter()
        subprocess.run([sys.executable, "-c", "pass"], capture_output=True, timeout=30)
        samples.append((time.perf_counter() - start) * 1000)
    return statistics.mean(samples)


def net_ms(end_to_end_ms, startup_ms):
    return max(0.0, end_to_end_ms - startup_ms)


def measure(rounds=15):
    tmp = tempfile.mkdtemp(prefix="eval-zg-arm-")
    try:
        empty = empty_dict(os.path.join(tmp, "empty.tsv"))
        full = full_dict(os.path.join(tmp, "full.tsv"))
        return {
            "baseline": baseline(),
            "empty": inject_cost(empty, rounds=rounds),
            "full": inject_cost(full, rounds=rounds),
            "timing": timing(full, rounds=rounds),
            "interception": interception_cost(full),
            "startup_ms": python_startup_ms(rounds=rounds),
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def table(m, turns):
    b, e, f = m["baseline"], m["empty"], m["full"]
    t, startup = m["timing"], m["startup_ms"]
    backend = f["token_backend"]
    print("zh-guard 方案成本评测")
    print("token 后端：%s ｜ 计时：%d 轮取均值 ｜ 裸解释器启动 %.0f ms"
          % (backend, t["rounds"], startup))
    print("")
    print("%-26s %14s %14s %14s" % ("每轮输入成本", "基线(没装)", "空字典", "完整字典"))
    print("-" * 72)
    print("%-26s %14s %14s %14s" % ("注入字符", b["chars"], e["chars"], f["chars"]))
    print("%-26s %14s %14s %14s" % ("注入 token", b["tokens"], e["tokens"], f["tokens"]))
    print("%-26s %14s %14s %14s" % ("词条数", b["entries"], e["entries"], f["entries"]))
    print("%-26s %14s %14s %14s" % (
        "字典带来的边际 token", "—", 0, f["tokens"] - e["tokens"]))
    print("-" * 72)
    for turns_n in turns:
        print("%-26s %14s %14s %14s" % (
            "%d 轮对话累计 token" % turns_n,
            b["tokens"] * turns_n, e["tokens"] * turns_n, f["tokens"] * turns_n))
    print("-" * 72)
    print("%-26s %14s %14s %14s" % (
        "L1 端到端 ms", "0.0", "%.1f" % e["ms"], "%.1f" % f["ms"]))
    print("%-26s %14s %14s %14s" % (
        "L1 净耗时 ms（扣启动时）", "0.0", "%.1f" % net_ms(e["ms"], startup),
        "%.1f" % net_ms(f["ms"], startup)))
    print("%-26s %14s %14s %14s" % (
        "L2 干净回复 ms", "0.0", "≈同上", "%.1f" % t["inspect_clean_ms"]))
    print("%-26s %14s %14s %14s" % (
        "L2 命中并拦截 ms", "0.0", "≈同上", "%.1f" % t["inspect_hit_ms"]))
    print("%-26s %14s %14s %14s" % (
        "L2 净耗时 ms", "0.0", "≈同上",
        "%.1f" % net_ms(t["inspect_clean_ms"], startup)))
    ic = m["interception"]
    print("-" * 72)
    print("%-26s %14s %14s %14s" % (
        "单次拦截的重写指令 token", "0", "0", ic["instruction_tokens"]))
    print("%-26s %14s %14s %14s" % (
        "单次拦截代价 token（重写一次回复）", "0", "0", ic["cost_per_block_tokens"]))
    print("%-26s %14s %14s %14s" % (
        "最坏窗口（10 分钟 3 次）token", "0", "0", ic["worst_window_tokens"]))
    print("")
    print("被拦一次的代价 ≈ 那条回复白写一遍再重写一遍（%d token）+ 指令 %d token，"
          "这是整套方案最贵的一项。"
          % (2 * ic["reply_tokens"], ic["instruction_tokens"]))
    print("每轮的额外等待：约 %.0f ms（L1）+ %.0f ms（L2）＝ %.0f ms，"
          "其中大头是解释器启动，本地 SSD 上基本无感。"
          % (t["inject_ms"], t["inspect_clean_ms"],
             t["inject_ms"] + t["inspect_clean_ms"]))
    print("想省就按顺序来：先让模型少踩词（注入规则 + MCP 查词），"
          "再砍注入文本（%d token/轮），几毫秒那个量级不值得动。" % f["tokens"])


def main():
    ap = argparse.ArgumentParser(description="zh-guard 方案成本评测")
    ap.add_argument("--json", action="store_true", help="输出 JSON 指标")
    ap.add_argument("--rounds", type=int, default=15, help="计时轮数")
    ap.add_argument("--turns", type=int, nargs="*", default=[10, 50],
                    help="折算成几轮对话的累计 token")
    args = ap.parse_args()

    m = measure(rounds=args.rounds)
    if args.json:
        print(json.dumps(m, ensure_ascii=False, indent=2))
        return
    table(m, args.turns)


if __name__ == "__main__":
    main()
