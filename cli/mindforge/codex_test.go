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

func TestInstallCodexRegistersOnlyInjection(t *testing.T) {
	home := t.TempDir()
	if err := os.MkdirAll(filepath.Join(home, ".codex"), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := installCodex(home, "zh-cn"); err != nil {
		t.Fatalf("installCodex: %v", err)
	}

	hooksPath := filepath.Join(home, ".codex", "hooks.json")
	events := loadCodexEvents(t, hooksPath)

	for _, ev := range []string{"SessionStart", "UserPromptSubmit"} {
		if len(events[ev]) == 0 {
			t.Errorf("event %s is not registered", ev)
		}
	}
	// Codex has no Subagent events.
	for _, ev := range []string{"SubagentStart", "SubagentStop"} {
		if _, ok := events[ev]; ok {
			t.Errorf("Codex does not support %s; it must not be registered", ev)
		}
	}
	for _, event := range []string{"PreToolUse", "Stop"} {
		if len(events[event]) != 0 {
			t.Errorf("Codex must not register %s under scheme A", event)
		}
	}
	// Runtime files + language marker under ~/.codex/mindforge/hooks.
	hooksDir := filepath.Join(home, ".codex", "mindforge", "hooks")
	if _, err := os.Stat(filepath.Join(hooksDir, "inject-style-rules.sh")); err != nil {
		t.Errorf("injection script was not installed: %v", err)
	}
	marker, _ := os.ReadFile(filepath.Join(hooksDir, "style-rules.lang"))
	if strings.TrimSpace(string(marker)) != "zh-cn" {
		t.Errorf("expected style-rules.lang to be zh-cn, got %q", string(marker))
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
	if n := len(events["PreToolUse"]); n != 1 {
		t.Errorf("expected only the preserved foreign PreToolUse group in English mode, got %d", n)
	}
	if n := len(events["Stop"]); n != 0 {
		t.Errorf("English mode must not register Stop checks, got %d groups", n)
	}
}
