#!/usr/bin/env python3
"""zh-guard term-dict MCP 服务器（MindForge style-rules-zh-cn 插件内）。

纯 Python stdio MCP 实现（JSON-RPC 2.0，零外部依赖，spec 原则 #5）。
与 L1/L2 共享同一份术语字典（合并加载 + re: 正则词条 + 安装迁移）。

工具面（拉模式知识层，不替代 L1 注入与 L2 检测）：
  lookup_term(query)   双向查词：直译词/期望写法/说明 子串匹配
  check_text(text)     草稿预检：共享检测、安全替换及结构化改写建议
  add_term(...)        数据飞轮：追加用户词条，下轮注入生效

设计原则（fail-open）：单个请求出错返回 isError，服务器不崩溃。
check_text / lookup_term 可显式传 cwd 加载项目词表。
"""
import json
import os
import sys

from zh_guard_common import (
    Rule,
    apply_replacements,
    ensure_user_dict,
    format_findings,
    guard_home,
    lint_text,
    load_rules,
)

PROTOCOL_VERSION = "2024-11-05"
MAX_LOOKUP_RESULTS = 20


def requested_cwd(args):
    cwd = args.get("cwd")
    if cwd is not None and (not isinstance(cwd, str) or not os.path.isabs(cwd)):
        raise ValueError("cwd 必须是项目目录的绝对路径")
    return cwd


# ---------- 工具实现 ----------

def tool_lookup_term(args):
    query = str(args.get("query", "")).strip().lower()
    if not query:
        return "query 为空。传入要查询的英文或中文术语。"
    entries = load_rules(requested_cwd(args))
    matched = []
    for rule in entries:
        term, good, note = rule.term, rule.expected, rule.note
        hay = " / ".join([term, good, note]).lower()
        if query in hay:
            display = term if not term.startswith("re:") else "re:" + term[3:]
            matched.append((display, good, note))
    if not matched:
        return "字典中无匹配词条（query=%s）。若无社区定译，保留英文原词。" % args.get("query")
    lines = []
    for term, good, note in matched[:MAX_LOOKUP_RESULTS]:
        line = "%s → %s" % (term, good)
        if note:
            line += "（%s）" % note
        lines.append(line)
    if len(matched) > MAX_LOOKUP_RESULTS:
        lines.append("（共 %d 条，仅列前 %d 条）" % (len(matched), MAX_LOOKUP_RESULTS))
    return "\n".join(lines)


def tool_check_text(args):
    text = args.get("text", "")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text 必须是非空中文草稿")
    rules = load_rules(requested_cwd(args))
    hits = lint_text(text, rules)
    corrected = apply_replacements(text, hits)
    remaining = lint_text(corrected, rules)
    report = {
        "corrected_text": corrected,
        "changed": corrected != text,
        "findings": [hit._asdict() for hit in hits],
        "remaining_findings": [hit._asdict() for hit in remaining],
        "needs_rewrite": bool(remaining),
    }
    if not hits:
        summary = "未命中直译词。"
    else:
        summary = "命中 %d 处，已执行标为 replace 的安全替换：\n%s" % (
            len(hits), format_findings(hits, 20),
        )
        summary += "\n安全替换后的草稿：\n" + corrected
        if remaining:
            summary += (
                "\n剩余命中请结合原句判断，合法用法保留；"
                "不要照抄候选列表或改写指令。修改后再次调用 check_text 复查。"
            )
    return {
        "content": [{"type": "text", "text": summary}],
        "structuredContent": report,
        "isError": False,
    }


def tool_add_term(args):
    term = str(args.get("term", "")).strip()
    expected = str(args.get("expected", "")).strip()
    note = str(args.get("note", "")).strip()
    if not term or not expected:
        raise ValueError("term 与 expected 必填。term 支持 re: 前缀（正则词条）。")
    # 清洗输入，保证 TSV 结构不被破坏。
    clean = lambda s: s.replace("\t", " ").replace("\n", " ").replace("\r", " ")
    term, expected, note = clean(term), clean(expected), clean(note)
    action = args.get("action", "rewrite")
    Rule(term, expected, note, action)
    ensure_user_dict()
    path = os.path.join(guard_home(), "terminology.tsv")
    row = "%s\t%s\t%s" % (term, expected, note)
    if "action" in args:
        row += "\t" + action
    with open(path, "a", encoding="utf-8") as f:
        f.write(row + "\n")
    return "已添加：%s → %s（写入 %s，下轮注入生效）" % (term, expected, path)


TOOLS = [
    {
        "name": "lookup_term",
        "description": (
            "查询术语的中文地道写法（zh-guard 术语字典）。写中文技术内容前，"
            "用英文原词或中文词查询：按上下文给出自然、易懂的说法，"
            "不硬套其他专业概念；无合适中文时返回「保留英文」。"
            "双向子串匹配直译词/期望写法/说明。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "英文或中文术语，如 slot key、病灶分析、ground truth",
                },
                "cwd": {"type": "string", "description": "项目目录绝对路径；可选，用于加载项目词表"},
            },
            "required": ["query"],
        },
    },
    {
        "name": "check_text",
        "description": (
            "交付前自查中文草稿中的直译词（zh-guard L2 同款检测，"
            "代码块与引号内提及豁免）。输出中文技术内容前调用，"
            "自动执行显式安全替换，返回 corrected_text、命中位置、原句上下文、"
            "规则动作及 remaining_findings。后者由助手结合语境改写，合法用法保留；"
            "修改后再次调用复查，不机械执行候选列表或改写指令。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "正式回答前的完整中文草稿"},
                "cwd": {"type": "string", "description": "项目目录绝对路径；可选，用于加载项目词表"},
            },
            "required": ["text"],
        },
    },
    {
        "name": "add_term",
        "description": (
            "向术语字典追加新直译 bad case（数据飞轮）。写入用户字典"
            " ~/.claude/MindForge/terminology.tsv，下轮注入即生效。"
            "term 支持 re: 前缀写正则词条（如 re:第\\s*\\d+\\s*刀）。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "term": {"type": "string", "description": "直译词；re: 前缀表示正则"},
                "expected": {"type": "string", "description": "期望写法"},
                "note": {"type": "string", "description": "简短说明（可选）"},
                "action": {
                    "type": "string", "enum": ["replace", "rewrite"],
                    "description": "默认 rewrite（结合原句改写）；明确无歧义的字面替换才标 replace",
                },
            },
            "required": ["term", "expected"],
        },
    },
]

TOOL_FUNCS = {
    "lookup_term": tool_lookup_term,
    "check_text": tool_check_text,
    "add_term": tool_add_term,
}


# ---------- MCP stdio 协议 ----------

def handle_request(msg):
    """返回响应 dict，或 None（通知/无需响应）。任何异常不抛出。"""
    try:
        method = msg.get("method", "")
        msg_id = msg.get("id")
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "protocolVersion": msg.get("params", {}).get(
                        "protocolVersion", PROTOCOL_VERSION
                    ),
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "term-dict", "version": "0.9.9"},
                },
            }
        if method == "ping":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {}}
        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": TOOLS}}
        if method == "tools/call":
            params = msg.get("params", {})
            name = params.get("name", "")
            func = TOOL_FUNCS.get(name)
            if func is None:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {
                        "content": [{"type": "text", "text": "Unknown tool: %s" % name}],
                        "isError": True,
                    },
                }
            result = func(params.get("arguments", {}) or {})
            if isinstance(result, str):
                result = {
                    "content": [{"type": "text", "text": result}],
                    "isError": False,
                }
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": result,
            }
        # 未知请求（有 id）→ 标准错误；通知（无 id）→ 忽略。
        if msg_id is not None:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": "Method not found: %s" % method},
            }
        return None
    except Exception as exc:
        if msg.get("id") is not None:
            return {
                "jsonrpc": "2.0",
                "id": msg["id"],
                "result": {
                    "content": [{"type": "text", "text": "internal error: %r" % exc}],
                    "isError": True,
                },
            }
        return None


def main():
    ensure_user_dict()
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except Exception:
            continue  # 非法行：跳过，不崩溃
        if not isinstance(msg, dict):
            continue
        resp = handle_request(msg)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
