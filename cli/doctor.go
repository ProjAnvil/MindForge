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
		fmt.Println("  python3        ✗ 未找到（hook 脚本需要它）")
	} else {
		version := ""
		if out, err := exec.Command(py, "--version").Output(); err == nil {
			version = strings.TrimSpace(string(out))
		}
		fmt.Printf("  python3        ✓ %s\n", version)
	}

	// Dictionary tiers.
	bundled := countEmbeddedEntries()
	fmt.Printf("  词典 内置       %d 条（随 CLI 分发）\n", bundled)
	userDict := filepath.Join(home, ".claude", "MindForge", "terminology.tsv")
	if n, ok := countFileEntries(userDict); ok {
		fmt.Printf("  词典 用户级     %d 条（%s）\n", n, userDict)
	} else {
		fmt.Printf("  词典 用户级     未生成（mindforge install 或首次 hook 运行时创建）\n")
	}
	if path, ok := findProjectDict(cwd); ok {
		n, _ := countFileEntries(path)
		fmt.Printf("  词典 项目级     %d 条（%s）\n", n, path)
	} else {
		fmt.Println("  词典 项目级     未找到（mindforge init dict 生成）")
	}
	if legacy := filepath.Join(home, ".claude", "zh-guard"); dirExists(legacy) {
		fmt.Println("  旧目录提醒     ~/.claude/zh-guard 仍存在；新版已迁移，确认后可手动删除")
	}

	// Per-platform registration.
	doctorClaude(home)
	doctorZcode(home)
	doctorCodex(home)

	if _, err := os.Stat(filepath.Join(home, ".kimi-code")); err == nil {
		fmt.Println("  kimi           检测到 ~/.kimi-code（支持规划中，暂不安装）")
	}
	fmt.Println("\n提示: hook 配置有会话快照——安装或更新后新建会话才生效。")
	return nil
}

func doctorClaude(home string) {
	settingsPath := filepath.Join(home, ".claude", "settings.json")
	if _, err := os.Stat(settingsPath); err != nil {
		fmt.Println("  claude         未检测到 settings.json")
		return
	}
	top, err := loadTopLevel(settingsPath)
	if err != nil {
		fmt.Printf("  claude         ✗ settings.json 解析失败: %v\n", err)
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
		fmt.Println("  claude         未注册（mindforge install --platform=claude）")
		return
	}
	fmt.Printf("  claude         ✓ 已注册 %d/%d 个 hook 事件组，脚本目录 %d 个文件\n", ours, total, files)
}

func doctorZcode(home string) {
	configPath := filepath.Join(home, ".zcode", "cli", "config.json")
	if _, err := os.Stat(configPath); err != nil {
		fmt.Println("  zcode          未检测到 config.json")
		return
	}
	top, err := loadTopLevel(configPath)
	if err != nil {
		fmt.Printf("  zcode          ✗ config.json 解析失败: %v\n", err)
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
		fmt.Printf("  zcode          ✓ 已注册 %d/%d 个 hook 事件组（hooks.enabled=true）\n", ours, total)
	case ours > 0 && !enabled:
		fmt.Println("  zcode          ⚠ 已注册但 hooks.enabled 不是 true（不生效）")
	default:
		fmt.Println("  zcode          未注册（mindforge install --platform=zcode）")
	}
}

func doctorCodex(home string) {
	hooksPath := filepath.Join(home, ".codex", "hooks.json")
	if _, err := os.Stat(hooksPath); err != nil {
		if dirExists(filepath.Join(home, ".codex")) {
			fmt.Println("  codex          未注册（mindforge install --platform=codex；需 codex 0.145+）")
		}
		return
	}
	top, err := loadTopLevel(hooksPath)
	if err != nil {
		fmt.Printf("  codex          ✗ hooks.json 解析失败: %v\n", err)
		return
	}
	var eventsRaw map[string]json.RawMessage
	if h, ok := top["hooks"]; ok {
		_ = json.Unmarshal(h, &eventsRaw)
	}
	ours, total := countOurs(eventsRaw)
	if ours == 0 {
		fmt.Println("  codex          未注册（mindforge install --platform=codex；需 codex 0.145+）")
		return
	}
	fmt.Printf("  codex          ✓ 已注册 %d/%d 个 hook 事件组（首次使用需在 /hooks 里信任）\n", ours, total)
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
	for _, line := range strings.Split(text, "\n") {
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
