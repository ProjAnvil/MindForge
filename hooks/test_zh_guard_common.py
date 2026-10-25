#!/usr/bin/env python3
"""Shared glossary loading and contextual sentence annotation tests."""
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
    def test_glossary_only_terms_do_not_trigger_rewrites(self):
        rule = guard.Rule("星环")
        self.assertEqual(guard.lint_text("星环正在运行。", [rule]), [])

    def test_meaning_only_entry_produces_a_sentence_annotation(self):
        text = "前一句。\n小说里，他举起机械胳膊挡住攻击。\n这一段描述角色的身体。\n\n另一段。"
        rule = guard.Rule("机械胳膊", "", "科幻角色的身体部件，不是工业设备")
        hits = guard.lint_text(text, [rule])
        self.assertEqual(len(hits), 1)
        hit = hits[0]
        self.assertEqual(hit.sentence, "小说里，他举起机械胳膊挡住攻击。")
        self.assertEqual(text[hit.sentence_start:hit.sentence_end], hit.sentence)
        self.assertEqual(hit.context, text.split("\n\n")[0])
        self.assertEqual(hit.meaning, "科幻角色的身体部件，不是工业设备")
        self.assertEqual(hit.suggestion, "")
        message = guard.format_findings(hits)
        self.assertIn(hit.sentence, message)
        self.assertIn(rule.meaning, message)
        self.assertNotIn("机械胳膊→", message)

    def test_annotations_identify_drafts_and_each_occurrence(self):
        rule = guard.Rule("病灶分析", "", "排查根因")
        text = "先做病灶分析，再做病灶分析。"
        hits = guard.lint_text(text, [rule])
        self.assertEqual(len(hits), 2)
        self.assertEqual(hits[0].rule_id, hits[1].rule_id)
        self.assertEqual(hits[0].draft_id, hits[1].draft_id)
        self.assertNotEqual(hits[0].annotation_id, hits[1].annotation_id)
        self.assertEqual(hits, guard.lint_text(text, [rule]))
        changed = guard.lint_text("加一句。" + text, [rule])[0]
        self.assertEqual(hits[0].rule_id, changed.rule_id)
        self.assertNotEqual(hits[0].draft_id, changed.draft_id)
        self.assertNotEqual(hits[0].annotation_id, changed.annotation_id)

    def test_sentence_context_respects_punctuation_and_protected_text(self):
        rule = guard.Rule("病灶分析", "", "排查根因")
        for text, sentence in [
            ("前句！“先看日志”，再做病灶分析？下一句。", "“先看日志”，再做病灶分析？"),
            ("说明：https://x.test/a。病灶分析结束。", "病灶分析结束。"),
            ("Value is 1.25. Review 病灶分析 now. Next.", "Review 病灶分析 now."),
            ("先看 `x.y。z`，再做病灶分析。下一句。", "先看 `x.y。z`，再做病灶分析。"),
            ("- 做病灶分析\n- 下一项", "- 做病灶分析"),
            ("前句。\r\n做病灶分析。\r\n", "做病灶分析。"),
            ("先做病灶分析（参考“日志。输出”），再比较。", "先做病灶分析（参考“日志。输出”），再比较。"),
        ]:
            with self.subTest(text=text):
                hit = guard.lint_text(text, [rule])[0]
                self.assertEqual(hit.sentence, sentence)
                self.assertEqual(text[hit.sentence_start:hit.sentence_end], sentence)

    def test_offsets_context_and_repeated_matches(self):
        text = "第一行。\n机械胳膊和机械胳膊。"
        rule = guard.Rule("机械胳膊", "机械臂")
        hits = guard.lint_text(text, [rule])
        self.assertEqual([(h.start, h.end, h.line, h.column) for h in hits],
                         [(5, 9, 2, 1), (10, 14, 2, 6)])
        self.assertEqual([h.text for h in hits], ["机械胳膊", "机械胳膊"])
        self.assertIn("机械胳膊和机械胳膊", hits[0].context)
        self.assertEqual([h.suggestion for h in hits], ["机械臂", "机械臂"])

    def test_leftmost_longest_non_overlapping_matches(self):
        rules = [
            guard.Rule("缺口", "剩下的待办"),
            guard.Rule("遗留缺口", "还没做完的部分"),
        ]
        hits = guard.lint_text("还有遗留缺口，也有缺口。", rules)
        self.assertEqual([h.text for h in hits], ["遗留缺口", "缺口"])
        self.assertEqual([h.start for h in hits], [2, 9])

    def test_identical_literal_and_regex_spans_are_not_duplicated(self):
        rules = [
            guard.Rule("机械胳膊", "机械臂"),
            guard.Rule("re:机械胳膊", "按上下文改写"),
        ]
        text = "机械胳膊"
        hits = guard.lint_text(text, rules)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].text, text)

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
        rules = [guard.Rule("机械胳膊", "机械臂")]
        hits = guard.lint_text(text, rules)
        self.assertEqual(len(hits), 2)
        self.assertEqual(hits[0].start, 0)
        self.assertEqual(hits[1].start, len(text) - 4)

    def test_unclosed_and_long_fences_remain_protected(self):
        text = "````text\n机械胳膊\n```\n机械胳膊\n"
        rule = guard.Rule("机械胳膊", "机械臂")
        self.assertEqual(guard.lint_text(text, [rule]), [])

    def test_fences_inside_lists_indentation_and_blockquotes(self):
        rule = guard.Rule("机械胳膊", "机械臂")
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

    def test_rule_requires_an_actual_term(self):
        for term in ["", "   ", "# comment", "@sync 1"]:
            with self.subTest(term=term), self.assertRaises(ValueError):
                guard.Rule(term)

    def test_fence_state_survives_display_batches(self):
        masked, fence = guard.mask_protected("```python\n机械胳膊\n")
        self.assertEqual(fence, "```")
        self.assertNotIn("机械胳膊", masked)
        masked, fence = guard.mask_protected("机械胳膊\n```\n机械胳膊\n", fence)
        self.assertEqual(fence, "")
        self.assertEqual(masked.count("机械胳膊"), 1)


class DictionaryTests(unittest.TestCase):
    def test_workspace_init_respects_git_file_boundaries(self):
        with tempfile.TemporaryDirectory() as directory:
            outer = Path(directory)
            project = outer / "project"
            child = project / "src"
            child.mkdir(parents=True)
            (outer / guard.PROJECT_DICT_NAME).write_text("外部词\t不应写入\n", encoding="utf-8")
            (project / ".git").write_text("gitdir: /unused/worktree\n", encoding="utf-8")
            self.assertIsNone(guard.find_project_dict(str(child)))
            path, created = guard.init_workspace_dict(str(child))
            self.assertEqual(path, str(project / guard.PROJECT_DICT_NAME))
            self.assertTrue(created)
            self.assertNotIn("外部词", Path(path).read_text(encoding="utf-8"))
            self.assertEqual(guard.find_project_dict(str(child)), path)

    def test_workspace_init_reuses_nearest_existing_dictionary(self):
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            child = project / "src"
            child.mkdir()
            (project / ".git").mkdir()
            (project / guard.PROJECT_DICT_NAME).write_text("# root\n", encoding="utf-8")
            local = child / guard.PROJECT_DICT_NAME
            local.write_text("# local\n", encoding="utf-8")
            path, created = guard.init_workspace_dict(str(child))
            self.assertEqual((path, created), (str(local), False))
            self.assertEqual(local.read_text(encoding="utf-8"), "# local\n")

    def test_optional_tsv_columns_preserve_legacy_meanings(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dict.tsv"
            path.write_text(
                "星环\n机械胳膊\t\t科幻人物的身体部件\n"
                "旧词\t偏好写法\n另一个词\t建议\t语境\n", encoding="utf-8",
            )
            with environment(ZH_GUARD_DICT=str(path)):
                rules = guard.load_rules()
        self.assertEqual([(r.term, r.suggestion, r.meaning) for r in rules], [
            ("星环", "", ""),
            ("机械胳膊", "", "科幻人物的身体部件"),
            ("旧词", "偏好写法", ""),
            ("另一个词", "建议", "语境"),
        ])

    def test_glossary_project_override_suppresses_bundled_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            (base / ".git").mkdir()
            (base / "mindforge.zh-dict.tsv").write_text("机械胳膊\n", encoding="utf-8")
            with environment(ZH_GUARD_HOME=str(base / "home"), ZH_GUARD_DICT=None):
                hits = guard.lint_text("机械胳膊举起。", cwd=str(base))
            self.assertEqual(hits, [])

    def test_bundled_terms_provide_contextual_suggestions(self):
        with environment(ZH_GUARD_DICT=str(Path(__file__).with_name("terminology.tsv"))):
            rules = {rule.term: rule for rule in guard.load_rules()}
        self.assertEqual(rules["机械胳膊"].suggestion, "机械臂")
        self.assertIn("语境", rules["机械胳膊"].meaning)

    def test_three_column_rules_preserve_guidance(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dict.tsv"
            path.write_text("旧词\t候选写法\t说明\n明确旧词\t新词\t说明\n",
                            encoding="utf-8")
            with environment(ZH_GUARD_DICT=str(path)):
                rules = guard.load_rules()
        self.assertEqual([(r.term, r.suggestion) for r in rules],
                         [("旧词", "候选写法"), ("明确旧词", "新词")])

    def test_project_override_can_disable_safe_replacement(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home, project = base / "home", base / "project"
            home.mkdir()
            project.mkdir()
            (project / ".git").mkdir()
            (home / "terminology.tsv").write_text(
                "自加旧词\t用户写法\t说明\n", encoding="utf-8")
            (project / "mindforge.zh-dict.tsv").write_text(
                "自加旧词\t项目按语境改写\t说明\n", encoding="utf-8")
            with environment(ZH_GUARD_HOME=str(home), ZH_GUARD_DICT=None):
                rule = next(r for r in guard.load_rules(str(project))
                            if r.term == "自加旧词")
            self.assertEqual(rule.suggestion, "项目按语境改写")

    def test_extra_columns_are_explicit_errors(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dict.tsv"
            path.write_text("旧词\t新词\t说明\tunknown\n", encoding="utf-8")
            with environment(ZH_GUARD_DICT=str(path)):
                with self.assertRaisesRegex(ValueError, "three columns"):
                    guard.load_rules()

    def test_sync_drops_the_legacy_action_column_from_user_entries(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            home = base / "home"
            home.mkdir()
            (home / "terminology.tsv").write_text(
                "# @sync 0.9.9.3\n"
                "用户自加词\t用户自己的写法\t用户补充\treplace\n",
                encoding="utf-8")
            with environment(ZH_GUARD_HOME=str(home)):
                guard.ensure_user_dict()
                rules = guard.load_rules()
        entry = next(r for r in rules if r.term == "用户自加词")
        self.assertEqual(entry.suggestion, "用户自己的写法")
        self.assertEqual(entry.meaning, "用户补充")


if __name__ == "__main__":
    unittest.main()
