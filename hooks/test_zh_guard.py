#!/usr/bin/env python3
"""zh-guard 测试套件（MindForge 插件版）。

运行：python3 test_zh_guard.py
退出码 0 表示全部通过。
每个测试用真实 stdin JSON 驱动 hook 脚本，验证端到端行为。
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
INJECT = os.path.join(HERE, "inject.py")
INSPECT = os.path.join(HERE, "inspect.py")
PY = sys.executable

FAILURES = []


def run_hook(script, payload, env_extra=None, args=None):
    env = dict(os.environ)
    env.pop("ZH_GUARD_OFF", None)
    env.pop("ZH_GUARD_DICT", None)
    env.pop("ZH_GUARD_HOME", None)
    env.pop("ZH_GUARD_LEGACY_HOME", None)
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run(
        [PY, script] + (args or []),
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
    check("L1 emits valid JSON with continue=true", ok and out.get("continue") is True, proc.stdout[:200])
    check("L1 includes mixed-language writing guidance", "禁止字面直译" in ctx, ctx[:200])
    check("L1 includes plain-language investigation guidance",
          "病灶实验→排查原因的实验" in ctx, ctx[:500])
    check("L1 does not recommend obsolete terminology", "消融" not in ctx, ctx[:500])
    check("L1 includes the added ground-truth entry", "地面真实" in ctx)
    check("Manual glossary guidance describes optional draft checks",
          "mindforge_check_text" in ctx and "草稿" in ctx and "复查" in ctx, ctx[-600:])


def test_injected_prompts_reference_exported_tool_names():
    with tempfile.TemporaryDirectory(prefix="zh-tool-prompts-") as base:
        dictionary = os.path.join(base, "dict.tsv")
        with open(dictionary, "w", encoding="utf-8") as stream:
            for index in range(51):
                stream.write("本地词%d\t建议%d\t本项目含义\n" % (index, index))
        env = {
            "ZH_GUARD_DICT": dictionary,
            "ZH_GUARD_HOME": os.path.join(base, "home"),
            "ZH_GUARD_LEGACY_HOME": os.path.join(base, "legacy"),
            "ZH_GUARD_STATE_DIR": os.path.join(base, "state"),
        }
        server = run_hook(os.path.join(HERE, "term-dict-server.py"), {
            "jsonrpc": "2.0", "id": 1, "method": "tools/list",
        }, env)
        exported = {tool["name"] for tool in json.loads(server.stdout)["result"]["tools"]}
        injection = run_hook(INJECT, {"prompt": "hi", "session_id": "names"}, env)
        context = json.loads(injection.stdout)["hookSpecificOutput"]["additionalContext"]
        check("Dictionary overflow guidance uses the exported lookup tool name",
              "mindforge_lookup_term" in context, context[-600:])
        check("Dictionary maintenance guidance requires workspace cwd and names the init tool",
              "mindforge_init_dict" in context and "mindforge_add_term" in context
              and "必须传绝对路径 cwd" in context, context[-700:])
        stop = run_hook(INSPECT, {
            "session_id": "names", "last_assistant_message": "请处理本地词0。",
        }, env)
        reason = json.loads(stop.stdout)["reason"]
        for label, prompt in [("UserPromptSubmit", context), ("Stop", reason)]:
            names = set(re.findall(r"\bmindforge_[a-z_]+\b", prompt))
            check("%s output references only exported mindforge tools" % label,
                  bool(names) and names <= exported, str(names))
            check("%s output contains no legacy tool names" % label,
                  re.search(r"\b(?:lookup_term|check_text|add_term)\b", prompt) is None,
                  prompt[-500:])


def test_l2_blocks_translationese():
    env, sd = temp_env()
    msg = "我们对网络做病灶实验，发现幽灵词元的问题。"
    proc = run_hook(INSPECT, {"session_id": "t2", "last_assistant_message": msg}, env)
    body = proc.stdout.decode("utf-8") + proc.stderr.decode("utf-8")
    check("L2 exits with status 2 for matching expressions", proc.returncode == 2, "rc=%d" % proc.returncode)
    check("L2 feedback includes plain-language investigation guidance",
          "排查原因的实验" in body and "消融" not in body, body[:300])
    out = json.loads(proc.stdout)
    check("Claude Stop requests continuation with block instead of continue:false",
          out.get("decision") == "block" and out.get("continue") is not False, str(out)[:200])


def test_l2_blocks_new_entries():
    env, sd = temp_env()
    proc = run_hook(
        INSPECT,
        {"session_id": "t2b", "last_assistant_message": "该进程的死因是 OOM，机器人胳膊的病症也很明显。"},
        env,
    )
    check("L2 detects the added process and robotics entries", proc.returncode == 2, "rc=%d" % proc.returncode)
    proc2 = run_hook(
        INSPECT,
        {"session_id": "t2c", "last_assistant_message": "先把接口钉死，再实现范围守卫。"},
        env,
    )
    body = proc2.stdout.decode("utf-8") + proc2.stderr.decode("utf-8")
    check("L2 detects fixed-version and scope-guard expressions", proc2.returncode == 2 and "敲定" in body and "作用域守卫" in body,
          body[:200])
    proc3 = run_hook(
        INSPECT,
        {"session_id": "t2d", "last_assistant_message": "这里还有一个遗留缺口需要补齐。"},
        env,
    )
    body3 = proc3.stdout.decode("utf-8") + proc3.stderr.decode("utf-8")
    check("L2 detects stiff remaining-work expressions",
          proc3.returncode == 2 and "剩下的待办" in body3, body3[:200])


def test_l2_passes_clean_message():
    env, sd = temp_env()
    proc = run_hook(
        INSPECT,
        {"session_id": "t3", "last_assistant_message": "重试逻辑已修复，重复请求从 24 次降到 7 次。"},
        env,
    )
    check("L2 allows clean Chinese text (exit 0)", proc.returncode == 0, "rc=%d" % proc.returncode)


def test_l2_ignores_code_blocks():
    env, sd = temp_env()
    msg = "代码如下：\n```python\n# 病灶实验 demo\nrun_ablation()\n```\n上面的脚本演示了消融实验。"
    proc = run_hook(INSPECT, {"session_id": "t4", "last_assistant_message": msg}, env)
    check("L2 exempts terms inside code blocks", proc.returncode == 0, "rc=%d" % proc.returncode)


def test_l2_ignores_quoted_mentions():
    """提及（引号内）与使用（正文）的区分。"""
    env, sd = temp_env()
    msg = "字典里有一条：「幽灵词元」→ghost token。这个直译词要避免。"
    proc = run_hook(INSPECT, {"session_id": "t8", "last_assistant_message": msg}, env)
    check("L2 exempts corner-quoted mentions", proc.returncode == 0, "rc=%d" % proc.returncode)
    msg2 = "模型存在幽灵词元问题，需要处理。"
    proc2 = run_hook(INSPECT, {"session_id": "t9", "last_assistant_message": msg2}, env)
    check("L2 still detects terms in ordinary prose", proc2.returncode == 2, "rc=%d" % proc2.returncode)
    msg3 = "字典里有一条：\u201c幽灵词元\u201d→ghost token。"
    proc3 = run_hook(INSPECT, {"session_id": "t10", "last_assistant_message": msg3}, env)
    check("L2 exempts curly-quoted mentions", proc3.returncode == 0, "rc=%d" % proc3.returncode)


def test_l2_failopen_on_garbage_stdin():
    env, sd = temp_env()
    proc = subprocess.run(
        [PY, INSPECT],
        input=b"not json at all {{{",
        capture_output=True,
        env={**os.environ, **env},
        timeout=20,
    )
    check("L2 fails open on invalid input", proc.returncode == 0, "rc=%d" % proc.returncode)
    proc2 = subprocess.run(
        [PY, INJECT],
        input=b"",
        capture_output=True,
        env={**os.environ, **env},
        timeout=20,
    )
    check("L1 fails open on empty input", proc2.returncode == 0, "rc=%d" % proc2.returncode)


def test_l2_missing_dict_failopen():
    env, sd = temp_env()
    env["ZH_GUARD_DICT"] = os.path.join(sd, "no-such-dict.tsv")
    proc = run_hook(INSPECT, {"session_id": "t5", "last_assistant_message": "病灶实验"}, env)
    check("L2 fails open when the dictionary is missing", proc.returncode == 0, "rc=%d" % proc.returncode)


def test_loop_protection_same_message():
    env, sd = temp_env()
    msg = "我们又做了一次病灶实验。"
    p1 = run_hook(INSPECT, {"session_id": "t6", "last_assistant_message": msg}, env)
    p2 = run_hook(INSPECT, {"session_id": "t6", "last_assistant_message": msg}, env)
    check("Identical messages are not blocked twice", p1.returncode == 2 and p2.returncode == 0,
          "rc1=%d rc2=%d" % (p1.returncode, p2.returncode))


def test_kill_switch():
    env, sd = temp_env()
    env["ZH_GUARD_OFF"] = "1"
    proc = run_hook(INSPECT, {"session_id": "t7", "last_assistant_message": "病灶实验"}, env)
    check("ZH_GUARD_OFF=1 disables L2", proc.returncode == 0, "rc=%d" % proc.returncode)
    proc2 = run_hook(INJECT, {"prompt": "hi", "session_id": "t7"}, env)
    check("ZH_GUARD_OFF=1 disables L1", proc2.returncode == 0 and proc2.stdout.strip() == b"",
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
        check("L2 detects added user dictionary entries", proc.returncode == 2, "rc=%d" % proc.returncode)
        proc2 = run_hook(INJECT, {"prompt": "hi", "session_id": "t12"}, env)
        ctx = json.loads(proc2.stdout.decode("utf-8"))["hookSpecificOutput"]["additionalContext"]
        check("L1 displays added user dictionary entries", "用户生造词" in ctx, ctx[-200:])
        check("L1 displays reference suggestions with arrows", "→" in ctx, ctx[-200:])
        check("L1 includes wording guidance in rule 5", "剩下的待办" in ctx, ctx[-200:])
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
            "病灶实验\t消融实验\t旧写法\n"
            "用户自加词\t用户自己的写法\t用户补充\n"
        )
    try:
        run_hook(INJECT, {"prompt": "hi", "session_id": "t17"}, env)
        with open(user_dict, encoding="utf-8") as f:
            content = f.read()
        check("Outdated user dictionary receives updated bundled entries",
              "下一处可以精简的部分" in content, content[:300])
        check("Upgrade removes obsolete experiment wording",
              "排查原因的实验" in content and "消融" not in content,
              content[:300])
        check("Synchronization preserves user-added entries", "用户自加词\t用户自己的写法" in content, content[:300])
        check("Synchronized user dictionary includes the @sync marker", "# @sync" in content, content[:300])
        proc = run_hook(
            INSPECT,
            {"session_id": "t18", "last_assistant_message": "下一刀砍在推理预算上。"},
            env,
        )
        body = proc.stdout.decode("utf-8") + proc.stderr.decode("utf-8")
        check("L2 feedback uses the updated suggestion instead of the old one",
              proc.returncode == 2 and "下一处可以精简的部分" in body
              and "下一个削减项" not in body, body[:300])
        # 版本号一致时不应再改动用户字典
        with open(user_dict, "a", encoding="utf-8") as f:
            f.write("手动加的行\t手动写法\t手工补充\n")
        run_hook(INJECT, {"prompt": "hi", "session_id": "t19"}, env)
        with open(user_dict, encoding="utf-8") as f:
            content2 = f.read()
        check("Matching @sync markers leave the user dictionary unchanged", "手动加的行\t手动写法" in content2, content2[-200:])
    finally:
        shutil.rmtree(home, ignore_errors=True)


def test_off_file_in_guard_home():
    env, sd = temp_env()
    home = tempfile.mkdtemp(prefix="zh-guard-home-")
    env["ZH_GUARD_HOME"] = home
    open(os.path.join(home, "OFF"), "w").close()
    try:
        proc = run_hook(INSPECT, {"session_id": "t13", "last_assistant_message": "病灶实验"}, env)
        check("ZH_GUARD_HOME/OFF disables L2", proc.returncode == 0, "rc=%d" % proc.returncode)
    finally:
        shutil.rmtree(home, ignore_errors=True)


def test_install_time_migration():
    """安装迁移：首次运行把插件自带字典复制到 ZH_GUARD_HOME，之后不覆盖。"""
    env, sd = temp_env()
    home = tempfile.mkdtemp(prefix="zh-guard-home-")
    env["ZH_GUARD_HOME"] = home
    try:
        user_dict = os.path.join(home, "terminology.tsv")
        check("User dictionary does not exist before migration", not os.path.exists(user_dict))
        run_hook(INJECT, {"prompt": "hi", "session_id": "t14"}, env)
        check("First run migrates the dictionary to ZH_GUARD_HOME", os.path.exists(user_dict))
        with open(user_dict, encoding="utf-8") as f:
            content = f.read()
        check("Migrated dictionary contains bundled investigation entries", "病灶实验" in content)
        with open(user_dict, "a", encoding="utf-8") as f:
            f.write("迁移后新增词\t正确写法\t用户补充\n")
        run_hook(INJECT, {"prompt": "hi", "session_id": "t15"}, env)
        with open(user_dict, encoding="utf-8") as f:
            content2 = f.read()
        check("Migration preserves entries added to an existing user dictionary", "迁移后新增词" in content2)
        proc = run_hook(
            INSPECT,
            {"session_id": "t16", "last_assistant_message": "这里出现了迁移后新增词。"},
            env,
        )
        check("L2 detects migrated user entries", proc.returncode == 2, "rc=%d" % proc.returncode)
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
        check("Regex fixture %s expects rc=%d" % (msg[:14], want_rc),
              proc.returncode == want_rc, "rc=%d" % proc.returncode)
        if want_rc == 2 and want_hit:
            body = proc.stdout.decode("utf-8") + proc.stderr.decode("utf-8")
            check("Block reason includes the actual match (%s)" % want_hit, want_hit in body, body[:200])


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
        check("Valid rules still block after an invalid regex is skipped", proc.returncode == 2, "rc=%d" % proc.returncode)
    finally:
        shutil.rmtree(home, ignore_errors=True)


def test_l2_zcode_stop_contract():
    """zcode 的 Stop 契约：decision:block + reason 续跑一轮。

    zcode 不认 continue:false（那里语义是「允许结束」），
    输出格式错了会让 L2 在 zcode 上整个失效。
    检测方式：环境变量 ZCODE_PLUGIN_ROOT（zcode 只向插件进程注入）。
    """
    env, sd = temp_env()
    env["ZCODE_PLUGIN_ROOT"] = os.path.join(sd, "fake-zcode-root")
    proc = run_hook(
        INSPECT,
        {"session_id": "t-zc1", "last_assistant_message": "我们对网络做病灶实验。"},
        env,
    )
    check("zcode L2 blocks matching text (exit 2)", proc.returncode == 2, "rc=%d" % proc.returncode)
    try:
        out = json.loads(proc.stdout.decode("utf-8"))
    except Exception:
        out = {}
    check("zcode output uses decision=block", out.get("decision") == "block",
          proc.stdout.decode("utf-8")[:200])
    check("zcode output omits continue:false", out.get("continue") is not False,
          proc.stdout.decode("utf-8")[:200])
    check("zcode reason includes plain-language review guidance",
          "排查原因的实验" in out.get("reason", ""), str(out.get("reason", ""))[:200])
    check("zcode writes the block reason to stderr", "排查原因的实验" in proc.stderr.decode("utf-8"),
          proc.stderr.decode("utf-8")[:200])
    proc2 = run_hook(
        INSPECT,
        {"session_id": "t-zc2", "last_assistant_message": "重试逻辑已修复，重复请求降到 7 次。"},
        env,
    )
    check("zcode allows clean messages (exit 0)", proc2.returncode == 0, "rc=%d" % proc2.returncode)


ZCODE_EVENTS = {
    "SessionStart", "UserPromptSubmit", "PreToolUse", "PermissionRequest",
    "PostToolUse", "PostToolUseFailure", "Stop",
}


def test_plugin_hook_files_structure():
    """hook 文件按平台拆分：标准文件只放 zcode 支持的事件，子代理事件单独给 Claude。"""
    with open(os.path.join(HERE, "hooks", "hooks.json"), encoding="utf-8") as f:
        core = json.load(f).get("hooks", {})
    bad = sorted(set(core) - ZCODE_EVENTS)
    check("Core hook configuration contains only zcode-supported events", not bad, "多出：%s" % bad)
    with open(os.path.join(HERE, "hooks", "subagent-hooks.json"), encoding="utf-8") as f:
        sub = json.load(f).get("hooks", {})
    check("Subagent configuration contains only SubagentStart",
          set(sub) == {"SubagentStart"}, "Actual: %s" % sorted(sub))
    with open(os.path.join(HERE, ".claude-plugin", "plugin.json"), encoding="utf-8") as f:
        m = json.load(f)
    check("Claude manifest declares injection-only subagent hooks",
          set(m.get("hooks", [])) == {"./hooks/subagent-hooks.json"} and "mcpServers" not in m,
          str(m.get("hooks")))
    zcode_manifest = os.path.join(HERE, ".zcode-plugin", "plugin.json")
    check("zcode plugin manifest exists", os.path.exists(zcode_manifest), zcode_manifest)
    if os.path.exists(zcode_manifest):
        with open(zcode_manifest, encoding="utf-8") as f:
            zm = json.load(f)
        check("zcode manifest declares no unsupported extra hooks", "hooks" not in zm, str(zm.get("hooks")))
        check("zcode manifest registers no automatic MCP server", "mcpServers" not in zm,
              str(zm.get("mcpServers", {}).keys()))


def test_l2_blocks_new_translationese():
    """新补的直译词条：槽位 / 槽键 / 键-值关系 / 已初步清楚。"""
    env, sd = temp_env()
    cases = [
        ("每个槽位对应一个插件。", "插槽"),
        ("配置按槽键存储。", "slot 的 key"),
        ("存储为键-值关系。", "key-value"),
        ("机制已初步清楚。", "大致了解"),
    ]
    for i, (msg, want) in enumerate(cases):
        proc = run_hook(INSPECT, {"session_id": "t-new%d" % i, "last_assistant_message": msg}, env)
        body = proc.stdout.decode("utf-8") + proc.stderr.decode("utf-8")
        check("L2 detects the new entry (%s)" % msg[:12],
              proc.returncode == 2 and want in body, body[:200])


def test_l1_injection_new_rules_and_wider_cap():
    """注入规则覆盖生硬翻译腔；展示上限放宽后尾部词条不再被截掉。"""
    env, sd = temp_env()
    proc = run_hook(INJECT, {"prompt": "hi", "session_id": "t-l1new"}, env)
    ctx = json.loads(proc.stdout.decode("utf-8"))["hookSpecificOutput"]["additionalContext"]
    check("L1 includes compound-word guidance in rule 6", "硬拼" in ctx and "slot 的 key" in ctx, ctx[:400])
    check("L1 includes updated progress wording in rule 5", "大致了解了" in ctx, ctx[:400])
    check("L1 includes entries near the end of the wider display limit", "槽位→" in ctx, ctx[-300:])
    check("L1 retains existing remaining-work guidance", "剩下的待办" in ctx, ctx[:400])


INSPECT_FILE = os.path.join(HERE, "inspect-file.py")


def test_shared_matching_positions_and_longest_rule():
    env, sd = temp_env()
    path = os.path.join(sd, "custom.tsv")
    with open(path, "w", encoding="utf-8") as f:
        f.write("缺口\t剩下的待办\t短词\n遗留缺口\t还没做完的部分\t长词\n")
    env["ZH_GUARD_DICT"] = path
    text = "第一行。\n遗留缺口。"
    for index, script in enumerate([INSPECT, INSPECT_FILE]):
        payload = {"session_id": "shared-%d" % index, "last_assistant_message": text,
                   "tool_input": {"file_path": "/x/a.md", "content": text}}
        proc = run_hook(script, payload, env)
        body = proc.stdout.decode("utf-8") + proc.stderr.decode("utf-8")
        check("Shared matcher provides positions and suppresses overlapping short terms (%s)" % os.path.basename(script),
              proc.returncode == 2 and "第2行" in body and "第1列" in body
              and "还没做完的部分" in body and "剩下的待办" not in body, body[:400])


def test_project_meaning_and_glossary_across_hooks():
    with tempfile.TemporaryDirectory(prefix="zh-project-meaning-") as base:
        project = os.path.join(base, "project")
        os.makedirs(os.path.join(project, ".git"))
        with open(os.path.join(project, "mindforge.zh-dict.tsv"), "w", encoding="utf-8") as stream:
            stream.write("机械胳膊\t\t科幻人物的身体部件，不是工业设备\n星环\n")
        env = {
            "ZH_GUARD_HOME": os.path.join(base, "home"),
            "ZH_GUARD_LEGACY_HOME": os.path.join(base, "legacy"),
            "ZH_GUARD_STATE_DIR": os.path.join(base, "state"),
        }
        proc = run_hook(INJECT, {"prompt": "你好", "cwd": project}, env)
        ctx = json.loads(proc.stdout)["hookSpecificOutput"]["additionalContext"]
        check("Project meanings are injected in full, not only suggestions",
              "科幻人物的身体部件，不是工业设备" in ctx and "机械胳膊→" not in ctx, ctx[:500])
        check("Glossary-only terms are injected as reference data, not banned words",
              "星环" in ctx and "仅登记" in ctx, ctx[:500])
        for index, script in enumerate([INSPECT, INSPECT_FILE]):
            text = "小说里，他举起机械胳膊挡住攻击。"
            payload = {
                "session_id": "meaning-%d" % index, "cwd": project,
                "last_assistant_message": text,
                "tool_input": {"file_path": "/x/a.md", "content": text},
            }
            proc = run_hook(script, payload, env)
            body = proc.stdout.decode() + proc.stderr.decode()
            check("Output checks receive meaning annotations (%s)" % os.path.basename(script),
                  proc.returncode == 2 and text in body
                  and "科幻人物的身体部件，不是工业设备" in body
                  and "机械胳膊→" not in body and "保留" in body, body[:500])
            payload["last_assistant_message"] = "星环正常。"
            payload["tool_input"]["content"] = "星环正常。"
            proc = run_hook(script, payload, env)
            check("Glossary-only terms do not block output (%s)" % os.path.basename(script),
                  proc.returncode == 0, proc.stderr.decode())


def test_l2_blocks_sentence_patterns():
    """句式级套话：re: 正则词条拦「值得注意的是」「进行了分析」这类模板腔。"""
    env, sd = temp_env()
    cases = [
        ("值得注意的是，网络吞吐量高。", "直接给结论"),
        ("综上所述，这个方案可行。", "直接说结论"),
        ("我们进行了全面的修改。", "直接用动词"),
        ("由于磁盘损坏的原因，数据丢了。", "因为"),
    ]
    for i, (msg, want) in enumerate(cases):
        proc = run_hook(INSPECT, {"session_id": "t-pat%d" % i, "last_assistant_message": msg}, env)
        body = proc.stdout.decode("utf-8") + proc.stderr.decode("utf-8")
        check("L2 detects sentence-level boilerplate (%s...)" % msg[:8],
              proc.returncode == 2 and want in body, body[:200])
    proc = run_hook(
        INSPECT,
        {"session_id": "t-pat-clean", "last_assistant_message": "网络吞吐量高，因为先写磁盘再批量推送。"},
        env,
    )
    check("L2 sentence rules allow natural Chinese text", proc.returncode == 0, "rc=%d" % proc.returncode)


def test_file_guard_blocks_translationese():
    """文件写入口：PreToolUse 检查 Write/Edit 即将写入的文档内容。"""
    env, sd = temp_env()
    proc = run_hook(INSPECT_FILE, {
        "session_id": "tf1", "tool_name": "Write",
        "tool_input": {"file_path": "/x/docs/a.md", "content": "我们对网络做病灶实验，结论如下。"},
    }, env)
    body = proc.stdout.decode("utf-8") + proc.stderr.decode("utf-8")
    check("File guard denies matching Markdown content (exit 2)", proc.returncode == 2, "rc=%d" % proc.returncode)
    check("File guard emits permissionDecision=deny",
          "permissionDecision" in body and "deny" in body, body[:200])
    check("File guard denial includes plain-language review guidance",
          "排查原因的实验" in body and "消融" not in body, body[:200])
    proc2 = run_hook(INSPECT_FILE, {
        "session_id": "tf2", "tool_name": "Write",
        "tool_input": {"file_path": "/x/docs/b.md", "content": "重试逻辑已修复，重复请求降到 7 次。"},
    }, env)
    check("File guard allows clean Markdown", proc2.returncode == 0, "rc=%d" % proc2.returncode)
    proc3 = run_hook(INSPECT_FILE, {
        "session_id": "tf3", "tool_name": "Write",
        "tool_input": {"file_path": "/x/src/a.py", "content": "注释：这里做了病灶实验。"},
    }, env)
    check("File guard allows non-document Python files", proc3.returncode == 0, "rc=%d" % proc3.returncode)
    proc4 = run_hook(INSPECT_FILE, {
        "session_id": "tf4", "tool_name": "Edit",
        "tool_input": {"file_path": "/x/docs/c.md", "new_string": "字典里有一条：「幽灵词元」→ghost token。"},
    }, env)
    check("File guard exempts quoted mentions", proc4.returncode == 0, "rc=%d" % proc4.returncode)
    proc5 = run_hook(INSPECT_FILE, {
        "session_id": "tf5", "tool_name": "Edit",
        "tool_input": {"file_path": "/x/docs/d.md", "new_string": "需要补充：我们对模型做了消融实验以外的病灶实验。"},
    }, env)
    check("File guard also checks Edit new_string content", proc5.returncode == 2, "rc=%d" % proc5.returncode)
    proc6 = run_hook(INSPECT_FILE, {
        "session_id": "tf5", "tool_name": "Edit",
        "tool_input": {"file_path": "/x/docs/d.md", "new_string": "需要补充：我们对模型做了消融实验以外的病灶实验。"},
    }, env)
    check("File guard allows repeated identical content to prevent loops", proc6.returncode == 0, "rc=%d" % proc6.returncode)


def test_prompt_judge_config():
    """Default scheme A ships no model-based Stop reviewer."""
    path = os.path.join(HERE, "hooks", "claude-prompt-hooks.json")
    check("No model-based prompt reviewer is shipped", not os.path.exists(path), path)


def test_project_level_dict():
    """项目级词典：cwd 向上找 mindforge.zh-dict.tsv，优先级最高。

    三级结构：内置 → 用户级 → 项目级（后者覆盖前者）；
    向上查找在含 .git 的项目根停止，根之外的词典不生效。
    """
    base = tempfile.mkdtemp(prefix="zh-guard-proj-")
    proj = os.path.join(base, "proj")
    sub = os.path.join(proj, "sub", "deep")
    os.makedirs(os.path.join(proj, ".git"))
    os.makedirs(sub)
    with open(os.path.join(proj, "mindforge.zh-dict.tsv"), "w", encoding="utf-8") as f:
        f.write("项目黑词\t项目写法\t项目词条\n"
                "病灶实验\t项目覆盖写法\t项目覆盖内置\n")
    with open(os.path.join(base, "mindforge.zh-dict.tsv"), "w", encoding="utf-8") as f:
        f.write("外部黑词\t外部写法\t不应被发现\n")
    env, sd = temp_env()
    try:
        proc = run_hook(INSPECT, {"session_id": "pj1", "cwd": sub,
                                  "last_assistant_message": "这里出现了项目黑词。"}, env)
        check("L2 discovers project entries from a nested cwd",
              proc.returncode == 2, "rc=%d" % proc.returncode)
        proc2 = run_hook(INSPECT, {"session_id": "pj2", "cwd": sub,
                                   "last_assistant_message": "我们对网络做病灶实验。"}, env)
        body = proc2.stdout.decode("utf-8") + proc2.stderr.decode("utf-8")
        check("Project suggestions override bundled entries",
              proc2.returncode == 2 and "项目覆盖写法" in body
              and "排查原因的实验" not in body, body[:200])
        proc3 = run_hook(INSPECT, {"session_id": "pj3", "cwd": sub,
                                   "last_assistant_message": "这里出现了外部黑词。"}, env)
        check("Discovery does not cross the .git project boundary", proc3.returncode == 0, "rc=%d" % proc3.returncode)
        proc4 = run_hook(INJECT, {"prompt": "hi", "session_id": "pj4", "cwd": sub}, env)
        ctx = json.loads(proc4.stdout.decode("utf-8"))["hookSpecificOutput"]["additionalContext"]
        check("L1 includes project-level entries", "项目黑词→项目写法" in ctx, ctx[:200])
        check("L1 displays project entries before bundled entries",
              ctx.index("项目黑词") < ctx.index("神经织网"), ctx[:300])
        proc5 = run_hook(INSPECT_FILE, {
            "session_id": "pj5", "cwd": sub, "tool_name": "Write",
            "tool_input": {"file_path": "/x/a.md", "content": "这里出现了项目黑词。"},
        }, env)
        check("File guard also uses project-level entries", proc5.returncode == 2, "rc=%d" % proc5.returncode)
    finally:
        shutil.rmtree(base, ignore_errors=True)


def test_legacy_home_migration():
    """产品目录改名：~/.claude/zh-guard → ~/.claude/MindForge。

    老用户的自加词条和 OFF 停用标记必须无缝跟到新目录；
    迁移后的旧字典走 @sync 版本同步，自带词条刷新、自加词条保留。
    """
    env, sd = temp_env()
    legacy = tempfile.mkdtemp(prefix="zh-guard-legacy-")
    new_home = tempfile.mkdtemp(prefix="mindforge-home-")
    env["ZH_GUARD_LEGACY_HOME"] = legacy
    env["ZH_GUARD_HOME"] = new_home
    with open(os.path.join(legacy, "terminology.tsv"), "w", encoding="utf-8") as f:
        f.write("# 老安装的用户字典（无 @sync 标记）\n"
                "用户生造词\t正确写法\t老词条\n")
    open(os.path.join(legacy, "OFF"), "w").close()
    try:
        proc = run_hook(INSPECT, {"session_id": "lg0",
                                  "last_assistant_message": "这里出现了用户生造词。"}, env)
        check("Legacy OFF marker disables hooks before migration", proc.returncode == 0,
              "rc=%d" % proc.returncode)
        check("OFF marker is migrated", os.path.exists(os.path.join(new_home, "OFF")))
        os.remove(os.path.join(new_home, "OFF"))
        run_hook(INJECT, {"prompt": "hi", "session_id": "lg1"}, env)
        new_dict = os.path.join(new_home, "terminology.tsv")
        check("Legacy dictionary migrates to the new directory", os.path.exists(new_dict), new_dict)
        with open(new_dict, encoding="utf-8") as f:
            content = f.read()
        check("Legacy user-added entries survive migration", "用户生造词\t正确写法" in content, content[:300])
        check("Legacy dictionary receives version synchronization and a new marker", "# @sync" in content, content[:300])
        proc2 = run_hook(INSPECT, {"session_id": "lg2",
                                   "last_assistant_message": "这里出现了用户生造词。"}, env)
        check("L2 uses migrated entries after hooks are re-enabled", proc2.returncode == 2, "rc=%d" % proc2.returncode)
    finally:
        shutil.rmtree(legacy, ignore_errors=True)
        shutil.rmtree(new_home, ignore_errors=True)


def test_platform_flag_for_cli_installed_hooks():
    """--platform 参数：CLI 用户级安装的 zcode hook 拿不到 ZCODE_PLUGIN_ROOT，
    需要显式参数切到 zcode 的 Stop 契约。"""
    env, sd = temp_env()
    proc = run_hook(INSPECT, {"session_id": "pf1",
                              "last_assistant_message": "我们对网络做病灶实验。"},
                    env, args=["--platform"])
    out = json.loads(proc.stdout.decode("utf-8"))
    check("The --platform option uses the decision:block contract",
          proc.returncode == 2 and out.get("decision") == "block",
          proc.stdout.decode("utf-8")[:200])


def main():
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        try:
            t()
        except Exception as exc:
            check(t.__name__ + " (exception)", False, repr(exc))
        finally:
            # temp_env 创建的状态目录在函数局部，统一在结尾清理代价高；
            # 用系统临时目录自清理策略，测试里不强制删除。
            pass
    print("")
    if FAILURES:
        print("Failed %d checks: %s" % (len(FAILURES), ", ".join(FAILURES)))
        sys.exit(1)
    print("All passed (%d tests)" % len(tests))
    sys.exit(0)


if __name__ == "__main__":
    main()
