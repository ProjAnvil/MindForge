#!/usr/bin/env python3
"""zh-guard 测试套件（MindForge 插件版）。

运行：python3 test_zh_guard.py
退出码 0 表示全部通过。
每个测试用真实 stdin JSON 驱动 hook 脚本，验证端到端行为。
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
INJECT = os.path.join(HERE, "inject.py")
INSPECT = os.path.join(HERE, "inspect.py")
PY = sys.executable

FAILURES = []


def run_hook(script, payload, env_extra=None):
    env = dict(os.environ)
    env.pop("ZH_GUARD_OFF", None)
    env.pop("ZH_GUARD_DICT", None)
    env.pop("ZH_GUARD_HOME", None)
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run(
        [PY, script],
        input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        capture_output=True,
        env=env,
        timeout=20,
    )
    return proc


def check(name, condition, detail=""):
    if condition:
        print("PASS  " + name)
    else:
        print("FAIL  " + name + ("  | " + detail if detail else ""))
        FAILURES.append(name)


def temp_env():
    """隔离状态目录与用户目录，避免污染真实会话状态。"""
    state_dir = tempfile.mkdtemp(prefix="zh-guard-test-")
    home_dir = tempfile.mkdtemp(prefix="zh-guard-home-")
    env = {
        "ZH_GUARD_STATE_DIR": state_dir,
        "ZH_GUARD_HOME": home_dir,
    }
    return env, state_dir


def cleanup(state_dir):
    shutil.rmtree(state_dir, ignore_errors=True)


def test_l1_injection_format():
    env, sd = temp_env()
    proc = run_hook(INJECT, {"prompt": "hi", "session_id": "s1"}, env)
    ok = proc.returncode == 0
    out = {}
    try:
        out = json.loads(proc.stdout.decode("utf-8"))
    except Exception:
        ok = False
    ctx = out.get("hookSpecificOutput", {}).get("additionalContext", "")
    check("L1 输出合法 JSON 且 continue=true", ok and out.get("continue") is True, proc.stdout[:200])
    check("L1 注入包含混排规范", "禁止字面直译" in ctx, ctx[:200])
    check("L1 注入包含字典定译（消融实验）", "消融实验" in ctx)
    check("L1 注入包含新增词条（地面真实）", "地面真实" in ctx)


def test_l2_blocks_translationese():
    env, sd = temp_env()
    msg = "我们对网络做病灶实验，发现幽灵词元的问题。"
    proc = run_hook(INSPECT, {"session_id": "t2", "last_assistant_message": msg}, env)
    body = proc.stdout.decode("utf-8") + proc.stderr.decode("utf-8")
    check("L2 命中直译词时退出码为 2", proc.returncode == 2, "rc=%d" % proc.returncode)
    check("L2 反馈包含修正指引（消融实验）", "消融实验" in body, body[:300])


def test_l2_blocks_new_entries():
    env, sd = temp_env()
    proc = run_hook(
        INSPECT,
        {"session_id": "t2b", "last_assistant_message": "该进程的死因是 OOM，机器人胳膊的病症也很明显。"},
        env,
    )
    check("L2 拦截新增词条（死因/机器人胳膊/病症）", proc.returncode == 2, "rc=%d" % proc.returncode)
    proc2 = run_hook(
        INSPECT,
        {"session_id": "t2c", "last_assistant_message": "先把接口钉死，再实现范围守卫。"},
        env,
    )
    body = proc2.stdout.decode("utf-8") + proc2.stderr.decode("utf-8")
    check("L2 拦截钉死/范围守卫", proc2.returncode == 2 and "敲定" in body and "作用域守卫" in body,
          body[:200])
    proc3 = run_hook(
        INSPECT,
        {"session_id": "t2d", "last_assistant_message": "这里还有一个遗留缺口需要补齐。"},
        env,
    )
    body3 = proc3.stdout.decode("utf-8") + proc3.stderr.decode("utf-8")
    check("L2 拦截机器腔措辞（遗留缺口）",
          proc3.returncode == 2 and "剩下的待办" in body3, body3[:200])


def test_l2_passes_clean_message():
    env, sd = temp_env()
    proc = run_hook(
        INSPECT,
        {"session_id": "t3", "last_assistant_message": "重试逻辑已修复，重复请求从 24 次降到 7 次。"},
        env,
    )
    check("L2 干净中文直接放行（exit 0）", proc.returncode == 0, "rc=%d" % proc.returncode)


def test_l2_ignores_code_blocks():
    env, sd = temp_env()
    msg = "代码如下：\n```python\n# 病灶实验 demo\nrun_ablation()\n```\n上面的脚本演示了消融实验。"
    proc = run_hook(INSPECT, {"session_id": "t4", "last_assistant_message": msg}, env)
    check("L2 忽略代码块内的术语", proc.returncode == 0, "rc=%d" % proc.returncode)


def test_l2_ignores_quoted_mentions():
    """提及（引号内）与使用（正文）的区分。"""
    env, sd = temp_env()
    msg = "字典里有一条：「幽灵词元」→ghost token。这个直译词要避免。"
    proc = run_hook(INSPECT, {"session_id": "t8", "last_assistant_message": msg}, env)
    check("L2 忽略「」引号内提及的术语", proc.returncode == 0, "rc=%d" % proc.returncode)
    msg2 = "模型存在幽灵词元问题，需要处理。"
    proc2 = run_hook(INSPECT, {"session_id": "t9", "last_assistant_message": msg2}, env)
    check("L2 仍拦截正文中的术语使用", proc2.returncode == 2, "rc=%d" % proc2.returncode)
    msg3 = "字典里有一条：\u201c幽灵词元\u201d→ghost token。"
    proc3 = run_hook(INSPECT, {"session_id": "t10", "last_assistant_message": msg3}, env)
    check("L2 忽略“”引号内提及的术语", proc3.returncode == 0, "rc=%d" % proc3.returncode)


def test_l2_failopen_on_garbage_stdin():
    env, sd = temp_env()
    proc = subprocess.run(
        [PY, INSPECT],
        input=b"not json at all {{{",
        capture_output=True,
        env={**os.environ, **env},
        timeout=20,
    )
    check("L2 收到非法输入时放行（fail-open）", proc.returncode == 0, "rc=%d" % proc.returncode)
    proc2 = subprocess.run(
        [PY, INJECT],
        input=b"",
        capture_output=True,
        env={**os.environ, **env},
        timeout=20,
    )
    check("L1 收到空输入时放行（fail-open）", proc2.returncode == 0, "rc=%d" % proc2.returncode)


def test_l2_missing_dict_failopen():
    env, sd = temp_env()
    env["ZH_GUARD_DICT"] = os.path.join(sd, "no-such-dict.tsv")
    proc = run_hook(INSPECT, {"session_id": "t5", "last_assistant_message": "病灶实验"}, env)
    check("L2 字典缺失时放行（fail-open）", proc.returncode == 0, "rc=%d" % proc.returncode)


def test_loop_protection_same_message():
    env, sd = temp_env()
    msg = "我们又做了一次病灶实验。"
    p1 = run_hook(INSPECT, {"session_id": "t6", "last_assistant_message": msg}, env)
    p2 = run_hook(INSPECT, {"session_id": "t6", "last_assistant_message": msg}, env)
    check("同一消息第二次不再阻断（防循环）", p1.returncode == 2 and p2.returncode == 0,
          "rc1=%d rc2=%d" % (p1.returncode, p2.returncode))


def test_kill_switch():
    env, sd = temp_env()
    env["ZH_GUARD_OFF"] = "1"
    proc = run_hook(INSPECT, {"session_id": "t7", "last_assistant_message": "病灶实验"}, env)
    check("ZH_GUARD_OFF=1 时 L2 停用", proc.returncode == 0, "rc=%d" % proc.returncode)
    proc2 = run_hook(INJECT, {"prompt": "hi", "session_id": "t7"}, env)
    check("ZH_GUARD_OFF=1 时 L1 停用", proc2.returncode == 0 and proc2.stdout.strip() == b"",
          proc2.stdout[:100])


def test_user_dict_merge():
    """用户目录字典：自加词条生效 + 同名词条不再被旧副本锁死（见版本同步）。"""
    env, sd = temp_env()
    home = tempfile.mkdtemp(prefix="zh-guard-home-")
    env["ZH_GUARD_HOME"] = home
    with open(os.path.join(home, "terminology.tsv"), "w", encoding="utf-8") as f:
        f.write("用户生造词\t正确写法\t测试新增\n")
    try:
        proc = run_hook(
            INSPECT,
            {"session_id": "t11", "last_assistant_message": "这里出现了用户生造词。"},
            env,
        )
        check("用户目录新增词条被 L2 拦截", proc.returncode == 2, "rc=%d" % proc.returncode)
        proc2 = run_hook(INJECT, {"prompt": "hi", "session_id": "t12"}, env)
        ctx = json.loads(proc2.stdout.decode("utf-8"))["hookSpecificOutput"]["additionalContext"]
        check("L1 负面清单含用户新增词条", "用户生造词" in ctx, ctx[-200:])
        check("L1 负面清单给出期望写法（箭头→）", "→" in ctx, ctx[-200:])
        check("L1 注入措辞规则（第 5 条）", "剩下的待办" in ctx, ctx[-200:])
    finally:
        shutil.rmtree(home, ignore_errors=True)


def test_dict_version_sync():
    """字典版本同步：@sync 变化时刷新自带词条，但保留用户自加的词条。

    没有这套机制，出厂时被复制走的旧写法会把后续的修正永久挡在外面。
    """
    env, sd = temp_env()
    home = tempfile.mkdtemp(prefix="zh-guard-home-")
    env["ZH_GUARD_HOME"] = home
    user_dict = os.path.join(home, "terminology.tsv")
    with open(user_dict, "w", encoding="utf-8") as f:
        f.write(
            "# 用户旧字典（无 @sync 标记，模拟旧版本安装）\n"
            "下一刀\t下一个削减项\t旧写法\n"
            "用户自加词\t用户自己的写法\t用户补充\n"
        )
    try:
        run_hook(INJECT, {"prompt": "hi", "session_id": "t17"}, env)
        with open(user_dict, encoding="utf-8") as f:
            content = f.read()
        check("版本落后时把新版自带词条同步到用户字典",
              "下一处可以精简的部分" in content, content[:300])
        check("用户自加词条在同步后保留", "用户自加词\t用户自己的写法" in content, content[:300])
        check("同步后用户字典带上 @sync 标记", "# @sync" in content, content[:300])
        proc = run_hook(
            INSPECT,
            {"session_id": "t18", "last_assistant_message": "下一刀砍在推理预算上。"},
            env,
        )
        body = proc.stdout.decode("utf-8") + proc.stderr.decode("utf-8")
        check("修正后的期望写法真正进入 L2 提示（不是旧写法）",
              proc.returncode == 2 and "下一处可以精简的部分" in body
              and "下一个削减项" not in body, body[:300])
        # 版本号一致时不应再改动用户字典
        with open(user_dict, "a", encoding="utf-8") as f:
            f.write("手动加的行\t手动写法\t手工补充\n")
        run_hook(INJECT, {"prompt": "hi", "session_id": "t19"}, env)
        with open(user_dict, encoding="utf-8") as f:
            content2 = f.read()
        check("@sync 一致时不动用户字典", "手动加的行\t手动写法" in content2, content2[-200:])
    finally:
        shutil.rmtree(home, ignore_errors=True)


def test_off_file_in_guard_home():
    env, sd = temp_env()
    home = tempfile.mkdtemp(prefix="zh-guard-home-")
    env["ZH_GUARD_HOME"] = home
    open(os.path.join(home, "OFF"), "w").close()
    try:
        proc = run_hook(INSPECT, {"session_id": "t13", "last_assistant_message": "病灶实验"}, env)
        check("ZH_GUARD_HOME/OFF 文件停用 L2", proc.returncode == 0, "rc=%d" % proc.returncode)
    finally:
        shutil.rmtree(home, ignore_errors=True)


def test_install_time_migration():
    """安装迁移：首次运行把插件自带字典复制到 ZH_GUARD_HOME，之后不覆盖。"""
    env, sd = temp_env()
    home = tempfile.mkdtemp(prefix="zh-guard-home-")
    env["ZH_GUARD_HOME"] = home
    try:
        user_dict = os.path.join(home, "terminology.tsv")
        check("迁移前用户字典不存在", not os.path.exists(user_dict))
        run_hook(INJECT, {"prompt": "hi", "session_id": "t14"}, env)
        check("首次运行后字典迁移到 ZH_GUARD_HOME", os.path.exists(user_dict))
        with open(user_dict, encoding="utf-8") as f:
            content = f.read()
        check("迁移内容含插件词条（病灶实验）", "病灶实验" in content)
        with open(user_dict, "a", encoding="utf-8") as f:
            f.write("迁移后新增词\t正确写法\t用户补充\n")
        run_hook(INJECT, {"prompt": "hi", "session_id": "t15"}, env)
        with open(user_dict, encoding="utf-8") as f:
            content2 = f.read()
        check("已有用户字典不被覆盖（迁移后新增词保留）", "迁移后新增词" in content2)
        proc = run_hook(
            INSPECT,
            {"session_id": "t16", "last_assistant_message": "这里出现了迁移后新增词。"},
            env,
        )
        check("迁移后的用户词条参与 L2 检测", proc.returncode == 2, "rc=%d" % proc.returncode)
    finally:
        shutil.rmtree(home, ignore_errors=True)


def test_regex_entries():
    """正则词条：第N刀 整类拦截，无效正则跳过。"""
    env, sd = temp_env()
    cases = [
        ("按照计划，第36刀砍在推理预算上。", 2, "第36刀"),
        ("第 128 刀之后预算见底了。", 2, "第 128 刀"),
        ("下一步削减测试预算。", 0, ""),
        ("我们继续做消融实验。", 0, ""),
    ]
    for i, (msg, want_rc, want_hit) in enumerate(cases):
        proc = run_hook(INSPECT, {"session_id": "t-re%d" % i, "last_assistant_message": msg}, env)
        check("正则词条：「%s」期望 rc=%d" % (msg[:14], want_rc),
              proc.returncode == want_rc, "rc=%d" % proc.returncode)
        if want_rc == 2 and want_hit:
            body = proc.stdout.decode("utf-8") + proc.stderr.decode("utf-8")
            check("阻断理由含实际命中文本（%s）" % want_hit, want_hit in body, body[:200])


def test_regex_invalid_pattern_skipped():
    """用户字典里的无效正则不崩溃、不拦截（fail-open）。"""
    env, sd = temp_env()
    home = tempfile.mkdtemp(prefix="zh-guard-home-")
    env["ZH_GUARD_HOME"] = home
    with open(os.path.join(home, "terminology.tsv"), "w", encoding="utf-8") as f:
        f.write("re:第[刀\t第 N 次削减\t未闭合括号的坏正则\n")
    try:
        proc = run_hook(
            INSPECT,
            {"session_id": "t-badre", "last_assistant_message": "正常的一句中文，第36刀应该被插件正则拦截。"},
            env,
        )
        check("无效正则跳过后仍由插件有效词条拦截", proc.returncode == 2, "rc=%d" % proc.returncode)
    finally:
        shutil.rmtree(home, ignore_errors=True)


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        try:
            t()
        except Exception as exc:
            check(t.__name__ + "（异常）", False, repr(exc))
        finally:
            # temp_env 创建的状态目录在函数局部，统一在结尾清理代价高；
            # 用系统临时目录自清理策略，测试里不强制删除。
            pass
    print("")
    if FAILURES:
        print("失败 %d 项：%s" % (len(FAILURES), ", ".join(FAILURES)))
        sys.exit(1)
    print("全部通过（%d 项测试）" % len(tests))
    sys.exit(0)


if __name__ == "__main__":
    main()
