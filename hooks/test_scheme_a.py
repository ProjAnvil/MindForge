#!/usr/bin/env python3
"""All default MindForge entrypoints are prompt-only, with no model roundtrips."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / "hooks"
ALLOWED = {"SessionStart", "UserPromptSubmit", "SubagentStart"}


class SchemeATests(unittest.TestCase):
    def assert_prompt_only(self, config):
        self.assertTrue(config)
        self.assertLessEqual(set(config), ALLOWED)
        for groups in config.values():
            self.assertEqual(len(groups), 1)
            for group in groups:
                for handler in group["hooks"]:
                    self.assertEqual(handler["type"], "command")
                    self.assertIn("inject-style-rules.sh", handler["command"])
                    self.assertNotIn("python", handler["command"])

    def test_all_default_hook_fragments_only_inject(self):
        for path in [
            HOOKS / "hooks/hooks.json", HOOKS / "hooks/subagent-hooks.json",
            HOOKS / "settings-hooks.json", ROOT / "plugins/style-rules/hooks/hooks.json",
        ]:
            with self.subTest(path=path):
                self.assert_prompt_only(json.loads(path.read_text())["hooks"])

    def test_plugin_manifests_register_no_mcp_or_model_reviewer(self):
        for path in [
            HOOKS / ".claude-plugin/plugin.json", HOOKS / ".zcode-plugin/plugin.json",
            ROOT / "plugins/style-rules/.claude-plugin/plugin.json",
        ]:
            with self.subTest(path=path):
                manifest = json.loads(path.read_text())
                self.assertNotIn("mcpServers", manifest)
                for reference in manifest.get("hooks", []):
                    self.assert_prompt_only(json.loads((HOOKS / reference).read_text())["hooks"])
        self.assertFalse((HOOKS / "hooks/claude-prompt-hooks.json").exists())

    def test_actual_injection_is_short_and_does_not_request_tools(self):
        for language in ["zh-cn", "en"]:
            with self.subTest(language=language), tempfile.TemporaryDirectory(prefix="scheme-a-") as home:
                process = subprocess.run(
                    ["bash", str(HOOKS / "inject-style-rules.sh"), language],
                    input='{"hook_event_name":"UserPromptSubmit"}',
                    text=True, capture_output=True, timeout=20, env={**os.environ, "HOME": home},
                )
                self.assertEqual(process.returncode, 0, process.stderr)
                context = json.loads(process.stdout)["hookSpecificOutput"]["additionalContext"]
                self.assertNotIn("mindforge_", context)
                self.assertNotIn("纯尾即就绪", context)
                self.assertEqual(list(Path(home).iterdir()), [])
                if language == "zh-cn":
                    self.assertLessEqual(len(context), 350)
                    self.assertIn("语境", context)
                    self.assertIn("数字", context)
                else:
                    self.assertIn("ASD-STE100", context)


if __name__ == "__main__":
    unittest.main()
