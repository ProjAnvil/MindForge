package main

import (
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"

	mf "github.com/ProjAnvil/MindForge"
)

// runDoctor checks runtimes, hook registration per platform, and the
// three dictionary tiers, then prints a status table.
func runDoctor(_ []string) error {
	home, err := os.UserHomeDir()
	if err != nil {
		return err
	}
	cwd, _ := os.Getwd()

	fmt.Printf("mindforge doctor (CLI %s)\n\n", Version)

	// Runtime.
	py, pyErr := exec.LookPath("python3")
	if pyErr != nil {
		fmt.Println("  python3        ✗ not found (required by hook scripts)")
	} else {
		version := ""
		if out, err := exec.Command(py, "--version").Output(); err == nil {
			version = strings.TrimSpace(string(out))
		}
		fmt.Printf("  python3        ✓ %s\n", version)
	}

	// Dictionary tiers.
	bundled := countEmbeddedEntries()
	fmt.Printf("  dictionary bundled  %d entries (included with the CLI)\n", bundled)
	userDict := filepath.Join(home, ".claude", "MindForge", "terminology.tsv")
	if n, ok := countFileEntries(userDict); ok {
		fmt.Printf("  dictionary user     %d entries (%s)\n", n, userDict)
	} else {
		fmt.Println("  dictionary user     not created (run mindforge install or a hook to create it)")
	}
	if path, ok := findProjectDict(cwd); ok {
		n, _ := countFileEntries(path)
		fmt.Printf("  dictionary project  %d entries (%s)\n", n, path)
	} else {
		fmt.Println("  dictionary project  not found (run mindforge init dict)")
	}
	if legacy := filepath.Join(home, ".claude", "zh-guard"); dirExists(legacy) {
		fmt.Println("  legacy directory    ~/.claude/zh-guard still exists; verify migration before removing it manually")
	}

	// Per-platform registration.
	doctorClaude(home)
	doctorZcode(home)
	doctorCodex(home)

	if _, err := os.Stat(filepath.Join(home, ".kimi-code")); err == nil {
		fmt.Println("  kimi           ~/.kimi-code detected (support is planned; not installed)")
	}
	fmt.Println("\nNote: Hook configuration is snapshotted per session. Start a new session after installing or updating hooks.")
	return nil
}

func doctorClaude(home string) {
	settingsPath := filepath.Join(home, ".claude", "settings.json")
	if _, err := os.Stat(settingsPath); err != nil {
		fmt.Println("  claude         settings.json not found")
		return
	}
	top, err := loadTopLevel(settingsPath)
	if err != nil {
		fmt.Printf("  claude         ✗ failed to parse settings.json: %v\n", err)
		return
	}
	var eventsRaw map[string]json.RawMessage
	if h, ok := top["hooks"]; ok {
		_ = json.Unmarshal(h, &eventsRaw)
	}
	ours, total := countOurs(eventsRaw)
	hooksDir := filepath.Join(home, ".claude", "MindForge", "hooks")
	files := 0
	if entries, err := os.ReadDir(hooksDir); err == nil {
		files = len(entries)
	}
	if ours == 0 {
		fmt.Println("  claude         not registered (run mindforge install --platform=claude)")
		return
	}
	fmt.Printf("  claude         ✓ registered %d/%d hook event groups; %d files in the hooks directory\n", ours, total, files)
}

func doctorZcode(home string) {
	configPath := filepath.Join(home, ".zcode", "cli", "config.json")
	if _, err := os.Stat(configPath); err != nil {
		fmt.Println("  zcode          config.json not found")
		return
	}
	top, err := loadTopLevel(configPath)
	if err != nil {
		fmt.Printf("  zcode          ✗ failed to parse config.json: %v\n", err)
		return
	}
	var hooksObj map[string]json.RawMessage
	if h, ok := top["hooks"]; ok {
		_ = json.Unmarshal(h, &hooksObj)
	}
	enabled := string(hooksObj["enabled"]) == "true"
	var eventsRaw map[string]json.RawMessage
	if e, ok := hooksObj["events"]; ok {
		_ = json.Unmarshal(e, &eventsRaw)
	}
	ours, total := countOurs(eventsRaw)
	switch {
	case ours > 0 && enabled:
		fmt.Printf("  zcode          ✓ registered %d/%d hook event groups (hooks.enabled=true)\n", ours, total)
	case ours > 0 && !enabled:
		fmt.Println("  zcode          ⚠ registered but hooks.enabled is not true (inactive)")
	default:
		fmt.Println("  zcode          not registered (run mindforge install --platform=zcode)")
	}
}

func doctorCodex(home string) {
	hooksPath := filepath.Join(home, ".codex", "hooks.json")
	if _, err := os.Stat(hooksPath); err != nil {
		if dirExists(filepath.Join(home, ".codex")) {
			fmt.Println("  codex          not registered (run mindforge install --platform=codex; requires codex 0.145+)")
		}
		return
	}
	top, err := loadTopLevel(hooksPath)
	if err != nil {
		fmt.Printf("  codex          ✗ failed to parse hooks.json: %v\n", err)
		return
	}
	var eventsRaw map[string]json.RawMessage
	if h, ok := top["hooks"]; ok {
		_ = json.Unmarshal(h, &eventsRaw)
	}
	ours, total := countOurs(eventsRaw)
	if ours == 0 {
		fmt.Println("  codex          not registered (run mindforge install --platform=codex; requires codex 0.145+)")
		return
	}
	fmt.Printf("  codex          ✓ registered %d/%d hook event groups (trust them in /hooks before first use)\n", ours, total)
}

// countOurs counts hook event groups owned by MindForge and the total
// number of groups (ours + foreign).
func countOurs(events map[string]json.RawMessage) (ours, total int) {
	for _, raw := range events {
		var groups []groupProbe
		if err := json.Unmarshal(raw, &groups); err != nil {
			continue
		}
		total += len(groups)
		for _, g := range groups {
			for _, h := range g.Hooks {
				if strings.Contains(strings.ToLower(h.Command), markerNeedle) {
					ours++
					break
				}
			}
		}
	}
	return ours, total
}

// findProjectDict walks up from dir looking for the project dictionary,
// stopping at the first .git directory (project root boundary).
func findProjectDict(dir string) (string, bool) {
	d := dir
	for {
		candidate := filepath.Join(d, projectDictName)
		if info, err := os.Stat(candidate); err == nil && !info.IsDir() {
			return candidate, true
		}
		if info, err := os.Stat(filepath.Join(d, ".git")); err == nil && info.IsDir() {
			return "", false
		}
		parent := filepath.Dir(d)
		if parent == d {
			return "", false
		}
		d = parent
	}
}

func countFileEntries(path string) (int, bool) {
	data, err := os.ReadFile(path)
	if err != nil {
		return 0, false
	}
	return countTSVEntries(string(data)), true
}

func countEmbeddedEntries() int {
	data, err := mf.Assets.ReadFile(mf.BundledDictPath)
	if err != nil {
		return 0
	}
	return countTSVEntries(string(data))
}

func countTSVEntries(text string) int {
	n := 0
	for line := range strings.SplitSeq(text, "\n") {
		line = strings.TrimSpace(line)
		if line == "" || strings.HasPrefix(line, "#") || strings.HasPrefix(line, "@sync") {
			continue
		}
		if strings.Contains(line, "\t") {
			n++
		}
	}
	return n
}
