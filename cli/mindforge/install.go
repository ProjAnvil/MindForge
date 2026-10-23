package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	mf "github.com/ProjAnvil/MindForge"
)

// markerMatch identifies hook entries owned by a MindForge install:
// every command we register points into a ".../mindforge/hooks/" directory.
// Case-insensitive so ".claude/MindForge/hooks" and ".zcode/mindforge/hooks"
// both match.
const markerNeedle = "mindforge/hooks/"

// platform describes a detected local agent.
type platform struct {
	name      string // canonical name: claude / zcode / kimi
	config    string // human-readable config path
	supported bool
}

// detectPlatforms reports which local agents exist under home.
func detectPlatforms(home string) []platform {
	return []platform{
		{
			name:      "claude",
			config:    filepath.Join(home, ".claude", "settings.json"),
			supported: dirExists(filepath.Join(home, ".claude")),
		},
		{
			name:      "zcode",
			config:    filepath.Join(home, ".zcode", "cli", "config.json"),
			supported: dirExists(filepath.Join(home, ".zcode")),
		},
		{
			name:      "codex",
			config:    filepath.Join(home, ".codex", "hooks.json"),
			supported: dirExists(filepath.Join(home, ".codex")),
		},
		{
			name:      "kimi",
			config:   filepath.Join(home, ".kimi-code", "config.toml"),
			supported: false, // Kimi adaptation is planned, not shipped (upstream Stop payload issue #2123)
		},
	}
}

func dirExists(p string) bool {
	info, err := os.Stat(p)
	return err == nil && info.IsDir()
}

// installOptions is the fully-resolved install plan inputs.
type installOptions struct {
	platforms []string
	lang      string
}

func runInstall(args []string, stdin io.Reader) error {
	fs := flag.NewFlagSet("install", flag.ContinueOnError)
	langFlag := fs.String("lang", "", "main writing language: zh-cn or en")
	platformFlag := fs.String("platform", "", "comma-separated platforms: claude,zcode")
	yesFlag := fs.Bool("yes", false, "non-interactive: use defaults, no prompts")
	if err := fs.Parse(args); err != nil {
		return err
	}

	home, err := os.UserHomeDir()
	if err != nil {
		return err
	}

	// One shared reader: bufio buffers ahead, so a fresh reader per prompt
	// would swallow the buffered bytes of the next answer.
	reader := bufio.NewReader(stdin)

	detected := detectPlatforms(home)
	// Choose platforms: flag > prompt > (with --yes) all supported.
	var names []string
	if *platformFlag != "" {
		names = splitList(*platformFlag)
	} else {
		supported := supportedNames(detected)
		if len(supported) == 0 {
			return fmt.Errorf("未检测到受支持的平台（Claude Code 或 zcode）。先安装其中一个 agent，或用 --platform 指定")
		}
		if *yesFlag {
			names = supported
		} else {
			picked, err := promptMultiSelect(
				"安装到哪些平台？",
				displayNames(detected),
				strings.Join(supported, ","),
				reader,
			)
			if err != nil {
				return err
			}
			names = picked
		}
	}

	// Resolve language: flag > prompt > default zh-cn.
	lang := *langFlag
	if lang == "" {
		if *yesFlag {
			lang = "zh-cn"
		} else {
			picked, err := promptSelect(
				"主要工作语言？",
				[]string{"zh-cn: 中文（注入中文+英文写作规范）", "en: 英文（仅 ASD-STE100）"},
				"1",
				reader,
			)
			if err != nil {
				return err
			}
			lang = strings.SplitN(picked, ":", 2)[0]
		}
	}
	if lang != "zh-cn" && lang != "en" {
		return fmt.Errorf("不支持的语言 %q（可选：zh-cn、en）", lang)
	}

	opts := installOptions{platforms: names, lang: lang}
	for _, name := range names {
		switch name {
		case "claude":
			if err := installClaude(home, opts.lang); err != nil {
				return fmt.Errorf("claude: %w", err)
			}
		case "zcode":
			if err := installZcode(home, opts.lang); err != nil {
				return fmt.Errorf("zcode: %w", err)
			}
		case "codex":
			if err := installCodex(home, opts.lang); err != nil {
				return fmt.Errorf("codex: %w", err)
			}
		default:
			return fmt.Errorf("未知平台 %q（可选：claude、zcode、codex）", name)
		}
	}
	printInstallSummary(home, opts)
	return nil
}

func supportedNames(detected []platform) []string {
	var out []string
	for _, p := range detected {
		if p.supported {
			out = append(out, p.name)
		}
	}
	return out
}

func displayNames(detected []platform) []string {
	var out []string
	for _, p := range detected {
		suffix := ""
		if !p.supported {
			suffix = "（暂未支持）"
		}
		out = append(out, fmt.Sprintf("%s  配置: %s%s", p.name, p.config, suffix))
	}
	return out
}

func splitList(s string) []string {
	var out []string
	for _, part := range strings.FieldsFunc(s, func(r rune) bool {
		return r == ',' || r == ' '
	}) {
		if part != "" {
			out = append(out, part)
		}
	}
	return out
}

// ---------- shared install pieces ----------

// writeRuntimeFiles extracts the embedded hook payload into hooksDir.
// Shell scripts become executable.
func writeRuntimeFiles(hooksDir string) error {
	if err := os.MkdirAll(hooksDir, 0o755); err != nil {
		return err
	}
	for _, name := range mf.RuntimeFiles {
		data, err := mf.Assets.ReadFile(name)
		if err != nil {
			return err
		}
		dst := filepath.Join(hooksDir, filepath.Base(name))
		mode := os.FileMode(0o644)
		if strings.HasSuffix(name, ".sh") {
			mode = 0o755
		}
		if err := os.WriteFile(dst, data, mode); err != nil {
			return err
		}
	}
	return nil
}

// writeLangMarker writes the style-rules language marker read by
// inject-style-rules.sh ($1 absent → marker file).
func writeLangMarker(hooksDir, lang string) error {
	return os.WriteFile(filepath.Join(hooksDir, "style-rules.lang"), []byte(lang), 0o644)
}

// seedUserDict copies the bundled dictionary to the canonical user home
// (~/.claude/MindForge/terminology.tsv) when absent. Existing user
// dictionaries are never touched; legacy ~/.claude/zh-guard migration is
// handled by the hooks themselves on first run.
func seedUserDict(home string) error {
	userHome := filepath.Join(home, ".claude", "MindForge")
	dict := filepath.Join(userHome, "terminology.tsv")
	if _, err := os.Stat(dict); err == nil {
		return nil
	}
	data, err := mf.Assets.ReadFile(mf.BundledDictPath)
	if err != nil {
		return err
	}
	if err := os.MkdirAll(userHome, 0o755); err != nil {
		return err
	}
	return os.WriteFile(dict, data, 0o644)
}

// groupProbe reads just the commands (and matcher) of a hook group to
// decide ownership.
type groupProbe struct {
	Matcher string `json:"matcher"`
	Hooks   []struct {
		Command string `json:"command"`
	} `json:"hooks"`
}

// filterGroups drops groups whose commands point into a mindforge/hooks
// directory; everything else survives byte-for-byte.
func filterGroups(arrays map[string]json.RawMessage) (map[string][]json.RawMessage, error) {
	out := map[string][]json.RawMessage{}
	for event, raw := range arrays {
		var groups []json.RawMessage
		if err := json.Unmarshal(raw, &groups); err != nil {
			return nil, fmt.Errorf("event %s: %w", event, err)
		}
		for _, g := range groups {
			var p groupProbe
			owned := false
			if err := json.Unmarshal(g, &p); err == nil {
				for _, h := range p.Hooks {
					if strings.Contains(strings.ToLower(h.Command), markerNeedle) {
						owned = true
						break
					}
				}
			}
			if !owned {
				out[event] = append(out[event], g)
			}
		}
	}
	return out, nil
}

// mergeHooks merges our typed groups into the filtered map. Pre-existing
// groups for the same events are kept and ours appended.
func mergeHooks(existing map[string][]json.RawMessage, ours map[string]any) (map[string]any, error) {
	merged := map[string]any{}
	for event, groups := range existing {
		if len(groups) == 0 {
			continue
		}
		// Re-wrap as []any so encoding/json emits a real array.
		arr := make([]any, 0, len(groups))
		for _, g := range groups {
			arr = append(arr, json.RawMessage(g))
		}
		merged[event] = arr
	}
	for event, groups := range ours {
		if prev, ok := merged[event]; ok {
			if prevArr, ok := prev.([]any); ok {
				if arr, ok := groups.([]any); ok {
					merged[event] = append(prevArr, arr...)
					continue
				}
			}
		}
		merged[event] = groups
	}
	return merged, nil
}

// writeJSONFile marshals v with stable 2-space indent.
func writeJSONFile(path string, v any) error {
	var buf bytes.Buffer
	enc := json.NewEncoder(&buf)
	enc.SetIndent("", "  ")
	enc.SetEscapeHTML(false)
	if err := enc.Encode(v); err != nil {
		return err
	}
	return os.WriteFile(path, buf.Bytes(), 0o644)
}

// loadTopLevel reads a JSON object file preserving unknown top-level keys.
// A missing file yields an empty map.
func loadTopLevel(path string) (map[string]json.RawMessage, error) {
	raw, err := os.ReadFile(path)
	if os.IsNotExist(err) {
		return map[string]json.RawMessage{}, nil
	}
	if err != nil {
		return nil, err
	}
	if len(bytes.TrimSpace(raw)) == 0 {
		return map[string]json.RawMessage{}, nil
	}
	top := map[string]json.RawMessage{}
	if err := json.Unmarshal(raw, &top); err != nil {
		return nil, fmt.Errorf("%s 不是合法 JSON（请人工修复后再安装）: %w", path, err)
	}
	return top, nil
}

// ---------- Claude Code ----------

func installClaude(home, lang string) error {
	hooksDir := filepath.Join(home, ".claude", "MindForge", "hooks")
	if err := writeRuntimeFiles(hooksDir); err != nil {
		return err
	}
	if err := writeLangMarker(hooksDir, lang); err != nil {
		return err
	}
	if err := seedUserDict(home); err != nil {
		return err
	}

	settingsPath := filepath.Join(home, ".claude", "settings.json")
	top, err := loadTopLevel(settingsPath)
	if err != nil {
		return err
	}
	var eventsRaw map[string]json.RawMessage
	if h, ok := top["hooks"]; ok {
		if err := json.Unmarshal(h, &eventsRaw); err != nil {
			return fmt.Errorf("settings.json 的 hooks 字段解析失败: %w", err)
		}
	}
	existing, err := filterGroups(eventsRaw)
	if err != nil {
		return err
	}
	merged, err := mergeHooks(existing, claudeGroups(hooksDir))
	if err != nil {
		return err
	}
	hooksBytes, err := json.Marshal(merged)
	if err != nil {
		return err
	}
	top["hooks"] = json.RawMessage(hooksBytes)
	return writeJSONFile(settingsPath, top)
}

// claudeGroups is the registration template for Claude Code. Subagent
// events are Claude-only and included; the language variant travels via
// the style-rules.lang marker file.
func claudeGroups(hooksDir string) map[string]any {
	bash := "bash " + filepath.Join(hooksDir, "inject-style-rules.sh")
	inject := "python3 " + filepath.Join(hooksDir, "inject.py")
	inspect := "python3 " + filepath.Join(hooksDir, "inspect.py")
	fileGuard := "python3 " + filepath.Join(hooksDir, "inspect-file.py")
	return map[string]any{
		"SessionStart":     []any{group("", bash)},
		"UserPromptSubmit": []any{group("", bash), group("", inject)},
		"SubagentStart":    []any{group("", bash)},
		"PreToolUse":       []any{group("Write|Edit|NotebookEdit", fileGuard)},
		"Stop":             []any{group("", inspect)},
		"SubagentStop":     []any{group("", inspect)},
	}
}

func group(matcher string, commands ...string) map[string]any {
	hooks := make([]any, 0, len(commands))
	for _, c := range commands {
		hooks = append(hooks, map[string]any{"type": "command", "command": c})
	}
	g := map[string]any{"hooks": hooks}
	if matcher != "" {
		g["matcher"] = matcher
	}
	return g
}

// ---------- zcode ----------

func installZcode(home, lang string) error {
	hooksDir := filepath.Join(home, ".zcode", "mindforge", "hooks")
	if err := writeRuntimeFiles(hooksDir); err != nil {
		return err
	}
	if err := writeLangMarker(hooksDir, lang); err != nil {
		return err
	}
	if err := seedUserDict(home); err != nil {
		return err
	}

	configPath := filepath.Join(home, ".zcode", "cli", "config.json")
	if err := os.MkdirAll(filepath.Dir(configPath), 0o755); err != nil {
		return err
	}
	top, err := loadTopLevel(configPath)
	if err != nil {
		return err
	}
	// hooks object: preserve unknown keys (timeoutMs, maxOutputBytes, ...).
	hooksObj := map[string]json.RawMessage{}
	if h, ok := top["hooks"]; ok {
		if err := json.Unmarshal(h, &hooksObj); err != nil {
			return fmt.Errorf("config.json 的 hooks 字段解析失败: %w", err)
		}
	}
	var eventsRaw map[string]json.RawMessage
	if e, ok := hooksObj["events"]; ok {
		if err := json.Unmarshal(e, &eventsRaw); err != nil {
			return fmt.Errorf("config.json 的 hooks.events 解析失败: %w", err)
		}
	}
	existing, err := filterGroups(eventsRaw)
	if err != nil {
		return err
	}
	merged, err := mergeHooks(existing, zcodeGroups(hooksDir))
	if err != nil {
		return err
	}
	eventsBytes, err := json.Marshal(merged)
	if err != nil {
		return err
	}
	hooksObj["enabled"] = json.RawMessage("true")
	hooksObj["events"] = json.RawMessage(eventsBytes)
	hooksBytes, err := json.Marshal(hooksObj)
	if err != nil {
		return err
	}
	top["hooks"] = json.RawMessage(hooksBytes)
	return writeJSONFile(configPath, top)
}

// zcodeGroups is the registration template for zcode. zcode supports only
// its 7 events (no SubagentStart/SubagentStop), and the Stop hook needs
// --platform because user-config hooks do not receive ZCODE_PLUGIN_ROOT
// (that env var is injected for plugin hooks only).
func zcodeGroups(hooksDir string) map[string]any {
	bash := "bash " + filepath.Join(hooksDir, "inject-style-rules.sh")
	inject := "python3 " + filepath.Join(hooksDir, "inject.py")
	inspect := "python3 " + filepath.Join(hooksDir, "inspect.py") + " --platform"
	fileGuard := "python3 " + filepath.Join(hooksDir, "inspect-file.py")
	return map[string]any{
		"SessionStart":     []any{group("", bash)},
		"UserPromptSubmit": []any{group("", bash), group("", inject)},
		"PreToolUse":       []any{group("Write|Edit", fileGuard)},
		"Stop":             []any{group("", inspect)},
	}
}

// ---------- codex ----------

// installCodex writes hooks into ~/.codex/hooks.json (single-format
// config; Codex warns when hooks.json and config.toml inline hooks are
// both present, so we never touch config.toml). The hooks feature is on
// by default since codex 0.145.
func installCodex(home, lang string) error {
	hooksDir := filepath.Join(home, ".codex", "mindforge", "hooks")
	if err := writeRuntimeFiles(hooksDir); err != nil {
		return err
	}
	if err := writeLangMarker(hooksDir, lang); err != nil {
		return err
	}
	if err := seedUserDict(home); err != nil {
		return err
	}

	hooksPath := filepath.Join(home, ".codex", "hooks.json")
	if err := os.MkdirAll(filepath.Dir(hooksPath), 0o755); err != nil {
		return err
	}
	top, err := loadTopLevel(hooksPath)
	if err != nil {
		return err
	}
	var eventsRaw map[string]json.RawMessage
	if h, ok := top["hooks"]; ok {
		if err := json.Unmarshal(h, &eventsRaw); err != nil {
			return fmt.Errorf("hooks.json 的 hooks 字段解析失败: %w", err)
		}
	}
	existing, err := filterGroups(eventsRaw)
	if err != nil {
		return err
	}
	merged, err := mergeHooks(existing, codexGroups(hooksDir))
	if err != nil {
		return err
	}
	hooksBytes, err := json.Marshal(merged)
	if err != nil {
		return err
	}
	top["hooks"] = json.RawMessage(hooksBytes)
	return writeJSONFile(hooksPath, top)
}

// codexGroups is the registration template for Codex. Its hook engine
// mirrors Claude Code's contract (same hooks.json shape, stdin carries
// cwd, additionalContext honored) with platform differences: no Subagent
// events, file edits go through apply_patch/Edit/Write, and Stop uses
// the decision:"block" contract — same as zcode, so the Stop command
// reuses the --platform flag.
func codexGroups(hooksDir string) map[string]any {
	bash := "bash " + filepath.Join(hooksDir, "inject-style-rules.sh")
	inject := "python3 " + filepath.Join(hooksDir, "inject.py")
	inspect := "python3 " + filepath.Join(hooksDir, "inspect.py") + " --platform"
	fileGuard := "python3 " + filepath.Join(hooksDir, "inspect-file.py")
	return map[string]any{
		"SessionStart":     []any{group("", bash)},
		"UserPromptSubmit": []any{group("", bash), group("", inject)},
		"PreToolUse":       []any{group("apply_patch|Edit|Write", fileGuard)},
		"Stop":             []any{group("", inspect)},
	}
}

// ---------- summary ----------

func printInstallSummary(home string, opts installOptions) {
	fmt.Println("✓ 安装完成")
	for _, name := range opts.platforms {
		switch name {
		case "claude":
			fmt.Printf("  claude: hook 已注册到 ~/.claude/settings.json，脚本在 ~/.claude/MindForge/hooks/\n")
		case "zcode":
			fmt.Printf("  zcode:  hook 已注册到 ~/.zcode/cli/config.json（hooks.enabled=true），脚本在 ~/.zcode/mindforge/hooks/\n")
		case "codex":
			fmt.Printf("  codex:  hook 已注册到 ~/.codex/hooks.json，脚本在 ~/.codex/mindforge/hooks/\n")
			fmt.Println("          首次运行 Codex 会要求信任新 hook（/hooks 命令审核；CI 可用 --dangerously-bypass-hook-trust）")
		}
	}
	fmt.Printf("  语言: %s（style-rules.lang 标记）\n", opts.lang)
	fmt.Printf("  用户词典: ~/.claude/MindForge/terminology.tsv（三级加载：内置 → 用户级 → 项目级）\n")
	fmt.Println("  项目词典: 在项目根放 mindforge.zh-dict.tsv（mindforge init dict 生成）")
	fmt.Println("  MCP（可选）: claude mcp add term-dict -- python3 ~/.claude/MindForge/hooks/term-dict-server.py")
	fmt.Println("  生效: 已打开的会话不热更新，新建会话后生效")
}
