#!/usr/bin/env python3
"""Engineering diagnostics stay English; Chinese product data stays unchanged."""
import ast
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from pathlib import Path

import zh_guard_common as guard

HERE = Path(__file__).resolve().parent
CJK = re.compile(r"[\u4e00-\u9fff]")


class EnglishDiagnosticsTests(unittest.TestCase):
    def assert_english(self, message):
        self.assertIsNone(CJK.search(message), message)
        self.assertRegex(message, r"[A-Za-z]")

    def test_python_check_descriptions_are_english(self):
        for path in HERE.glob("test_*.py"):
            for call in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
                if not (isinstance(call, ast.Call) and isinstance(call.func, ast.Name)
                        and call.func.id == "check" and call.args):
                    continue
                for part in ast.walk(call.args[0]):
                    if isinstance(part, ast.Constant) and isinstance(part.value, str):
                        with self.subTest(file=path.name, line=part.lineno):
                            self.assertIsNone(CJK.search(part.value), part.value)

    def test_go_assertion_descriptions_are_english(self):
        for path in (HERE.parent / "cli/mindforge").glob("*_test.go"):
            for message in re.findall(r't\.(?:Errorf?|Fatalf?|Logf?)\("((?:[^"\\]|\\.)*)"', path.read_text()):
                with self.subTest(file=path.name, message=message):
                    self.assertIsNone(CJK.search(message), message)

    def test_core_validation_and_regex_diagnostics_are_english(self):
        for operation in [
            lambda: guard.Rule(""),
            lambda: guard.init_workspace_dict("relative"),
            lambda: guard.lint_text("text", [], masked_text=""),
            lambda: guard.mask_protected("text", "invalid"),
        ]:
            with self.subTest(operation=operation):
                with self.assertRaises(ValueError) as error:
                    operation()
                self.assert_english(str(error.exception))
        output = io.StringIO()
        with redirect_stderr(output):
            guard.lint_text("text", [guard.Rule("re:[", "suggestion")])
        self.assert_english(output.getvalue())

    def test_runtime_validation_templates_are_english(self):
        for script in ["zh_guard_common.py", "term-dict-server.py"]:
            for statement in ast.walk(ast.parse((HERE / script).read_text(encoding="utf-8"))):
                if not isinstance(statement, ast.Raise) or statement.exc is None:
                    continue
                for part in ast.walk(statement.exc):
                    if isinstance(part, ast.Constant) and isinstance(part.value, str):
                        with self.subTest(script=script, line=part.lineno):
                            self.assertIsNone(CJK.search(part.value), part.value)

    def test_tidy_reports_english_errors(self):
        spec = importlib.util.spec_from_file_location("tidy_english", HERE / "tidy-dict.py")
        tidy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tidy)
        errors, _warnings = tidy.check(tidy.parse([
            "re:[\tsuggestion\tmeaning",
            "term\tsuggestion\tmeaning\textra",
        ]))
        self.assertTrue(errors)
        for message in errors:
            self.assert_english(message)
        with tempfile.TemporaryDirectory(prefix="english-tidy-") as directory:
            path = Path(directory) / "dict.tsv"
            path.write_text("term\t\tmeaning\n", encoding="utf-8")
            process = subprocess.run(
                [sys.executable, str(HERE / "tidy-dict.py"), "--path", str(path), "--check"],
                capture_output=True, text=True, timeout=20,
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assert_english(process.stdout)

    def test_mcp_validation_errors_are_english(self):
        with tempfile.TemporaryDirectory(prefix="english-mcp-") as directory:
            requests = [
                ("mindforge_init_dict", {"cwd": "relative"}),
                ("mindforge_add_term", {"term": "term", "scope": "invalid"}),
                ("mindforge_check_text", {"text": ""}),
            ]
            payload = "\n".join(json.dumps({
                "jsonrpc": "2.0", "id": index, "method": "tools/call",
                "params": {"name": name, "arguments": args},
            }) for index, (name, args) in enumerate(requests)) + "\n"
            process = subprocess.run(
                [sys.executable, str(HERE / "term-dict-server.py")],
                input=payload, capture_output=True, text=True, timeout=20,
                env={**os.environ, "ZH_GUARD_HOME": directory,
                     "ZH_GUARD_LEGACY_HOME": str(Path(directory) / "legacy")},
            )
            self.assertEqual(process.returncode, 0, process.stderr)
            responses = [json.loads(line)["result"] for line in process.stdout.splitlines()]
            self.assertEqual(len(responses), len(requests))
            for response in responses:
                self.assertTrue(response["isError"], response)
                self.assert_english(response["content"][0]["text"])

    def test_chinese_meaning_and_sentence_are_product_data(self):
        text = "小说里，他举起机械胳膊。"
        meaning = "科幻人物的身体部件，不是工业设备"
        annotation = guard.lint_text(text, [guard.Rule("机械胳膊", "", meaning)])[0]
        self.assertEqual(annotation.meaning, meaning)
        self.assertEqual(annotation.sentence, text)

    def test_evaluation_reports_are_english(self):
        for script in ["eval-tidy-dict.py", "eval-zh-guard.py"]:
            with self.subTest(script=script):
                process = subprocess.run(
                    [sys.executable, str(HERE / script), "--rounds", "1"],
                    capture_output=True, text=True, timeout=60,
                    env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
                )
                self.assertEqual(process.returncode, 0, process.stderr)
                self.assert_english(process.stdout)


if __name__ == "__main__":
    unittest.main()
