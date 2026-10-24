#!/usr/bin/env python3
"""Shared terminology matching and safe replacement tests."""
import io
import os
import tempfile
import unittest
from contextlib import contextmanager, redirect_stderr
from pathlib import Path

import zh_guard_common as guard


@contextmanager
def environment(**values):
    before = os.environ.copy()
    try:
        for key, value in values.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        yield
    finally:
        os.environ.clear()
        os.environ.update(before)


class MatchingTests(unittest.TestCase):
    def test_offsets_context_and_repeated_matches(self):
        text = "第一行。\n机械胳膊和机械胳膊。"
        rule = guard.Rule("机械胳膊", "机械臂", action="replace")
        hits = guard.lint_text(text, [rule])
        self.assertEqual([(h.start, h.end, h.line, h.column) for h in hits],
                         [(5, 9, 2, 1), (10, 14, 2, 6)])
        self.assertEqual([h.text for h in hits], ["机械胳膊", "机械胳膊"])
        self.assertIn("机械胳膊和机械胳膊", hits[0].context)
        self.assertEqual(guard.apply_replacements(text, hits), "第一行。\n机械臂和机械臂。")

    def test_leftmost_longest_non_overlapping_matches(self):
        rules = [
            guard.Rule("缺口", "剩下的待办"),
            guard.Rule("遗留缺口", "还没做完的部分"),
        ]
        hits = guard.lint_text("还有遗留缺口，也有缺口。", rules)
        self.assertEqual([h.text for h in hits], ["遗留缺口", "缺口"])
        self.assertEqual([h.start for h in hits], [2, 9])

    def test_rewrite_wins_identical_span_over_replace(self):
        rules = [
            guard.Rule("机械胳膊", "机械臂", action="replace"),
            guard.Rule("re:机械胳膊", "按上下文改写"),
        ]
        text = "机械胳膊"
        hits = guard.lint_text(text, rules)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].action, "rewrite")
        self.assertEqual(guard.apply_replacements(text, hits), text)

    def test_regex_reports_every_actual_match(self):
        rule = guard.Rule(r"re:第\s*\d+\s*刀", "第 N 处精简")
        hits = guard.lint_text("第3刀，然后第 12 刀。", [rule])
        self.assertEqual([(h.text, h.start, h.end) for h in hits],
                         [("第3刀", 0, 3), ("第 12 刀", 6, 12)])

    def test_invalid_regex_is_reported_and_skipped(self):
        rules = [guard.Rule("re:[", "坏规则"), guard.Rule("问题", "检查原因")]
        stderr = io.StringIO()
        with redirect_stderr(stderr):
            hits = guard.lint_text("问题", rules)
        self.assertEqual([h.text for h in hits], ["问题"])
        self.assertIn("re:[", stderr.getvalue())

    def test_protected_text_is_not_changed(self):
        text = (
            "机械胳膊 `机械胳膊` ``机械胳膊`` 「机械胳膊」 “机械胳膊”\n"
            "```python\n机械胳膊\n```\n"
            "~~~text\n机械胳膊\n~~~\n"
            "机械胳膊"
        )
        rules = [guard.Rule("机械胳膊", "机械臂", action="replace")]
        hits = guard.lint_text(text, rules)
        self.assertEqual(len(hits), 2)
        result = guard.apply_replacements(text, hits)
        self.assertTrue(result.startswith("机械臂 `机械胳膊`"))
        self.assertTrue(result.endswith("\n机械臂"))
        self.assertIn("```python\n机械胳膊\n```", result)
        self.assertIn("~~~text\n机械胳膊\n~~~", result)

    def test_unclosed_and_long_fences_remain_protected(self):
        text = "````text\n机械胳膊\n```\n机械胳膊\n"
        rule = guard.Rule("机械胳膊", "机械臂", action="replace")
        self.assertEqual(guard.lint_text(text, [rule]), [])

    def test_fences_inside_lists_indentation_and_blockquotes(self):
        rule = guard.Rule("机械胳膊", "机械臂", action="replace")
        for prefix, closing in [
            ("    ```text\n", "    ```\n"),
            ("- ```text\n", "  ```\n"),
            ("> ```text\n", "> ```\n"),
        ]:
            with self.subTest(prefix=prefix):
                text = prefix + "机械胳膊\n" + closing + "机械胳膊"
                hits = guard.lint_text(text, [rule])
                self.assertEqual([h.start for h in hits], [len(text) - 4])
        text = "```text\n> ```\n机械胳膊\n```\n机械胳膊"
        self.assertEqual(len(guard.lint_text(text, [rule])), 1)

    def test_matches_cannot_bridge_a_protected_region(self):
        rules = [
            guard.Rule("病灶", "问题原因"),
            guard.Rule("re:病.*灶", "问题原因"),
        ]
        self.assertEqual(guard.lint_text("病`示例`灶", rules), [])

    def test_safe_replacements_are_not_cascaded(self):
        rules = [
            guard.Rule("甲词", "乙词", action="replace"),
            guard.Rule("乙词", "丙词", action="replace"),
            guard.Rule("病灶分析", "分析问题原因"),
        ]
        text = "甲词，做病灶分析。"
        self.assertEqual(guard.apply_replacements(text, guard.lint_text(text, rules)),
                         "乙词，做病灶分析。")

    def test_contextual_rules_are_never_directly_replaced(self):
        rules = [guard.Rule("台账", "清单 / 记录"), guard.Rule("缺口", "剩下的待办")]
        text = "医生确认了缺口，补上台账。"
        hits = guard.lint_text(text, rules)
        self.assertEqual(guard.apply_replacements(text, hits), text)
        self.assertTrue(all(h.action == "rewrite" for h in hits))

    def test_rule_validation_prevents_unsafe_automation(self):
        for term, target, action in [
            ("词", "结果", "unknown"),
            ("re:词", "结果", "replace"),
            ("词", "候选一 / 候选二", "replace"),
            ("词", "", "replace"),
            ("词", "直接给结论", "replace"),
        ]:
            with self.subTest(term=term, target=target, action=action):
                with self.assertRaises(ValueError):
                    guard.Rule(term, target, action=action)

    def test_fence_state_survives_display_batches(self):
        masked, fence = guard.mask_protected("```python\n机械胳膊\n")
        self.assertEqual(fence, "```")
        self.assertNotIn("机械胳膊", masked)
        masked, fence = guard.mask_protected("机械胳膊\n```\n机械胳膊\n", fence)
        self.assertEqual(fence, "")
        self.assertEqual(masked.count("机械胳膊"), 1)


class DictionaryTests(unittest.TestCase):
    def test_bundled_rules_opt_in_to_conservative_automation(self):
        with environment(ZH_GUARD_DICT=str(Path(__file__).with_name("terminology.tsv"))):
            rules = {rule.term: rule for rule in guard.load_rules()}
        for term in ["机械胳膊", "机器人胳膊", "大的语言模型", "槽键"]:
            self.assertEqual(rules[term].action, "replace", term)
        for term in ["病灶实验", "病灶分析", "缺口", "台账", "锚定", "引擎盖下"]:
            self.assertEqual(rules[term].action, "rewrite", term)
        self.assertTrue(all(rule.action == "rewrite" for rule in rules.values()
                            if rule.term.startswith("re:")))

    def test_three_column_rules_default_to_rewrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dict.tsv"
            path.write_text("旧词\t候选写法\t说明\n明确旧词\t新词\t说明\treplace\n",
                            encoding="utf-8")
            with environment(ZH_GUARD_DICT=str(path)):
                rules = guard.load_rules()
        self.assertEqual([(r.term, r.action) for r in rules],
                         [("旧词", "rewrite"), ("明确旧词", "replace")])

    def test_project_override_can_disable_safe_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home, project = base / "home", base / "project"
            home.mkdir()
            project.mkdir()
            (project / ".git").mkdir()
            (home / "terminology.tsv").write_text(
                "自加旧词\t用户写法\t说明\treplace\n", encoding="utf-8")
            (project / "mindforge.zh-dict.tsv").write_text(
                "自加旧词\t项目按语境改写\t说明\n", encoding="utf-8")
            with environment(ZH_GUARD_HOME=str(home), ZH_GUARD_DICT=None):
                rule = next(r for r in guard.load_rules(str(project))
                            if r.term == "自加旧词")
            self.assertEqual((rule.expected, rule.action), ("项目按语境改写", "rewrite"))

    def test_invalid_action_in_dictionary_is_explicit_error(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dict.tsv"
            path.write_text("旧词\t新词\t说明\tunknown\n", encoding="utf-8")
            with environment(ZH_GUARD_DICT=str(path)):
                with self.assertRaisesRegex(ValueError, "unknown"):
                    guard.load_rules()


if __name__ == "__main__":
    unittest.main()
