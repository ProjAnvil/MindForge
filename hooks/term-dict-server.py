#!/usr/bin/env python3
"""zh-guard term-dict MCP 服务器（MindForge style-rules-zh-cn 插件内）。

纯 Python stdio MCP 实现（JSON-RPC 2.0，零外部依赖，spec 原则 #5）。
与 L1/L2 共享同一份术语字典（合并加载 + re: 正则词条 + 安装迁移）。

工具面（拉模式知识层，不替代 L1 注入与 L2 检测）：
  lookup_term(query)   双向查词：直译词/期望写法/说明 子串匹配
  check_text(text)     交付前自查：L2 同款检测（豁免区 + 正则）
  add_term(...)        数据飞轮：追加用户词条，下轮注入生效

设计原则（fail-open）：单个请求出错返回 isError，服务器不崩溃。
"""
import json
import os
import re
import sys

from zh_guard_common import (
    ensure_user_dict,
    guard_home,
    load_note_entries,
    strip_code,
)

PROTOCOL_VERSION = "2024-11-05"
MAX_LOOKUP_RESULTS = 20


def load_entries():
    """合并读取 [(直译词, 期望写法, 说明), ...]。更具体层优先。

    MCP 服务器是常驻进程，拿不到会话 cwd，项目级词典不参与
    （hook 层的 L1/L2/文件检测仍三级生效）。
    """
    return load_note_entries(None)


def detect(text):
    """返回 [(命中词, 期望写法), ...]。正则词条引用实际命中串。"""
    entries = load_entries()
    stripped = strip_code(text)
    hits = []
    for term, good, _note in entries:
        if term.startswith("re:"):
            try:
                m = re.search(term[3:], stripped)
            except re.error:
                continue
            if m:
                hits.append((m.group(0), good))
        elif term in stripped:
            hits.append((term, good))
    return hits


# ---------- 工具实现 ----------

def tool_lookup_term(args):
    query = str(args.get("query", "")).strip().lower()
    if not query:
        return "query 为空。传入要查询的英文或中文术语。"
    entries = load_entries()
    matched = []
    for term, good, note in entries:
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
    text = str(args.get("text", ""))
    if not text.strip():
        return "text 为空。"
    hits = detect(text)
    if not hits:
        return "未命中直译词。"
    lines = ["命中 %d 处直译词，修正后再交付：" % len(hits)]
    for bad, good in hits[:20]:
        lines.append("  %s → %s" % (bad, good))
    return "\n".join(lines)


def tool_add_term(args):
    term = str(args.get("term", "")).strip()
    expected = str(args.get("expected", "")).strip()
    note = str(args.get("note", "")).strip()
    if not term or not expected:
        return "term 与 expected 必填。term 支持 re: 前缀（正则词条）。"
    # 清洗输入，保证 TSV 结构不被破坏。
    clean = lambda s: s.replace("\t", " ").replace("\n", " ").replace("\r", " ")
    term, expected, note = clean(term), clean(expected), clean(note)
    ensure_user_dict()
    path = os.path.join(guard_home(), "terminology.tsv")
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write("%s\t%s\t%s\n" % (term, expected, note))
    except Exception as exc:
        return "写入失败：%r" % exc
    return "已添加：%s → %s（写入 %s，下轮注入生效）" % (term, expected, path)


TOOLS = [
    {
        "name": "lookup_term",
        "description": (
            "查询术语的中文地道写法（zh-guard 术语字典）。写中文技术内容前，"
            "用英文原词或中文词查询：有社区定译返回定译（ablation study=消融实验），"
            "无定译的返回「保留英文」。双向子串匹配直译词/期望写法/说明。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "英文或中文术语，如 ablation、病灶、ground truth",
                }
            },
            "required": ["query"],
        },
    },
    {
        "name": "check_text",
        "description": (
            "交付前自查中文草稿中的直译词（zh-guard L2 同款检测，"
            "代码块与引号内提及豁免）。输出中文技术内容前调用，"
            "命中会列出 直译词→期望写法。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "待自查的中文草稿"}
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
                    "serverInfo": {"name": "term-dict", "version": "0.9.6"},
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
            text = func(params.get("arguments", {}) or {})
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [{"type": "text", "text": text}],
                    "isError": False,
                },
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
