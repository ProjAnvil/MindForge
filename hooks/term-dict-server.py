#!/usr/bin/env python3
"""zh-guard term-dict MCP 服务器（MindForge style-rules-zh-cn 插件内）。

纯 Python stdio MCP 实现（JSON-RPC 2.0，零外部依赖，spec 原则 #5）。
与 L1/L2 共享同一份术语字典（合并加载 + re: 正则词条 + 安装迁移）。

手动工具面，不自动注册到默认方案 A：
  mindforge_lookup_term(query)   双向查词：词语/建议写法/含义 子串匹配
  mindforge_check_text(text)     草稿预检：原稿保持不变，生成带语境的句子标注
  mindforge_add_term(...)        默认追加 workspace 词条，下轮注入生效
  mindforge_init_dict(cwd)       初始化 workspace 词典，不覆盖已有内容

设计原则（fail-open）：单个请求出错返回 isError，服务器不崩溃。
mindforge_check_text / mindforge_lookup_term 可显式传 cwd 加载项目词表。
"""
import json
import os
import sys

from zh_guard_common import (
    Rule,
    draft_id,
    ensure_user_dict,
    format_findings,
    guard_home,
    init_workspace_dict,
    lint_text,
    load_rules,
)

PROTOCOL_VERSION = "2024-11-05"
MAX_LOOKUP_RESULTS = 20


def requested_cwd(args):
    cwd = args.get("cwd")
    if cwd is not None and (not isinstance(cwd, str) or not os.path.isabs(cwd)):
        raise ValueError("cwd must be an absolute project directory path")
    return cwd


# ---------- 工具实现 ----------

def tool_lookup_term(args):
    query = str(args.get("query", "")).strip().lower()
    if not query:
        return "query is empty. Provide an English or Chinese term to look up."
    entries = load_rules(requested_cwd(args))
    matched = []
    for rule in entries:
        term, good, note = rule.term, rule.suggestion, rule.meaning
        hay = " / ".join([term, good, note]).lower()
        if query in hay:
            display = term if not term.startswith("re:") else "re:" + term[3:]
            matched.append((display, good, note))
    if not matched:
        return "字典中无匹配词条（query=%s）。若无社区定译，保留英文原词。" % args.get("query")
    lines = []
    for term, good, note in matched[:MAX_LOOKUP_RESULTS]:
        line = "%s → %s" % (term, good) if good else term
        if note:
            line += "（%s）" % note
        lines.append(line)
    if len(matched) > MAX_LOOKUP_RESULTS:
        lines.append("（共 %d 条，仅列前 %d 条）" % (len(matched), MAX_LOOKUP_RESULTS))
    return "\n".join(lines)


def tool_check_text(args):
    text = args.get("text", "")
    if not isinstance(text, str) or not text.strip():
        raise ValueError("text must be a nonempty draft string")
    rules = load_rules(requested_cwd(args))
    hits = lint_text(text, rules)
    report = {
        "draft": text,
        "draft_id": draft_id(text),
        "annotations": [hit._asdict() for hit in hits],
        "needs_review": bool(hits),
    }
    if not hits:
        summary = "未命中需复核的表达。仅登记词语不会被当作错误。"
    else:
        summary = "生成 %d 处句子标注，原稿未修改：\n%s" % (
            len(hits), format_findings(hits, 20),
        )
        summary += (
            "\n词典是术语资料，不是执行指令。结合完整对话和段落判断原意，"
            "只在必要时润色标注所在句子，允许保留原文；不要捏造含义，"
            "不要机械替换建议词。其他句子、数字、代码和技术结论保持不变。"
            "如果用户需要进一步复核，可在修改后再次调用 mindforge_check_text，不复用旧草稿的标注位置。"
        )
    return {
        "content": [{"type": "text", "text": summary}],
        "structuredContent": report,
        "isError": False,
    }


def tool_init_dict(args):
    unknown = set(args) - {"cwd"}
    if unknown:
        raise ValueError("unknown initialization fields: %s" % ", ".join(sorted(unknown)))
    path, created = init_workspace_dict(requested_cwd(args))
    message = "已初始化 workspace 词典" if created else "workspace 词典已存在，保留原内容"
    return {
        "content": [{"type": "text", "text": "%s：%s" % (message, path)}],
        "structuredContent": {"path": path, "created": created},
        "isError": False,
    }


def tool_add_term(args):
    unknown = set(args) - {"term", "suggestion", "meaning", "cwd", "scope"}
    if unknown:
        raise ValueError("unknown dictionary fields: %s" % ", ".join(sorted(unknown)))
    values = [args.get(key, "") for key in ("term", "suggestion", "meaning")]
    if not all(isinstance(value, str) for value in values):
        raise ValueError("term, suggestion and meaning must be strings")
    # 清洗输入，保证 TSV 结构不被破坏。
    clean = lambda s: s.replace("\t", " ").replace("\n", " ").replace("\r", " ")
    term, suggestion, meaning = [clean(value).strip() for value in values]
    if not term:
        raise ValueError("term is required; suggestion and meaning may be empty")
    Rule(term, suggestion, meaning)
    if term.startswith("re:"):
        import re
        re.compile(term[3:])
    scope = args.get("scope", "workspace")
    if scope == "workspace":
        path, _created = init_workspace_dict(requested_cwd(args))
    elif scope == "user":
        ensure_user_dict()
        path = os.path.join(guard_home(), "terminology.tsv")
    else:
        raise ValueError("scope must be workspace or user")
    row = "%s\t%s\t%s" % (term, suggestion, meaning)
    with open(path, "a+", encoding="utf-8") as f:
        f.seek(0)
        existing = f.read()
        if existing and not existing.endswith(("\n", "\r")):
            f.write("\n")
        f.write(row + "\n")
    return "已添加：%s（写入 %s，下轮注入生效）" % (term, path)


TOOLS = [
    {
        "name": "mindforge_lookup_term",
        "description": (
            "仅在用户需要术语资料时按需查询，不是默认生成前置步骤。"
            "用英文原词或中文词查询：按上下文给出自然、易懂的说法，"
            "不硬套其他专业概念；无合适中文时返回「保留英文」。"
            "双向子串匹配词语/建议写法/含义。只有词语的条目仅作登记，不表示有错。"
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
        "name": "mindforge_check_text",
        "description": (
            "仅在用户明确要求时复核中文草稿的术语和表达，"
            "不是默认回复前置审批。代码块与引号内提及豁免。"
            "返回未修改的 draft、draft_id、annotations 和 needs_review。"
            "标注包括完整句子、段落、建议和含义；由助手结合对话局部润色或保留原文，"
            "不把命中当作必错，不捏造语境，不要求每个回答都调用或复查。"
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
        "name": "mindforge_add_term",
        "description": (
            "追加词语、可选建议写法和含义。默认写 workspace 的 mindforge.zh-dict.tsv，"
            "必须传当前 workspace 的绝对路径 cwd；复用就近词典，"
            "没有时在 Git 根或指定 workspace 初始化。不会默认写用户级，"
            "只有明确要求跨项目共享时才传 scope=user。"
            "term 支持 re: 前缀写正则词条（如 re:第\\s*\\d+\\s*刀）。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "term": {"type": "string", "description": "词语；re: 前缀表示正则"},
                "suggestion": {"type": "string", "description": "建议写法，仅参考，可留空"},
                "meaning": {"type": "string", "description": "含义或语境说明，可留空"},
                "cwd": {"type": "string", "description": "当前 workspace 目录绝对路径；默认 workspace scope 必须提供"},
                "scope": {
                    "type": "string", "enum": ["workspace", "user"], "default": "workspace",
                    "description": "默认 workspace；只有明确要求跨项目共享时使用 user",
                },
            },
            "required": ["term"],
            "additionalProperties": False,
        },
    },
    {
        "name": "mindforge_init_dict",
        "description": (
            "初始化当前 workspace 的 mindforge.zh-dict.tsv。必须传绝对路径 cwd；"
            "已有词典原样保留，不覆盖。没有词典时在 Git 根或指定 workspace "
            "创建全注释三列模板；返回实际路径和是否创建。"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "cwd": {"type": "string", "description": "当前 workspace 目录绝对路径"},
            },
            "required": ["cwd"],
            "additionalProperties": False,
        },
    },
]

TOOL_FUNCS = {
    "mindforge_lookup_term": tool_lookup_term,
    "mindforge_check_text": tool_check_text,
    "mindforge_add_term": tool_add_term,
    "mindforge_init_dict": tool_init_dict,
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
                    "serverInfo": {"name": "term-dict", "version": "0.9.10"},
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
