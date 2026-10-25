package main

import (
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

// loadEvents unmarshals the hooks.events object of a config file.
func loadEvents(t *testing.T, path string) map[string][]groupProbe {
	t.Helper()
	top, err := loadTopLevel(path)
	if err != nil {
		t.Fatalf("loadTopLevel: %v", err)
	}
	var hooks map[string]json.RawMessage
	if h, ok := top["hooks"]; ok {
		if err := json.Unmarshal(h, &hooks); err != nil {
			t.Fatalf("hooks: %v", err)
		}
	}
	// Two shapes: Claude's hooks object is the event map itself;
	// zcode nests events under hooks.events (alongside enabled, timeoutMs...).
	var eventsRaw map[string]json.RawMessage
	if e, ok := hooks["events"]; ok {
		if err := json.Unmarshal(e, &eventsRaw); err != nil {
			t.Fatalf("events: %v", err)
		}
	} else {
		eventsRaw = hooks
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

func TestInstallClaudeRegistersOnlyInjection(t *testing.T) {
	home := t.TempDir()
	if err := installClaude(home, "zh-cn"); err != nil {
		t.Fatalf("installClaude: %v", err)
	}

	settingsPath := filepath.Join(home, ".claude", "settings.json")
	events := loadEvents(t, settingsPath)

	wantEvents := []string{
		"SessionStart", "UserPromptSubmit", "SubagentStart",
	}
	for _, ev := range wantEvents {
		if len(events[ev]) == 0 {
			t.Errorf("event %s is not registered", ev)
		}
	}
	if n := len(events["UserPromptSubmit"]); n != 1 {
		t.Errorf("expected one UserPromptSubmit group, got %d", n)
	}

	for _, event := range []string{"PreToolUse", "Stop", "SubagentStop"} {
		if len(events[event]) != 0 {
			t.Errorf("scheme A must not register %s", event)
		}
	}

	// Runtime files extracted.
	hooksDir := filepath.Join(home, ".claude", "MindForge", "hooks")
	for _, name := range []string{
		"inject-style-rules.sh", "style-rules-zh.md",
	} {
		if _, err := os.Stat(filepath.Join(hooksDir, name)); err != nil {
			t.Errorf("missing runtime file: %s (%v)", name, err)
		}
	}
	if _, registered := events["MessageDisplay"]; registered {
		t.Error("sentence annotations must not register display replacement hooks")
	}
	if _, err := os.Stat(filepath.Join(hooksDir, "message-display.py")); !os.IsNotExist(err) {
		t.Errorf("display replacement script must not be installed: %v", err)
	}
	// Language marker.
	marker, err := os.ReadFile(filepath.Join(hooksDir, "style-rules.lang"))
	if err != nil || strings.TrimSpace(string(marker)) != "zh-cn" {
		t.Errorf("expected style-rules.lang to be zh-cn, got %q err=%v", string(marker), err)
	}
	// Shell script executable.
	info, err := os.Stat(filepath.Join(hooksDir, "inject-style-rules.sh"))
	if err != nil || info.Mode()&0o111 == 0 {
		t.Errorf("inject-style-rules.sh must be executable, mode=%v err=%v", info.Mode(), err)
	}
	if _, err := os.Stat(filepath.Join(home, ".claude", "MindForge", "terminology.tsv")); !os.IsNotExist(err) {
		t.Errorf("scheme A must not create a user dictionary: %v", err)
	}
}

func TestInstallClaudeIdempotent(t *testing.T) {
	home := t.TempDir()
	for i := 0; i < 2; i++ {
		if err := installClaude(home, "zh-cn"); err != nil {
			t.Fatalf("install #%d: %v", i+1, err)
		}
	}
	events := loadEvents(t, filepath.Join(home, ".claude", "settings.json"))
	if n := len(events["UserPromptSubmit"]); n != 1 {
		t.Errorf("expected one UserPromptSubmit group after repeated installation, got %d", n)
	}
	if n := len(events["Stop"]); n != 0 {
		t.Errorf("scheme A must not register Stop, got %d groups", n)
	}
}

func TestInstallClaudePreservesExistingConfig(t *testing.T) {
	home := t.TempDir()
	settingsDir := filepath.Join(home, ".claude")
	if err := os.MkdirAll(settingsDir, 0o755); err != nil {
		t.Fatal(err)
	}
	existing := `{
  "model": "sonnet",
  "hooks": {
    "PostToolUse": [
      {"matcher": "Write", "hooks": [{"type": "command", "command": "prettier --write", "timeout": 30}]}
    ],
    "Stop": [
      {"hooks": [{"type": "command", "command": "my-own-stop.sh"}]}
    ]
  }
}`
	if err := os.WriteFile(filepath.Join(settingsDir, "settings.json"), []byte(existing), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := installClaude(home, "en"); err != nil {
		t.Fatalf("installClaude: %v", err)
	}
	top, err := loadTopLevel(filepath.Join(settingsDir, "settings.json"))
	if err != nil {
		t.Fatal(err)
	}
	if string(top["model"]) != `"sonnet"` {
		t.Errorf("top-level model field was modified: %s", string(top["model"]))
	}
	events := loadEvents(t, filepath.Join(settingsDir, "settings.json"))
	if n := len(events["PostToolUse"]); n != 1 {
		t.Errorf("expected one preserved foreign PostToolUse group, got %d", n)
	}
	if n := len(events["Stop"]); n != 1 {
		t.Errorf("expected only the preserved foreign Stop group in English mode, got %d", n)
	}
	// Foreign handler fields (timeout) survive byte-for-byte.
	if !strings.Contains(string(top["hooks"]), "prettier --write") {
		t.Error("foreign command contents were lost")
	}
}

func TestAllInstallProfilesArePromptOnly(t *testing.T) {
	for _, platform := range []struct {
		name     string
		hooksDir string
		config   string
		install  func(string, string) error
	}{
		{"claude", ".claude/MindForge/hooks", ".claude/settings.json", installClaude},
		{"zcode", ".zcode/mindforge/hooks", ".zcode/cli/config.json", installZcode},
		{"codex", ".codex/mindforge/hooks", ".codex/hooks.json", installCodex},
	} {
		for _, language := range []string{"en", "zh-cn"} {
			t.Run(platform.name+"/"+language, func(t *testing.T) {
				home := t.TempDir()
				if err := platform.install(home, language); err != nil {
					t.Fatal(err)
				}
				events := loadEvents(t, filepath.Join(home, platform.config))
				for event, groups := range events {
					if event != "SessionStart" && event != "UserPromptSubmit" && event != "SubagentStart" {
						t.Errorf("prompt-only mode registered a non-injection event: %s", event)
					}
					if len(groups) != 1 {
						t.Errorf("expected one injection group for %s, got %d", event, len(groups))
					}
					for _, group := range groups {
						for _, hook := range group.Hooks {
							if !strings.Contains(hook.Command, "inject-style-rules.sh") {
								t.Errorf("prompt-only mode registered a terminology hook: %s", hook.Command)
							}
						}
					}
				}
				if len(events["SessionStart"]) != 1 || len(events["UserPromptSubmit"]) != 1 {
					t.Error("scheme A must inject writing rules at session start and each prompt")
				}
				hooksDir := filepath.Join(home, platform.hooksDir)
				files, err := os.ReadDir(hooksDir)
				if err != nil {
					t.Fatal(err)
				}
				if len(files) != 3 {
					t.Errorf("expected only the injection script, selected rules and language marker, got %d files", len(files))
				}
				if _, err := os.Stat(filepath.Join(home, ".claude", "MindForge", "terminology.tsv")); !os.IsNotExist(err) {
					t.Errorf("prompt-only install must not create a user dictionary: %v", err)
				}
				command := exec.CommandContext(t.Context(), "bash", filepath.Join(hooksDir, "inject-style-rules.sh"))
				command.Stdin = strings.NewReader(`{"hook_event_name":"UserPromptSubmit"}`)
				output, err := command.Output()
				if err != nil {
					t.Fatal(err)
				}
				var payload struct {
					HookSpecificOutput struct {
						Context string `json:"additionalContext"`
					} `json:"hookSpecificOutput"`
				}
				if err := json.Unmarshal(output, &payload); err != nil {
					t.Fatal(err)
				}
				context := payload.HookSpecificOutput.Context
				if strings.Contains(context, "mindforge_") {
					t.Error("scheme A must not request dictionary tools")
				}
				if language == "en" && !strings.Contains(context, "ASD-STE100") {
					t.Error("English injection must retain ASD-STE100")
				}
			})
		}
	}
}

func TestSwitchToEnglishDisablesOwnedChecksAndPreservesDictionary(t *testing.T) {
	home := t.TempDir()
	if err := installClaude(home, "zh-cn"); err != nil {
		t.Fatal(err)
	}
	dictionary := filepath.Join(home, ".claude", "MindForge", "terminology.tsv")
	content := []byte("existing-term\t\tpreserve this meaning\n")
	if err := os.WriteFile(dictionary, content, 0o644); err != nil {
		t.Fatal(err)
	}
	if err := installClaude(home, "en"); err != nil {
		t.Fatal(err)
	}
	events := loadEvents(t, filepath.Join(home, ".claude", "settings.json"))
	if len(events["Stop"]) != 0 || len(events["SubagentStop"]) != 0 || len(events["PreToolUse"]) != 0 {
		t.Error("switching to English must unregister owned terminology checks")
	}
	after, err := os.ReadFile(dictionary)
	if err != nil || string(after) != string(content) {
		t.Errorf("switching language must preserve existing dictionary contents: %v", err)
	}
	if err := installClaude(home, "zh-cn"); err != nil {
		t.Fatal(err)
	}
	events = loadEvents(t, filepath.Join(home, ".claude", "settings.json"))
	if len(events["Stop"]) != 0 || len(events["UserPromptSubmit"]) != 1 {
		t.Error("Chinese mode must remain prompt-only after a language switch")
	}
}

func TestSchemeAUpgradeRemovesLegacyOwnedChecks(t *testing.T) {
	home := t.TempDir()
	configDir := filepath.Join(home, ".claude")
	if err := os.MkdirAll(filepath.Join(configDir, "MindForge"), 0o755); err != nil {
		t.Fatal(err)
	}
	legacy := `{"hooks":{
		"UserPromptSubmit":[{"hooks":[{"command":"python3 ~/.claude/MindForge/hooks/inject.py"}]}],
		"PreToolUse":[{"hooks":[{"command":"python3 ~/.claude/MindForge/hooks/inspect-file.py"}]}],
		"Stop":[{"hooks":[{"command":"python3 ~/.claude/MindForge/hooks/inspect.py"}]},
		        {"hooks":[{"command":"foreign-audit.sh"}]}],
		"SubagentStop":[{"hooks":[{"command":"python3 ~/.claude/MindForge/hooks/inspect.py"}]}]
	}}`
	if err := os.WriteFile(filepath.Join(configDir, "settings.json"), []byte(legacy), 0o644); err != nil {
		t.Fatal(err)
	}
	dictionary := filepath.Join(configDir, "MindForge", "terminology.tsv")
	saved := []byte("custom-term\t\tretained data\n")
	if err := os.WriteFile(dictionary, saved, 0o644); err != nil {
		t.Fatal(err)
	}
	if err := installClaude(home, "zh-cn"); err != nil {
		t.Fatal(err)
	}
	events := loadEvents(t, filepath.Join(configDir, "settings.json"))
	if len(events["PreToolUse"]) != 0 || len(events["SubagentStop"]) != 0 || len(events["UserPromptSubmit"]) != 1 {
		t.Error("scheme A upgrade must remove the legacy owned terminology registrations")
	}
	if len(events["Stop"]) != 1 || events["Stop"][0].Hooks[0].Command != "foreign-audit.sh" {
		t.Error("scheme A upgrade must preserve the foreign Stop hook")
	}
	current, err := os.ReadFile(dictionary)
	if err != nil || string(current) != string(saved) {
		t.Errorf("scheme A upgrade must preserve existing dictionary data: %v", err)
	}
}

func TestInstallZcodeMergesConfig(t *testing.T) {
	home := t.TempDir()
	configDir := filepath.Join(home, ".zcode", "cli")
	if err := os.MkdirAll(configDir, 0o755); err != nil {
		t.Fatal(err)
	}
	existing := `{
  "skills": {"/some/skill/SKILL.md": {"enable": false}},
  "hooks": {
    "timeoutMs": 60000,
    "events": {
      "PreToolUse": [
        {"matcher": "Bash", "hooks": [{"type": "command", "command": "my-guard.sh"}]}
      ]
    }
  }
}`
	if err := os.WriteFile(filepath.Join(configDir, "config.json"), []byte(existing), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := installZcode(home, "zh-cn"); err != nil {
		t.Fatalf("installZcode: %v", err)
	}

	top, err := loadTopLevel(filepath.Join(configDir, "config.json"))
	if err != nil {
		t.Fatal(err)
	}
	if string(top["skills"]) == "" {
		t.Error("skills field was lost")
	}
	var hooksObj map[string]json.RawMessage
	if err := json.Unmarshal(top["hooks"], &hooksObj); err != nil {
		t.Fatal(err)
	}
	if string(hooksObj["timeoutMs"]) != "60000" {
		t.Errorf("expected hooks.timeoutMs to remain 60000, got %s", string(hooksObj["timeoutMs"]))
	}
	if string(hooksObj["enabled"]) != "true" {
		t.Errorf("expected hooks.enabled to be true, got %s", string(hooksObj["enabled"]))
	}

	events := loadEvents(t, filepath.Join(configDir, "config.json"))
	// zcode has no Subagent events — ours must not add them.
	if _, ok := events["SubagentStart"]; ok {
		t.Error("SubagentStart must not be registered for zcode")
	}
	if n := len(events["PreToolUse"]); n != 1 {
		t.Errorf("expected only the preserved foreign PreToolUse group, got %d", n)
	}
	if len(events["Stop"]) != 0 {
		t.Error("zcode must not register Stop under scheme A")
	}
}

func TestInstallZcodeCreatesMissingConfigDir(t *testing.T) {
	home := t.TempDir()
	if err := os.MkdirAll(filepath.Join(home, ".zcode"), 0o755); err != nil {
		t.Fatal(err)
	}
	// ~/.zcode exists but cli/ does not: install must create it.
	if err := installZcode(home, "zh-cn"); err != nil {
		t.Fatalf("installZcode: %v", err)
	}
	if _, err := os.Stat(filepath.Join(home, ".zcode", "cli", "config.json")); err != nil {
		t.Errorf("config.json was not generated: %v", err)
	}
}

func TestCountOursCountsOursAndTotal(t *testing.T) {
	events := map[string]json.RawMessage{
		"Stop":       json.RawMessage(`[{"hooks":[{"command":"python3 ~/.claude/MindForge/hooks/inspect.py"}]},{"hooks":[{"command":"mine.sh"}]}]`),
		"PreToolUse": json.RawMessage(`[{"hooks":[{"command":"my-guard.sh"}]}]`),
	}
	ours, total := countOurs(events)
	if ours != 1 || total != 3 {
		t.Errorf("expected ours=1 total=3 including a foreign group, got ours=%d total=%d", ours, total)
	}
}

func TestDetectPlatforms(t *testing.T) {
	home := t.TempDir()
	for _, d := range []string{".claude", ".zcode", ".kimi-code"} {
		if err := os.MkdirAll(filepath.Join(home, d), 0o755); err != nil {
			t.Fatal(err)
		}
	}
	detected := detectPlatforms(home)
	var found []string
	for _, p := range detected {
		if p.supported {
			found = append(found, p.name)
		}
	}
	if len(found) != 2 || found[0] != "claude" || found[1] != "zcode" {
		t.Errorf("expected supported platforms claude and zcode, got %v", found)
	}
}
