package main

import (
	"encoding/json"
	"os"
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

func TestInstallClaudeRegistersAllEvents(t *testing.T) {
	home := t.TempDir()
	if err := installClaude(home, "zh-cn"); err != nil {
		t.Fatalf("installClaude: %v", err)
	}

	settingsPath := filepath.Join(home, ".claude", "settings.json")
	events := loadEvents(t, settingsPath)

	wantEvents := []string{
		"SessionStart", "UserPromptSubmit", "SubagentStart",
		"PreToolUse", "Stop", "SubagentStop",
	}
	for _, ev := range wantEvents {
		if len(events[ev]) == 0 {
			t.Errorf("event %s 未注册", ev)
		}
	}
	if n := len(events["UserPromptSubmit"]); n != 2 {
		t.Errorf("UserPromptSubmit 应注册 2 组，实际 %d", n)
	}

	// PreToolUse carries the file-guard matcher.
	for _, g := range events["PreToolUse"] {
		if g.Hooks == nil {
			t.Errorf("PreToolUse 组缺 hooks")
		}
	}
	// Commands point into the MindForge hooks directory.
	for _, g := range events["Stop"] {
		for _, h := range g.Hooks {
			if !strings.Contains(h.Command, "MindForge/hooks/inspect.py") {
				t.Errorf("Stop 命令路径不对: %s", h.Command)
			}
		}
	}

	// Runtime files extracted.
	hooksDir := filepath.Join(home, ".claude", "MindForge", "hooks")
	for _, name := range []string{
		"inject-style-rules.sh", "inject.py", "inspect.py",
		"inspect-file.py", "zh_guard_common.py", "term-dict-server.py",
		"terminology.tsv", "style-rules-zh.md", "style-rules-en.md",
	} {
		if _, err := os.Stat(filepath.Join(hooksDir, name)); err != nil {
			t.Errorf("脚本缺失: %s (%v)", name, err)
		}
	}
	// Language marker.
	marker, err := os.ReadFile(filepath.Join(hooksDir, "style-rules.lang"))
	if err != nil || strings.TrimSpace(string(marker)) != "zh-cn" {
		t.Errorf("style-rules.lang 应为 zh-cn, got %q err=%v", string(marker), err)
	}
	// Shell script executable.
	info, err := os.Stat(filepath.Join(hooksDir, "inject-style-rules.sh"))
	if err != nil || info.Mode()&0o111 == 0 {
		t.Errorf("inject-style-rules.sh 应可执行, mode=%v err=%v", info.Mode(), err)
	}
	// User dict seeded.
	if _, err := os.Stat(filepath.Join(home, ".claude", "MindForge", "terminology.tsv")); err != nil {
		t.Errorf("用户词典未生成: %v", err)
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
	if n := len(events["UserPromptSubmit"]); n != 2 {
		t.Errorf("重复安装后 UserPromptSubmit 应仍为 2 组，实际 %d（过滤失效）", n)
	}
	if n := len(events["Stop"]); n != 1 {
		t.Errorf("重复安装后 Stop 应仍为 1 组，实际 %d", n)
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
		t.Errorf("顶层字段 model 被破坏: %s", string(top["model"]))
	}
	events := loadEvents(t, filepath.Join(settingsDir, "settings.json"))
	if n := len(events["PostToolUse"]); n != 1 {
		t.Errorf("外来 PostToolUse 组应保留 1 组，实际 %d", n)
	}
	if n := len(events["Stop"]); n != 2 {
		t.Errorf("Stop 应为 外来1组 + mindforge1组 = 2，实际 %d", n)
	}
	// Foreign handler fields (timeout) survive byte-for-byte.
	if !strings.Contains(string(top["hooks"]), "prettier --write") {
		t.Error("外来命令内容丢失")
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
		t.Error("skills 字段丢失")
	}
	var hooksObj map[string]json.RawMessage
	if err := json.Unmarshal(top["hooks"], &hooksObj); err != nil {
		t.Fatal(err)
	}
	if string(hooksObj["timeoutMs"]) != "60000" {
		t.Errorf("hooks.timeoutMs 应保留 60000，实际 %s", string(hooksObj["timeoutMs"]))
	}
	if string(hooksObj["enabled"]) != "true" {
		t.Errorf("hooks.enabled 应为 true，实际 %s", string(hooksObj["enabled"]))
	}

	events := loadEvents(t, filepath.Join(configDir, "config.json"))
	// zcode has no Subagent events — ours must not add them.
	if _, ok := events["SubagentStart"]; ok {
		t.Error("zcode 不支持 SubagentStart，不应注册（死配置）")
	}
	if n := len(events["PreToolUse"]); n != 2 {
		t.Errorf("PreToolUse 应为 外来1组 + mindforge1组 = 2，实际 %d", n)
	}
	// Stop hook carries --platform (user-config hooks get no ZCODE_PLUGIN_ROOT).
	var sawPlatform bool
	for _, g := range events["Stop"] {
		for _, h := range g.Hooks {
			if strings.Contains(h.Command, "--platform") {
				sawPlatform = true
			}
		}
	}
	if !sawPlatform {
		t.Error("zcode 的 Stop 命令应带 --platform")
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
		t.Errorf("config.json 未生成: %v", err)
	}
}

func TestCountOursCountsOursAndTotal(t *testing.T) {
	events := map[string]json.RawMessage{
		"Stop": json.RawMessage(`[{"hooks":[{"command":"python3 ~/.claude/MindForge/hooks/inspect.py"}]},{"hooks":[{"command":"mine.sh"}]}]`),
		"PreToolUse": json.RawMessage(`[{"hooks":[{"command":"my-guard.sh"}]}]`),
	}
	ours, total := countOurs(events)
	if ours != 1 || total != 3 {
		t.Errorf("应为 ours=1 total=3（含 1 外来组），实际 ours=%d total=%d", ours, total)
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
		t.Errorf("受支持平台应为 claude+zcode，实际 %v", found)
	}
}
