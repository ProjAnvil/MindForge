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
import shutil
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
        """安装迁移：用户字典不存在时，从插件自带字典复制过去。绝不覆盖。"""
        try:
            home = guard_home()
            user = os.path.join(home, "terminology.tsv")
            bundled = os.path.join(HERE, "terminology.tsv")
            if not os.path.exists(user) and os.path.exists(bundled):
                os.makedirs(home, exist_ok=True)
                shutil.copyfile(bundled, user)
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

    def load_bad_terms():
        """合并读字典第一列，返回去重直译词列表。用户条目优先。

        正则词条（re: 前缀）以模式串形式展示给模型。
        """
        seen = {}
        for path in dict_paths():
            with open(path, encoding="utf-8-sig") as f:
                for line in f:
                    line = line.rstrip("\n").lstrip("\ufeff")
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split("\t")
                    if parts and parts[0].strip():
                        term = parts[0].strip()
                        if term.startswith("re:"):
                            term = term[3:]
                        seen[term] = True
        return list(seen.keys())

    def build_context(terms):
        bad_list = "、".join(terms[:40])
        more = "" if len(terms) <= 40 else "（仅列前 40 条，完整表见 ~/.claude/zh-guard/ 与插件目录）"
        return (
            "【中文术语规范（自动注入）】\n"
            "1. 术语有中文社区定译就用定译：ablation study=消融实验，"
            "hallucination=幻觉，prompt=提示词。\n"
            "2. 术语没有通用定译就保留英文原词：token、agent、hook、embedding、"
            "ghost token。中英混排是中文技术写作的惯例。\n"
            "3. 禁止字面直译英文黑话。\n"
            "4. 以下直译词禁用（括号内为期望写法）："
            + (bad_list + more if bad_list else "暂无")
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
        ctx = build_context(load_bad_terms())
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
