package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

// loadCodexEvents reads the hooks.json written for Codex. Its top level is
// {"hooks": {event: [groups]}} — the same shape Claude uses inside
// settings.json, so the merge machinery is shared.
func loadCodexEvents(t *testing.T, path string) map[string][]groupProbe {
	t.Helper()
	top, err := loadTopLevel(path)
	if err != nil {
		t.Fatalf("loadTopLevel: %v", err)
	}
	var eventsRaw map[string]json.RawMessage
	if h, ok := top["hooks"]; ok {
		if err := json.Unmarshal(h, &eventsRaw); err != nil {
			t.Fatalf("hooks: %v", err)
		}
	}
	events := map[string][]groupProbe{}
	for ev, raw := range eventsRaw {
		var groups []groupProbe
		if err := json.Unmarshal(raw, &groups); err != nil {
			t.Fatalf("event %s: %v", ev, err)
		}
		events[ev] = groups
	}
	return events
}

func TestInstallCodexRegistersSevenEventSet(t *testing.T) {
	home := t.TempDir()
	if err := os.MkdirAll(filepath.Join(home, ".codex"), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := installCodex(home, "zh-cn"); err != nil {
		t.Fatalf("installCodex: %v", err)
	}

	hooksPath := filepath.Join(home, ".codex", "hooks.json")
	events := loadCodexEvents(t, hooksPath)

	for _, ev := range []string{"SessionStart", "UserPromptSubmit", "PreToolUse", "Stop"} {
		if len(events[ev]) == 0 {
			t.Errorf("event %s 未注册", ev)
		}
	}
	// Codex has no Subagent events.
	for _, ev := range []string{"SubagentStart", "SubagentStop"} {
		if _, ok := events[ev]; ok {
			t.Errorf("Codex 不支持 %s，不应注册（死配置）", ev)
		}
	}
	// File guard matches Codex tool names (apply_patch is Codex's editor).
	var matcher string
	for _, g := range events["PreToolUse"] {
		matcher = g.Matcher
	}
	if !strings.Contains(matcher, "apply_patch") {
		t.Errorf("PreToolUse matcher 应含 Codex 的 apply_patch 工具名，实际 %q", matcher)
	}
	// Stop hook uses the --platform flag: user-config hooks get no env var,
	// and Codex's Stop contract (decision:block) matches zcode's.
	var sawPlatform bool
	for _, g := range events["Stop"] {
		for _, h := range g.Hooks {
			if strings.Contains(h.Command, "--platform") {
				sawPlatform = true
			}
		}
	}
	if !sawPlatform {
		t.Error("Codex 的 Stop 命令应带 --platform（decision:block 契约）")
	}
	// Runtime files + language marker under ~/.codex/mindforge/hooks.
	hooksDir := filepath.Join(home, ".codex", "mindforge", "hooks")
	if _, err := os.Stat(filepath.Join(hooksDir, "inspect.py")); err != nil {
		t.Errorf("脚本未安装: %v", err)
	}
	marker, _ := os.ReadFile(filepath.Join(hooksDir, "style-rules.lang"))
	if strings.TrimSpace(string(marker)) != "zh-cn" {
		t.Errorf("style-rules.lang 应为 zh-cn，实际 %q", string(marker))
	}
}

func TestInstallCodexIdempotentAndPreservesForeign(t *testing.T) {
	home := t.TempDir()
	codexDir := filepath.Join(home, ".codex")
	if err := os.MkdirAll(codexDir, 0o755); err != nil {
		t.Fatal(err)
	}
	existing := `{"hooks": {"PreToolUse": [
		{"matcher": "Bash", "hooks": [{"type": "command", "command": "my-audit.sh", "timeout": 30}]}
	]}}`
	if err := os.WriteFile(filepath.Join(codexDir, "hooks.json"), []byte(existing), 0o644); err != nil {
		t.Fatal(err)
	}
	for i := 0; i < 2; i++ {
		if err := installCodex(home, "en"); err != nil {
			t.Fatalf("install #%d: %v", i+1, err)
		}
	}
	events := loadCodexEvents(t, filepath.Join(codexDir, "hooks.json"))
	if n := len(events["PreToolUse"]); n != 2 {
		t.Errorf("PreToolUse 应为 外来1组 + mindforge1组 = 2，实际 %d", n)
	}
	if n := len(events["Stop"]); n != 1 {
		t.Errorf("重复安装后 Stop 应仍为 1 组，实际 %d", n)
	}
}
