#!/usr/bin/env python3
"""term-dict MCP 服务器测试套件。

运行：python3 test_term_dict_mcp.py
用真实 stdio JSON-RPC 驱动服务器，验证端到端行为。
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER = os.path.join(HERE, "term-dict-server.py")
PY = sys.executable

FAILURES = []


def check(name, condition, detail=""):
    if condition:
        print("PASS  " + name)
    else:
        print("FAIL  " + name + ("  | " + detail if detail else ""))
        FAILURES.append(name)


class McpClient:
    """极简 stdio MCP 客户端：发送请求，按 id 匹配响应。"""

    def __init__(self, env):
        self.proc = subprocess.Popen(
            [PY, SERVER],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=env,
        )
        self._id = 0

    def request(self, method, params=None):
        self._id += 1
        msg = {"jsonrpc": "2.0", "id": self._id, "method": method}
        if params is not None:
            msg["params"] = params
        return self._roundtrip(msg)

    def notify(self, method, params=None):
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        self.proc.stdin.write(
            (json.dumps(msg, ensure_ascii=False) + "\n").encode("utf-8")
        )
        self.proc.stdin.flush()

    def _roundtrip(self, msg):
        self.proc.stdin.write(
            (json.dumps(msg, ensure_ascii=False) + "\n").encode("utf-8")
        )
        self.proc.stdin.flush()
        while True:
            line = self.proc.stdout.readline()
            if not line:
                raise RuntimeError("server closed stdout")
            resp = json.loads(line.decode("utf-8"))
            if resp.get("id") == msg["id"]:
                return resp

    def close(self):
        try:
            self.proc.stdin.close()
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()


def call_tool(client, name, args):
    resp = client.request("tools/call", {"name": name, "arguments": args})
    result = resp.get("result", {})
    return result.get("isError", True), result.get("content", [{}])[0].get("text", "")


def fresh_env():
    home = tempfile.mkdtemp(prefix="term-dict-home-")
    env = dict(os.environ)
    env["ZH_GUARD_HOME"] = home
    return env, home


def test_initialize_handshake():
    env, home = fresh_env()
    c = McpClient(env)
    try:
        resp = c.request("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}})
        ok = resp.get("result", {}).get("capabilities", {}).get("tools") == {}
        check("Initialize handshake exposes tool capabilities", ok, json.dumps(resp)[:200])
        c.notify("notifications/initialized")
        resp2 = c.request("tools/list")
        names = sorted(t["name"] for t in resp2.get("result", {}).get("tools", []))
        check("tools/list exposes all four mindforge tools", names == [
            "mindforge_add_term", "mindforge_check_text", "mindforge_init_dict", "mindforge_lookup_term",
        ], str(names))
        check("Tool descriptions do not recommend obsolete wording",
              "消融" not in json.dumps(resp2, ensure_ascii=False), str(resp2)[:300])
        for old_name in ["lookup_term", "check_text", "add_term"]:
            err, text = call_tool(c, old_name, {})
            check("Legacy tool names are rejected (%s)" % old_name,
                  err and text == "Unknown tool: %s" % old_name, text[:200])
        resp3 = c.request("ping")
        check("Ping returns an empty result", resp3.get("result") == {})
    finally:
        c.close()
        shutil.rmtree(home, ignore_errors=True)


def test_lookup_term():
    env, home = fresh_env()
    c = McpClient(env)
    try:
        err, text = call_tool(c, "mindforge_lookup_term", {"query": "ablation"})
        check("Lookup does not conflate ablation with root-cause terminology",
              (not err) and "无匹配词条" in text and "病灶" not in text, text[:300])
        err, text = call_tool(c, "mindforge_lookup_term", {"query": "病灶"})
        check("Lookup provides root-cause investigation guidance",
              (not err) and "病灶实验 → 排查原因的实验" in text
              and "病灶研究 → 排查问题原因" in text
              and "病灶分析 → 分析问题原因" in text
              and "消融" not in text, text[:300])
        err, text = call_tool(c, "mindforge_lookup_term", {"query": "GROUND TRUTH"})
        check("Lookup is case-insensitive (GROUND TRUTH)", (not err) and "真值" in text, text[:200])
        err, text = call_tool(c, "mindforge_lookup_term", {"query": "不存在的词xyz"})
        check("Lookup misses advise retaining the original English term", (not err) and "保留英文" in text, text[:200])
        err, text = call_tool(c, "mindforge_lookup_term", {"query": ""})
        check("Empty lookup query returns a diagnostic", err or "query" in text, text[:200])
    finally:
        c.close()
        shutil.rmtree(home, ignore_errors=True)


def test_check_text():
    env, home = fresh_env()
    c = McpClient(env)
    try:
        err, text = call_tool(c, "mindforge_check_text", {"text": "我们对网络做病灶实验，发现幽灵词元。"})
        check("mindforge_check_text annotates matching expressions",
              (not err) and "排查原因的实验" in text
              and "幽灵词元" in text and "消融" not in text, text[:300])
        err, text = call_tool(c, "mindforge_check_text", {"text": "按计划，第36刀砍在推理预算上。"})
        check("mindforge_check_text detects regex entries", (not err) and "第36刀" in text, text[:300])
        err, text = call_tool(c, "mindforge_check_text", {"text": "重试逻辑已修复，请求从 24 次降到 7 次。"})
        check("mindforge_check_text allows clean text", (not err) and "未命中" in text, text[:200])
        err, text = call_tool(c, "mindforge_check_text", {"text": "医生正在确认病灶的位置。"})
        check("mindforge_check_text does not flag the medical fixture", (not err) and "未命中" in text, text[:200])
        msg = "代码：\n```python\n# 病灶实验\nrun()\n```\n字典里「幽灵词元」→ghost token。"
        err, text = call_tool(c, "mindforge_check_text", {"text": msg})
        check("mindforge_check_text exempts code and quoted mentions", (not err) and "未命中" in text, text[:200])
    finally:
        c.close()
        shutil.rmtree(home, ignore_errors=True)


def test_add_term_flywheel():
    env, home = fresh_env()
    c = McpClient(env)
    try:
        err, text = call_tool(c, "mindforge_add_term", {"term": "飞轮测试词", "suggestion": "正确写法", "meaning": "MCP 测试", "scope": "user"})
        check("mindforge_add_term reports successful writes", (not err) and "已添加" in text, text[:300])
        user_dict = os.path.join(home, "terminology.tsv")
        content = open(user_dict, encoding="utf-8").read()
        check("Entry is written to the user dictionary", "飞轮测试词\t正确写法\tMCP 测试" in content, content[-200:])
        err, text = call_tool(c, "mindforge_lookup_term", {"query": "飞轮测试词"})
        check("New entry is immediately searchable", (not err) and "正确写法" in text, text[:200])
        err, text = call_tool(c, "mindforge_check_text", {"text": "这里出现了飞轮测试词。"})
        check("New entry is immediately detected", (not err) and "飞轮测试词" in text, text[:200])
        # TSV 注入防护
        err, text = call_tool(c, "mindforge_add_term", {"term": "带\t制表符\t词", "suggestion": "安全写法", "scope": "user"})
        content2 = open(user_dict, encoding="utf-8").read()
        lines = [l for l in content2.split("\n") if "安全写法" in l]
        check("Embedded tabs are sanitized to preserve TSV structure", lines and len(lines[0].split("\t")) == 3, str(lines))
        err, text = call_tool(c, "mindforge_add_term", {"term": "", "suggestion": "x"})
        check("Missing term is rejected", err or "必填" in text, text[:200])
    finally:
        c.close()
        shutil.rmtree(home, ignore_errors=True)


def test_install_migration_and_unknown_tool():
    env, home = fresh_env()
    c = McpClient(env)
    try:
        c.request("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}})
        user_dict = os.path.join(home, "terminology.tsv")
        check("Server startup seeds the bundled dictionary in ZH_GUARD_HOME", os.path.exists(user_dict))
        err, text = call_tool(c, "mindforge_check_text", {"text": "模型存在幽灵词元问题。"})
        check("Bundled entries remain available after migration", (not err) and "幽灵词元" in text, text[:200])
        err, text = call_tool(c, "mindforge_lookup_term", {"query": "x"})
        err, text = call_tool(c, "no_such_tool", {})
        check("Unknown tool returns isError", err and "Unknown tool" in text, text[:200])
    finally:
        c.close()
        shutil.rmtree(home, ignore_errors=True)


def test_structured_sentence_annotations_do_not_replace_text():
    env, home = fresh_env()
    dictionary = os.path.join(home, "custom.tsv")
    with open(dictionary, "w", encoding="utf-8") as f:
        f.write("机械胳膊\t机械臂\t工业设备语境才参考\n"
                "台账\t清单 / 记录\t按上下文选择\n")
    env["ZH_GUARD_DICT"] = dictionary
    c = McpClient(env)
    try:
        text = "机械胳膊。\n补上台账，台账中保留 `机械胳膊`。"
        response = c.request("tools/call", {
            "name": "mindforge_check_text", "arguments": {"text": text},
        }).get("result", {})
        report = response.get("structuredContent", {})
        check("Preflight preserves the complete draft without replacement",
              report.get("draft") == text,
              str(report)[:300])
        findings = report.get("annotations", [])
        check("Structured output includes all unprotected annotations",
              [h.get("text") for h in findings] == ["机械胳膊", "台账", "台账"],
              str(findings)[:300])
        check("Annotations retain original offsets, line, column and context",
              len(findings) == 3 and findings[1].get("start") == 8
              and findings[1].get("line") == 2 and findings[1].get("column") == 3
              and "补上台账" in findings[1].get("context", ""), str(findings)[:300])
        check("Annotations include meaning, suggestion and complete sentence",
              len(findings) == 3 and findings[0].get("suggestion") == "机械臂"
              and findings[0].get("meaning") == "工业设备语境才参考"
              and findings[1].get("sentence") == "补上台账，台账中保留 `机械胳膊`。"
              and report.get("needs_review") is True, str(report)[:300])
        check("Reports expose no misleading automatic-correction fields",
              not {"corrected_text", "changed", "needs_rewrite"} & report.keys(),
              str(report)[:300])
        check("Human-readable feedback remains available",
              bool(response.get("content")) and "台账" in response["content"][0]["text"],
              str(response)[:300])
        feedback = response["content"][0]["text"]
        check("MCP recheck guidance uses only prefixed tool names",
              "mindforge_check_text" in feedback
              and re.search(r"\b(?:lookup_term|check_text|add_term)\b", feedback) is None,
              feedback[-400:])
    finally:
        c.close()
        shutil.rmtree(home, ignore_errors=True)


def test_preflight_project_dictionary_and_invalid_input():
    env, home = fresh_env()
    project = os.path.join(home, "project")
    os.mkdir(project)
    os.mkdir(os.path.join(project, ".git"))
    with open(os.path.join(project, "mindforge.zh-dict.tsv"), "w", encoding="utf-8") as f:
        f.write("机械胳膊\t项目中保留原意\t项目覆盖\n")
    c = McpClient(env)
    try:
        response = c.request("tools/call", {
            "name": "mindforge_check_text", "arguments": {"text": "机械胳膊", "cwd": project},
        }).get("result", {})
        report = response.get("structuredContent", {})
        check("Explicit MCP cwd uses the same project overrides as hooks",
              report.get("draft") == "机械胳膊"
              and len(report.get("annotations", [])) == 1
              and report["annotations"][0].get("suggestion") == "项目中保留原意",
              str(report)[:300])
        for args in [{"text": ""}, {"text": "测试", "cwd": "relative/path"}]:
            response = c.request("tools/call", {
                "name": "mindforge_check_text", "arguments": args,
            }).get("result", {})
            check("Invalid preflight input returns a tool error (%s)" % args,
                  response.get("isError") is True, str(response)[:300])
    finally:
        c.close()
        shutil.rmtree(home, ignore_errors=True)


def test_add_term_can_register_a_term_or_only_its_meaning():
    env, home = fresh_env()
    c = McpClient(env)
    try:
        err, text = call_tool(c, "mindforge_add_term", {"term": "星环", "scope": "user"})
        check("Terms can be registered without guidance", not err and "已添加" in text, text[:200])
        err, text = call_tool(c, "mindforge_add_term", {
            "term": "科幻机械胳膊", "meaning": "人物身体部件，不是工业设备", "scope": "user",
        })
        check("Entries can provide meaning without a suggestion", not err and "已添加" in text, text[:200])
        response = c.request("tools/call", {
            "name": "mindforge_check_text", "arguments": {"text": "星环里，他举起科幻机械胳膊。"},
        }).get("result", {})
        report = response.get("structuredContent", {})
        annotations = report.get("annotations", [])
        check("Glossary terms are not errors and meanings appear in annotations",
              len(annotations) == 1 and annotations[0].get("text") == "科幻机械胳膊"
              and annotations[0].get("suggestion") == ""
              and annotations[0].get("meaning") == "人物身体部件，不是工业设备",
              str(response)[:300])
        for term in ["# 无效注释", "   ", "re:["]:
            err, text = call_tool(c, "mindforge_add_term", {"term": term})
            check("Invalid entry is not written (%s)" % term, err, text[:200])
        with open(os.path.join(home, "terminology.tsv"), encoding="utf-8") as f:
            content = f.read()
        check("Optional fields preserve three-column TSV output",
              "星环\t\t\n" in content
              and "科幻机械胳膊\t\t人物身体部件，不是工业设备\n" in content,
              content[-200:])
    finally:
        c.close()
        shutil.rmtree(home, ignore_errors=True)


def test_project_meanings_override_bundled_suggestions():
    env, home = fresh_env()
    project = os.path.join(home, "project")
    os.makedirs(os.path.join(project, ".git"))
    with open(os.path.join(project, "mindforge.zh-dict.tsv"), "w", encoding="utf-8") as stream:
        stream.write("机械胳膊\t\t本项目指科幻人物身体部件\n病灶分析\t\t排查问题根因\n星环\n")
    client = McpClient(env)
    try:
        text = "小说里，他举起机械胳膊。星环正常。"
        result = client.request("tools/call", {
            "name": "mindforge_check_text", "arguments": {"text": text, "cwd": project},
        }).get("result", {})
        report = result.get("structuredContent", {})
        annotations = report.get("annotations", [])
        check("Project meanings annotate the unchanged draft",
              report.get("draft") == text and len(annotations) == 1
              and annotations[0].get("meaning") == "本项目指科幻人物身体部件"
              and annotations[0].get("sentence") == "小说里，他举起机械胳膊。",
              str(report)[:400])
        check("Annotation identifiers are generated and tied to the draft",
              len(annotations) == 1 and bool(annotations[0].get("annotation_id"))
              and annotations[0].get("draft_id") == report.get("draft_id"),
              str(report)[:400])
        err, lookup = call_tool(client, "mindforge_lookup_term", {"query": "星环", "cwd": project})
        check("Glossary-only entries are searchable without invented suggestions", not err and "星环" in lookup and "→" not in lookup, lookup)
        err, lookup = call_tool(client, "mindforge_lookup_term", {"query": "机械胳膊", "cwd": project})
        check("Meaning-only feedback contains no empty replacement arrow",
              not err and "科幻人物身体部件" in lookup and "→" not in lookup, lookup)
        _, feedback = call_tool(client, "mindforge_check_text", {"text": "星环正常。", "cwd": project})
        check("Glossary-only entries do not request rewriting", "未命中" in feedback, feedback)
    finally:
        client.close()
        shutil.rmtree(home, ignore_errors=True)


def test_add_term_defaults_to_workspace_and_isolates_workspaces():
    env, home = fresh_env()
    first, second = os.path.join(home, "first"), os.path.join(home, "second")
    os.makedirs(os.path.join(first, ".git"))
    os.makedirs(os.path.join(first, "src"))
    os.makedirs(os.path.join(second, ".git"))
    client = McpClient(env)
    try:
        client.request("initialize")
        user_path = os.path.join(home, "terminology.tsv")
        with open(user_path, encoding="utf-8") as stream:
            user_before = stream.read()
        for cwd, meaning in [(os.path.join(first, "src"), "第一个项目的含义"), (second, "第二个项目的含义")]:
            err, text = call_tool(client, "mindforge_add_term", {
                "term": "工作区词", "meaning": meaning, "cwd": cwd,
            })
            check("Default additions target the workspace (%s)" % meaning, not err and "已添加" in text, text)
            response = client.request("tools/call", {
                "name": "mindforge_check_text", "arguments": {"text": "解释工作区词。", "cwd": cwd},
            }).get("result", {})
            annotations = response.get("structuredContent", {}).get("annotations", [])
            check("One MCP process isolates meanings across workspaces",
                  len(annotations) == 1 and annotations[0].get("meaning") == meaning, str(response)[:300])
        check("Adding from a subdirectory initializes the project root", os.path.isfile(os.path.join(first, "mindforge.zh-dict.tsv")))
        check("No extra dictionary is created in the source subdirectory", not os.path.exists(os.path.join(first, "src", "mindforge.zh-dict.tsv")))
        with open(user_path, encoding="utf-8") as stream:
            check("Workspace additions leave the user dictionary unchanged", stream.read() == user_before)
    finally:
        client.close()
        shutil.rmtree(home, ignore_errors=True)


def test_workspace_init_is_idempotent_and_preserves_existing_text():
    env, home = fresh_env()
    workspace = os.path.join(home, "workspace")
    os.mkdir(workspace)
    client = McpClient(env)
    try:
        first = client.request("tools/call", {
            "name": "mindforge_init_dict", "arguments": {"cwd": workspace},
        }).get("result", {})
        report = first.get("structuredContent", {})
        path = os.path.join(workspace, "mindforge.zh-dict.tsv")
        check("Init reports the actual path and creation status",
              first.get("isError") is False and report == {"path": path, "created": True}, str(first)[:300])
        if not os.path.isfile(path):
            check("Init creates the workspace dictionary", False, path)
            return
        with open(path, encoding="utf-8") as stream:
            template = stream.read()
        check("New dictionary contains only comments and blank lines",
              all(not line.strip() or line.startswith("#") for line in template.splitlines()), template)
        with open(path, "w", encoding="utf-8") as stream:
            stream.write("原词\t\t原意")  # Deliberately no trailing newline.
        second = client.request("tools/call", {
            "name": "mindforge_init_dict", "arguments": {"cwd": workspace},
        }).get("result", {})
        with open(path, encoding="utf-8") as stream:
            check("Repeated initialization preserves existing contents",
                  second.get("isError") is False
                  and second.get("structuredContent") == {"path": path, "created": False}
                  and stream.read() == "原词\t\t原意", str(second)[:300])
        err, text = call_tool(client, "mindforge_add_term", {
            "cwd": workspace, "term": "新词", "meaning": "新意",
        })
        with open(path, encoding="utf-8") as stream:
            check("Appending supplies a missing newline without joining entries",
                  not err and stream.read() == "原词\t\t原意\n新词\t\t新意\n", text)
    finally:
        client.close()
        shutil.rmtree(home, ignore_errors=True)


def test_workspace_writes_require_explicit_valid_directory():
    env, home = fresh_env()
    client = McpClient(env)
    try:
        for name in ["mindforge_init_dict", "mindforge_add_term"]:
            for cwd in [None, "relative", os.path.join(home, "missing")]:
                args = {} if cwd is None else {"cwd": cwd}
                if name == "mindforge_add_term":
                    args["term"] = "不能写错目录"
                err, text = call_tool(client, name, args)
                check("Missing or invalid cwd reports an error (%s, %s)" % (name, cwd),
                      err and "cwd" in text, text)
        err, text = call_tool(client, "mindforge_add_term", {
            "term": "不能选错层级", "scope": "unknown",
        })
        check("Invalid scope does not fall back to the user dictionary", err and "scope" in text, text)
    finally:
        client.close()
        shutil.rmtree(home, ignore_errors=True)


def test_scheduling_and_sleep_annotations_preserve_context():
    env, home = fresh_env()
    client = McpClient(env)
    try:
        for text, term, meaning in [
            ("当前任务纯尾即就绪。", "纯尾即就绪", "等这个任务完成之后，就继续下一项"),
            ("下一项已挂起等门控。", "已挂起等门控", "已经安排下一个任务，等待执行"),
            ("线程先睡20毫秒，再重试。", "睡", "进程、线程的休眠机制"),
            ("今晚早点睡觉。", "睡", "人的睡眠、睡觉"),
        ]:
            response = client.request("tools/call", {
                "name": "mindforge_check_text", "arguments": {"text": text},
            }).get("result", {})
            report = response.get("structuredContent", {})
            annotations = report.get("annotations", [])
            check("Contextual annotation provides meaning without prescribing a replacement (%s)" % term,
                  response.get("isError") is False and report.get("draft") == text
                  and len(annotations) == 1 and annotations[0].get("text") == term
                  and annotations[0].get("suggestion") == ""
                  and meaning in annotations[0].get("meaning", ""), str(report)[:400])
            if term == "睡" and annotations:
                check("Sleep guidance distinguishes human sleep from engineering mechanisms",
                      "保留" in annotations[0]["meaning"]
                      and "不要" in annotations[0]["meaning"], annotations[0]["meaning"])
    finally:
        client.close()
        shutil.rmtree(home, ignore_errors=True)


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
