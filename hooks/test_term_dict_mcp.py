#!/usr/bin/env python3
"""term-dict MCP 服务器测试套件。

运行：python3 test_term_dict_mcp.py
用真实 stdio JSON-RPC 驱动服务器，验证端到端行为。
"""
import json
import os
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
        check("initialize 握手返回 tools 能力", ok, json.dumps(resp)[:200])
        c.notify("notifications/initialized")
        resp2 = c.request("tools/list")
        names = sorted(t["name"] for t in resp2.get("result", {}).get("tools", []))
        check("tools/list 返回三工具", names == ["add_term", "check_text", "lookup_term"], str(names))
        check("工具说明不再推荐旧说法",
              "消融" not in json.dumps(resp2, ensure_ascii=False), str(resp2)[:300])
        resp3 = c.request("ping")
        check("ping 返回空结果", resp3.get("result") == {})
    finally:
        c.close()
        shutil.rmtree(home, ignore_errors=True)


def test_lookup_term():
    env, home = fresh_env()
    c = McpClient(env)
    try:
        err, text = call_tool(c, "lookup_term", {"query": "ablation"})
        check("lookup ablation 不再错误关联病灶词条",
              (not err) and "无匹配词条" in text and "病灶" not in text, text[:300])
        err, text = call_tool(c, "lookup_term", {"query": "病灶"})
        check("lookup 病灶 按排查问题原因改写",
              (not err) and "病灶实验 → 排查原因的实验" in text
              and "病灶研究 → 排查问题原因" in text
              and "病灶分析 → 分析问题原因" in text
              and "消融" not in text, text[:300])
        err, text = call_tool(c, "lookup_term", {"query": "GROUND TRUTH"})
        check("lookup 大小写不敏感（GROUND TRUTH）", (not err) and "真值" in text, text[:200])
        err, text = call_tool(c, "lookup_term", {"query": "不存在的词xyz"})
        check("lookup 未命中给保留英文指引", (not err) and "保留英文" in text, text[:200])
        err, text = call_tool(c, "lookup_term", {"query": ""})
        check("lookup 空查询返回提示", err or "query" in text, text[:200])
    finally:
        c.close()
        shutil.rmtree(home, ignore_errors=True)


def test_check_text():
    env, home = fresh_env()
    c = McpClient(env)
    try:
        err, text = call_tool(c, "check_text", {"text": "我们对网络做病灶实验，发现幽灵词元。"})
        check("check_text 命中直译词并给修正",
              (not err) and "排查原因的实验" in text
              and "幽灵词元" in text and "消融" not in text, text[:300])
        err, text = call_tool(c, "check_text", {"text": "按计划，第36刀砍在推理预算上。"})
        check("check_text 命中正则词条（第36刀）", (not err) and "第36刀" in text, text[:300])
        err, text = call_tool(c, "check_text", {"text": "重试逻辑已修复，请求从 24 次降到 7 次。"})
        check("check_text 干净文本无命中", (not err) and "未命中" in text, text[:200])
        err, text = call_tool(c, "check_text", {"text": "医生正在确认病灶的位置。"})
        check("check_text 不拦截医疗语境的病灶", (not err) and "未命中" in text, text[:200])
        msg = "代码：\n```python\n# 病灶实验\nrun()\n```\n字典里「幽灵词元」→ghost token。"
        err, text = call_tool(c, "check_text", {"text": msg})
        check("check_text 代码块与引号提及豁免", (not err) and "未命中" in text, text[:200])
    finally:
        c.close()
        shutil.rmtree(home, ignore_errors=True)


def test_add_term_flywheel():
    env, home = fresh_env()
    c = McpClient(env)
    try:
        err, text = call_tool(c, "add_term", {"term": "飞轮测试词", "expected": "正确写法", "note": "MCP 测试"})
        check("add_term 返回成功", (not err) and "已添加" in text, text[:300])
        user_dict = os.path.join(home, "terminology.tsv")
        content = open(user_dict, encoding="utf-8").read()
        check("词条写入用户字典", "飞轮测试词\t正确写法\tMCP 测试" in content, content[-200:])
        err, text = call_tool(c, "lookup_term", {"query": "飞轮测试词"})
        check("新增词条立即可查询", (not err) and "正确写法" in text, text[:200])
        err, text = call_tool(c, "check_text", {"text": "这里出现了飞轮测试词。"})
        check("新增词条立即可检测", (not err) and "飞轮测试词" in text, text[:200])
        # TSV 注入防护
        err, text = call_tool(c, "add_term", {"term": "带\t制表符\t词", "expected": "安全写法"})
        content2 = open(user_dict, encoding="utf-8").read()
        lines = [l for l in content2.split("\n") if "安全写法" in l]
        check("词条内制表符被清洗（TSV 结构完好）", lines and len(lines[0].split("\t")) == 3, str(lines))
        err, text = call_tool(c, "add_term", {"term": "", "expected": "x"})
        check("缺 term 拒绝写入", err or "必填" in text, text[:200])
    finally:
        c.close()
        shutil.rmtree(home, ignore_errors=True)


def test_install_migration_and_unknown_tool():
    env, home = fresh_env()
    c = McpClient(env)
    try:
        c.request("initialize", {"protocolVersion": "2024-11-05", "capabilities": {}})
        user_dict = os.path.join(home, "terminology.tsv")
        check("服务器启动即迁移字典（bundled → ZH_GUARD_HOME）", os.path.exists(user_dict))
        err, text = call_tool(c, "check_text", {"text": "模型存在幽灵词元问题。"})
        check("迁移后插件词条可用", (not err) and "幽灵词元" in text, text[:200])
        err, text = call_tool(c, "lookup_term", {"query": "x"})
        err, text = call_tool(c, "no_such_tool", {})
        check("未知工具返回 isError", err and "Unknown tool" in text, text[:200])
    finally:
        c.close()
        shutil.rmtree(home, ignore_errors=True)


def test_structured_preflight_and_safe_replacements():
    env, home = fresh_env()
    dictionary = os.path.join(home, "custom.tsv")
    with open(dictionary, "w", encoding="utf-8") as f:
        f.write("机械胳膊\t机械臂\t明确同义词\treplace\n"
                "台账\t清单 / 记录\t按上下文选择\n")
    env["ZH_GUARD_DICT"] = dictionary
    c = McpClient(env)
    try:
        text = "机械胳膊。\n补上台账，台账中保留 `机械胳膊`。"
        response = c.request("tools/call", {
            "name": "check_text", "arguments": {"text": text},
        }).get("result", {})
        report = response.get("structuredContent", {})
        check("预检返回安全替换后的完整草稿",
              report.get("corrected_text") == "机械臂。\n补上台账，台账中保留 `机械胳膊`。",
              str(report)[:300])
        findings = report.get("findings", [])
        check("结构化结果记录全部非豁免命中和动作",
              [h.get("action") for h in findings] == ["replace", "rewrite", "rewrite"],
              str(findings)[:300])
        check("命中保留原文位置、行列及上下文",
              len(findings) == 3 and findings[1].get("start") == 8
              and findings[1].get("line") == 2 and findings[1].get("column") == 3
              and "补上台账" in findings[1].get("context", ""), str(findings)[:300])
        remaining = report.get("remaining_findings", [])
        check("替换后仍需按语境处理的规则不被机械执行",
              report.get("changed") is True and report.get("needs_rewrite") is True
              and [h.get("text") for h in remaining] == ["台账", "台账"], str(report)[:300])
        check("原有可读文本反馈仍然存在",
              bool(response.get("content")) and "台账" in response["content"][0]["text"],
              str(response)[:300])
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
            "name": "check_text", "arguments": {"text": "机械胳膊", "cwd": project},
        }).get("result", {})
        report = response.get("structuredContent", {})
        check("MCP 显式 cwd 与 hook 使用同一项目覆盖",
              report.get("corrected_text") == "机械胳膊"
              and len(report.get("findings", [])) == 1
              and report["findings"][0].get("expected") == "项目中保留原意",
              str(report)[:300])
        for args in [{"text": ""}, {"text": "测试", "cwd": "relative/path"}]:
            response = c.request("tools/call", {
                "name": "check_text", "arguments": args,
            }).get("result", {})
            check("无效预检输入显式返回工具错误（%s）" % args,
                  response.get("isError") is True, str(response)[:300])
    finally:
        c.close()
        shutil.rmtree(home, ignore_errors=True)


def test_add_term_action_is_preserved_and_validated():
    env, home = fresh_env()
    c = McpClient(env)
    try:
        err, text = call_tool(c, "add_term", {
            "term": "安全测试旧词", "expected": "安全新词", "action": "replace",
        })
        check("可添加显式安全替换规则", not err and "已添加" in text, text[:200])
        response = c.request("tools/call", {
            "name": "check_text", "arguments": {"text": "安全测试旧词"},
        }).get("result", {})
        check("新规则动作进入预检",
              response.get("structuredContent", {}).get("corrected_text") == "安全新词",
              str(response)[:300])
        for term, action in [("re:坏自动词", "replace"), ("坏动作词", "unknown")]:
            err, text = call_tool(c, "add_term", {
                "term": term, "expected": "新词", "action": action,
            })
            check("不合法的规则动作不写入（%s）" % term, err, text[:200])
        with open(os.path.join(home, "terminology.tsv"), encoding="utf-8") as f:
            content = f.read()
        check("错误规则没有污染用户词表",
              "坏自动词" not in content and "坏动作词" not in content, content[-200:])
    finally:
        c.close()
        shutil.rmtree(home, ignore_errors=True)


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
