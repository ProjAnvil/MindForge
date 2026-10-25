#!/usr/bin/env python3
"""English setup installs writing-rule injection without terminology checks."""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


class EnglishInstallationTests(unittest.TestCase):
    def setup_language(self, home, language):
        process = subprocess.run(
            ["bash", str(ROOT / "setup-claude.sh"), "--lang=" + language],
            env={**os.environ, "HOME": str(home)}, input="",
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        return process.stdout

    def test_fresh_english_setup_is_prompt_only(self):
        with tempfile.TemporaryDirectory(prefix="english-setup-") as directory:
            home = Path(directory)
            output = self.setup_language(home, "en")
            config = json.loads((home / ".claude/settings.json").read_text())
            self.assertEqual(set(config["hooks"]), {
                "SessionStart", "UserPromptSubmit", "SubagentStart",
            })
            for groups in config["hooks"].values():
                for group in groups:
                    for hook in group["hooks"]:
                        self.assertIn("inject-style-rules.sh", hook["command"])
            self.assertFalse((home / ".claude/MindForge/terminology.tsv").exists())
            self.assertEqual(list((home / ".claude/hooks").glob("*.tsv")), [])
            self.assertNotIn("claude mcp add", output)
            injection = subprocess.run(
                ["bash", str(home / ".claude/hooks/inject-style-rules.sh")],
                input='{"hook_event_name":"UserPromptSubmit"}',
                capture_output=True, text=True, timeout=20,
            )
            self.assertEqual(injection.returncode, 0, injection.stderr)
            context = json.loads(injection.stdout)["hookSpecificOutput"]["additionalContext"]
            self.assertIn("ASD-STE100", context)
            self.assertNotIn("mindforge_check_text", context)

    def test_switch_to_english_preserves_data_and_foreign_hooks(self):
        with tempfile.TemporaryDirectory(prefix="switch-english-") as directory:
            home = Path(directory)
            self.setup_language(home, "zh-cn")
            dictionary = home / ".claude/MindForge/terminology.tsv"
            content = b"custom-term\t\tretain this meaning\n"
            dictionary.parent.mkdir(parents=True, exist_ok=True)
            dictionary.write_bytes(content)
            settings = home / ".claude/settings.json"
            config = json.loads(settings.read_text())
            foreign = {"hooks": [{"type": "command", "command": "custom-audit.sh"}]}
            config["hooks"]["Stop"] = [
                {"hooks": [{"type": "command", "command": 'python3 "$HOME/.claude/hooks/inspect.py"'}]},
                foreign,
            ]
            settings.write_text(json.dumps(config))
            self.setup_language(home, "en")
            after = json.loads(settings.read_text())["hooks"]
            self.assertEqual(after["Stop"], [foreign])
            self.assertEqual(after.get("SubagentStop", []), [])
            self.assertEqual(len(after["UserPromptSubmit"]), 1)
            self.assertEqual(dictionary.read_bytes(), content)

    def test_chinese_setup_also_uses_prompt_only_profile(self):
        with tempfile.TemporaryDirectory(prefix="chinese-scheme-a-") as directory:
            home = Path(directory)
            self.setup_language(home, "zh-cn")
            config = json.loads((home / ".claude/settings.json").read_text())["hooks"]
            self.assertEqual(set(config), {"SessionStart", "UserPromptSubmit", "SubagentStart"})
            self.assertEqual(len(config["UserPromptSubmit"]), 1)
            self.assertFalse((home / ".claude/MindForge/terminology.tsv").exists())
            for groups in config.values():
                for group in groups:
                    self.assertTrue(all("inject-style-rules.sh" in hook["command"] for hook in group["hooks"]))


if __name__ == "__main__":
    unittest.main()
