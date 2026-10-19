#!/usr/bin/env python3
"""zh-guard L1 注入层：UserPromptSubmit hook（MindForge style-rules-zh-cn 插件内）。

职责：每轮用户输入触发，向会话注入中文术语规范（additionalContext），
在生成阶段压住直译术语。预防为主，零延迟。

字典（install 时迁移模型）：
  1. 插件自带 terminology.tsv 是发布源；
  2. 首次运行时若 ~/.claude/zh-guard/terminology.tsv 不存在，
     自动把插件自带字典复制过去（安装迁移，不覆盖已有用户词条）；
  3. 运行时合并读取插件自带 + 用户目录（用户条目优先），
     插件更新带来的新词条自动生效；
  4. ZH_GUARD_DICT 环境变量可指定单一字典文件（调试用）。

设计原则（fail-open）：任何异常一律静默退出 0，绝不阻断用户输入。
停用方式：export ZH_GUARD_OFF=1，或创建 OFF 文件（ZH_GUARD_HOME/ 或插件目录）。
"""
import json
import os
import re
import sys

try:
    HERE = os.path.dirname(os.path.abspath(__file__))

    def guard_home():
        return os.environ.get(
            "ZH_GUARD_HOME",
            os.path.join(os.path.expanduser("~"), ".claude", "zh-guard"),
        )

    def is_off():
        if os.environ.get("ZH_GUARD_OFF"):
            return True
        if os.path.exists(os.path.join(HERE, "OFF")):
            return True
        return os.path.exists(os.path.join(guard_home(), "OFF"))

    def ensure_user_dict():
        """安装迁移 + 版本同步。

        1. 用户字典不存在：复制插件自带字典过去；
        2. 已存在且 @sync 版本与自带字典一致：不动；
        3. 版本不一致（插件升级带来了新词条或改了写法）：以新版自带字典为底，
           再把用户自加的词条（第一列不在自带字典里的行）追加回去。

        用户对自带词条本身的本地改写会被新版覆盖——这是刻意的：字典要能迭代，
        否则「下一刀 → 下一个削减项」这种机器写法一旦被复制出厂就再也修不掉。
        想完全自己掌控字典，用 ZH_GUARD_DICT 指向自己的文件。
        """
        try:
            home = guard_home()
            user = os.path.join(home, "terminology.tsv")
            bundled = os.path.join(HERE, "terminology.tsv")
            if not os.path.exists(bundled):
                return
            with open(bundled, encoding="utf-8") as f:
                bundled_text = f.read()
            if not os.path.exists(user):
                os.makedirs(home, exist_ok=True)
                with open(user, "w", encoding="utf-8") as f:
                    f.write(bundled_text)
                return
            marker = ""
            for line in bundled_text.splitlines():
                if line.startswith("@sync") or line.startswith("# @sync"):
                    marker = line.strip()
                    break
            with open(user, encoding="utf-8") as f:
                user_text = f.read()
            if marker and marker in user_text:
                return
            bundled_keys = set()
            for line in bundled_text.splitlines():
                line = line.lstrip("\ufeff")
                if not line or line.startswith("#"):
                    continue
                key = line.split("\t")[0].strip()
                if key:
                    bundled_keys.add(key)
            kept = []
            for line in user_text.splitlines():
                line = line.lstrip("\ufeff")
                if not line or line.startswith("#"):
                    continue
                key = line.split("\t")[0].strip()
                if key and key not in bundled_keys:
                    kept.append(line)
            text = bundled_text if bundled_text.endswith("\n") else bundled_text + "\n"
            if kept:
                text += "\n# 以下为用户自加词条（字典升级时自动保留）\n" + "\n".join(kept) + "\n"
            with open(user, "w", encoding="utf-8") as f:
                f.write(text)
        except Exception:
            pass

    def dict_paths():
        """返回字典文件路径列表：插件自带在前，用户覆盖在后。"""
        override = os.environ.get("ZH_GUARD_DICT")
        if override:
            return [override] if os.path.exists(override) else []
        paths = []
        default = os.path.join(HERE, "terminology.tsv")
        if os.path.exists(default):
            paths.append(default)
        user = os.path.join(guard_home(), "terminology.tsv")
        if os.path.exists(user):
            paths.append(user)
        return paths

    def humanize_regex(pattern):
        """把正则渲染成人能读的形式：第\\s*\\d+\\s*刀 → 第N刀。"""
        try:
            p = pattern.replace("\\s*", "").replace("\\s+", " ")
            p = re.sub(r"\\d\+?", "N", p)
            return p.lstrip("^").rstrip("$") or pattern
        except Exception:
            return pattern

    def load_entries():
        """合并读字典，返回 [(直译词, 期望写法), ...]。用户条目优先。

        正则词条（re: 前缀）以模式串形式展示给模型。
        """
        merged = {}
        user_only = []
        first = True
        for path in dict_paths():
            with open(path, encoding="utf-8-sig") as f:
                for line in f:
                    line = line.rstrip("\n").lstrip("\ufeff")
                    if not line or line.startswith("#"):
                        continue
                    parts = [p.strip() for p in line.split("\t")]
                    if not parts or not parts[0]:
                        continue
                    term = parts[0]
                    if term.startswith("re:"):
                        term = humanize_regex(term[3:])
                    target = parts[1] if len(parts) >= 2 else ""
                    if not first and term not in merged:
                        user_only.append((term, target))
                    merged[term] = target
            first = False
        # 用户自加的词条排在最前面：超出 MAX_SHOWN 时先牺牲自带词条。
        rest = [(k, v) for k, v in merged.items() if k not in dict(user_only)]
        return user_only + rest

    MAX_SHOWN = 30

    def build_context(entries):
        shown = entries[:MAX_SHOWN]
        pairs = "、".join(
            "%s→%s" % (bad, good) if good else bad for bad, good in shown
        )
        more = "" if len(entries) <= MAX_SHOWN else (
            "（仅列前 %d 条，其余用 term-dict MCP 的 lookup_term 查询）" % MAX_SHOWN
        )
        return (
            "【中文术语规范（自动注入）】\n"
            "1. 术语有中文社区定译就用定译：ablation study=消融实验，"
            "hallucination=幻觉，prompt=提示词。\n"
            "2. 术语没有通用定译就保留英文原词：token、agent、hook、embedding、"
            "ghost token。中英混排是中文技术写作的惯例。\n"
            "3. 禁止字面直译英文黑话。\n"
            "4. 以下直译词禁用，按箭头右侧的写法表达；右侧是高亮条款所指的中文措辞，"
            "拿不准就保留英文原词："
            + (pairs + more if pairs else "暂无") +
            "\n5. 措辞要像人在说话：说「剩下的待办」「发现的问题」「这儿有个 bug」，"
            "别端着写成「遗留缺口」「结构性缺陷」这类从英文句型硬搬过来的词。"
            "一句话里如果名词叠着名词，就拆成短句直说。"
        )

    def main():
        if is_off():
            sys.exit(0)
        ensure_user_dict()
        raw = sys.stdin.read()
        if not raw.strip():
            sys.exit(0)
        # 只读取输入验证可用性，内容本身不参与注入。
        try:
            json.loads(raw)
        except Exception:
            sys.exit(0)
        ctx = build_context(load_entries())
        print(json.dumps({
            "continue": True,
            "hookSpecificOutput": {
                "hookEventName": "UserPromptSubmit",
                "additionalContext": ctx,
            },
        }, ensure_ascii=False))

    main()
except SystemExit:
    raise
except Exception:
    # fail-open：任何未预期错误都放行。
    sys.exit(0)
