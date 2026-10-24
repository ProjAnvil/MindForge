#!/usr/bin/env python3
"""MessageDisplay protocol and cross-batch code protection tests."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


class DisplayTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(prefix="zh-display-test-")
        self.root = Path(self.directory.name)
        dictionary = self.root / "dict.tsv"
        dictionary.write_text(
            "机械胳膊\t机械臂\t同义词\treplace\n"
            "病灶分析\t分析问题原因\t按原句改写\n"
            "台账\t清单 / 记录\t按原句选择\n",
            encoding="utf-8",
        )
        self.env = {
            **os.environ,
            "ZH_GUARD_DICT": str(dictionary),
            "ZH_GUARD_HOME": str(self.root / "home"),
            "ZH_GUARD_LEGACY_HOME": str(self.root / "legacy"),
            "ZH_GUARD_STATE_DIR": str(self.root / "state"),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        self.env.pop("ZH_GUARD_OFF", None)

    def tearDown(self):
        self.directory.cleanup()

    def run_batch(self, delta, index=0, final=True, session="s1", message="m1"):
        return subprocess.run(
            [sys.executable, str(HERE / "message-display.py")],
            input=json.dumps({
                "hook_event_name": "MessageDisplay",
                "session_id": session, "message_id": message,
                "index": index, "final": final, "delta": delta,
            }, ensure_ascii=False),
            text=True, capture_output=True, env=self.env, timeout=20,
        )

    def displayed(self, delta, **kwargs):
        process = self.run_batch(delta, **kwargs)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(process.stderr, "")
        return json.loads(process.stdout)["displayContent"]

    def test_only_explicit_safe_rules_are_replaced(self):
        text = "机械胳膊，做病灶分析并保留台账。`机械胳膊`「机械胳膊」"
        self.assertEqual(
            self.displayed(text),
            "机械臂，做病灶分析并保留台账。`机械胳膊`「机械胳膊」",
        )

    def test_fenced_code_across_batches(self):
        self.assertEqual(self.displayed("```python\n", final=False), "```python\n")
        self.assertEqual(
            self.displayed("机械胳膊\n", index=1, final=False), "机械胳膊\n")
        self.assertEqual(
            self.displayed("```\n机械胳膊\n", index=2), "```\n机械臂\n")

    def test_blockquote_fences_across_batches(self):
        self.assertEqual(self.displayed("> ```text\n", final=False), "> ```text\n")
        self.assertEqual(self.displayed("> 机械胳膊\n", index=1, final=False),
                         "> 机械胳膊\n")
        self.assertEqual(self.displayed("> ```\n机械胳膊\n", index=2),
                         "> ```\n机械臂\n")

    def test_tilde_fences_and_empty_final_batch(self):
        self.displayed("~~~~text\n", final=False)
        self.assertEqual(self.displayed("~~~\n机械胳膊\n", index=1, final=False),
                         "~~~\n机械胳膊\n")
        self.assertEqual(self.displayed("~~~~\n机械胳膊\n", index=2, final=False),
                         "~~~~\n机械臂\n")
        self.assertEqual(self.displayed("", index=3), "")

    def test_replayed_batch_does_not_corrupt_fence_state(self):
        opening = "```text\n"
        self.displayed(opening, final=False)
        self.assertEqual(self.displayed(opening, final=False), opening)
        self.assertEqual(self.displayed("机械胳膊\n", index=1), "机械胳膊\n")
        self.assertEqual(self.displayed("机械胳膊\n", index=1), "机械胳膊\n")

    def test_message_and_session_state_are_isolated(self):
        self.displayed("```text\n", final=False)
        self.assertEqual(self.displayed("机械胳膊", session="s2"), "机械臂")
        self.assertEqual(self.displayed("机械胳膊", message="m2"), "机械臂")
        self.assertEqual(self.displayed("机械胳膊\n", index=1), "机械胳膊\n")

    def test_out_of_order_batches_fail_open_with_diagnostic(self):
        self.displayed("```text\n", final=False)
        bad = self.run_batch("机械胳膊\n", index=2)
        self.assertEqual(bad.returncode, 0)
        self.assertEqual(bad.stdout, "")
        self.assertTrue(bad.stderr)
        self.assertEqual(self.displayed("机械胳膊\n", index=1), "机械胳膊\n")

    def test_changed_replay_is_rejected_without_advancing_state(self):
        self.displayed("```text\n", final=False)
        bad = self.run_batch("机械胳膊\n", final=False)
        self.assertEqual(bad.stdout, "")
        self.assertTrue(bad.stderr)
        self.assertEqual(self.displayed("机械胳膊\n", index=1), "机械胳膊\n")

    def test_off_switch_and_invalid_input_do_not_replace(self):
        self.env["ZH_GUARD_OFF"] = "1"
        process = self.run_batch("机械胳膊")
        self.assertEqual((process.returncode, process.stdout), (0, ""))
        self.env.pop("ZH_GUARD_OFF")
        process = subprocess.run(
            [sys.executable, str(HERE / "message-display.py")],
            input="not json", capture_output=True, text=True, env=self.env, timeout=20,
        )
        self.assertEqual((process.returncode, process.stdout), (0, ""))
        self.assertTrue(process.stderr)

    def test_state_contains_only_metadata_not_draft_text(self):
        self.displayed("机械胳膊", final=False)
        files = list((self.root / "state").glob("display-*.json"))
        self.assertEqual(len(files), 1)
        state = files[0].read_text(encoding="utf-8")
        self.assertNotIn("机械胳膊", state)
        self.assertNotIn("机械臂", state)
        files[0].write_text("invalid json", encoding="utf-8")
        process = self.run_batch("机械胳膊", index=1)
        self.assertEqual((process.returncode, process.stdout), (0, ""))
        self.assertTrue(process.stderr)

    def test_project_override_can_prevent_replacement(self):
        project = self.root / "project"
        project.mkdir()
        (project / ".git").mkdir()
        (project / "mindforge.zh-dict.tsv").write_text(
            "机械胳膊\t根据原意改写\t项目覆盖\n", encoding="utf-8")
        self.env.pop("ZH_GUARD_DICT")
        payload = {
            "session_id": "s1", "message_id": "m1",
            "index": 0, "final": True, "delta": "机械胳膊", "cwd": str(project),
        }
        process = subprocess.run(
            [sys.executable, str(HERE / "message-display.py")],
            input=json.dumps(payload), capture_output=True, text=True,
            env=self.env, timeout=20,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout)["displayContent"], "机械胳膊")

    def test_optional_configuration_executes_without_default_registration(self):
        config = json.loads((HERE / "hooks/message-display-hooks.json").read_text())
        self.assertEqual(set(config["hooks"]), {"MessageDisplay"})
        hook = config["hooks"]["MessageDisplay"][0]["hooks"][0]
        payload = {"session_id": "s1", "message_id": "m1", "index": 0,
                   "final": True, "delta": "机械胳膊"}
        process = subprocess.run(
            ["sh", "-c", hook["command"]], input=json.dumps(payload),
            text=True, capture_output=True,
            env={**self.env, "CLAUDE_PLUGIN_ROOT": str(HERE)}, timeout=20,
        )
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout)["displayContent"], "机械臂")


if __name__ == "__main__":
    unittest.main()
