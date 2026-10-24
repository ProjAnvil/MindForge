package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
	"unicode"
)

func TestInitDictGeneratesTemplate(t *testing.T) {
	dir := t.TempDir()
	t.Chdir(dir)
	if err := runInit([]string{"dict"}); err != nil {
		t.Fatalf("runInit: %v", err)
	}
	data, err := os.ReadFile(filepath.Join(dir, projectDictName))
	if err != nil {
		t.Fatalf("dictionary was not generated: %v", err)
	}
	text := string(data)
	if !strings.Contains(text, "re:") || !strings.Contains(text, "直译词") {
		t.Error("template is missing format instructions")
	}
	if !strings.Contains(text, "replace") || !strings.Contains(text, "rewrite") {
		t.Error("template is missing optional rule action instructions")
	}
	// All example lines stay commented so an empty dict blocks nothing.
	for line := range strings.SplitSeq(text, "\n") {
		if strings.Contains(line, "\t") && !strings.HasPrefix(line, "#") {
			t.Errorf("template contains an uncommented rule that could match real text: %s", line)
		}
	}
}

func TestInitDictRefusesOverwriteAndForce(t *testing.T) {
	dir := t.TempDir()
	t.Chdir(dir)
	if err := runInit([]string{"dict"}); err != nil {
		t.Fatal(err)
	}
	if err := runInit([]string{"dict"}); err == nil {
		t.Error("expected an error when the dictionary already exists")
	}
	if err := runInit([]string{"dict", "--force"}); err != nil {
		t.Errorf("--force failed to overwrite the dictionary: %v", err)
	}
}

func TestFindProjectDictRespectsGitBoundary(t *testing.T) {
	base := t.TempDir()
	proj := filepath.Join(base, "proj")
	sub := filepath.Join(proj, "sub")
	if err := os.MkdirAll(filepath.Join(proj, ".git"), 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.MkdirAll(sub, 0o755); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(proj, projectDictName), []byte("# x\n"), 0o644); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(base, projectDictName), []byte("# outside\n"), 0o644); err != nil {
		t.Fatal(err)
	}

	got, ok := findProjectDict(sub)
	if !ok || got != filepath.Join(proj, projectDictName) {
		t.Errorf("expected the project root dictionary, got ok=%v path=%s", ok, got)
	}
	// Remove the project dict: from inside the project, walking up must
	// stop at proj/.git — the dict sitting in base (outside the project)
	// must never be discovered. (Without a .git boundary, walking further
	// up is documented behavior.)
	if err := os.Remove(filepath.Join(proj, projectDictName)); err != nil {
		t.Fatal(err)
	}
	if _, ok := findProjectDict(sub); ok {
		t.Error("dictionary discovery must not cross the .git project boundary")
	}
}

func TestCountTSVEntries(t *testing.T) {
	text := "# 注释\n\n病灶实验\t消融实验\t说明\n@sync 0.9.9\nre:第\\d 刀\t第 N 刀\t正则\n坏行缺列\n"
	if n := countTSVEntries(text); n != 2 {
		t.Errorf("expected 2 entries, excluding comments, @sync and incomplete rows; got %d", n)
	}
}

func captureDoctorOutput(t *testing.T, run func()) string {
	t.Helper()
	output, err := os.CreateTemp(t.TempDir(), "doctor-output-")
	if err != nil {
		t.Fatalf("create output capture: %v", err)
	}
	original := os.Stdout
	os.Stdout = output
	defer func() {
		os.Stdout = original
		if err := output.Close(); err != nil {
			t.Errorf("close output capture: %v", err)
		}
	}()
	run()
	data, err := os.ReadFile(output.Name())
	if err != nil {
		t.Fatalf("read captured output: %v", err)
	}
	return string(data)
}

func assertDoctorEnglish(t *testing.T, output string, expected ...string) {
	t.Helper()
	if strings.ContainsFunc(output, func(r rune) bool { return unicode.Is(unicode.Han, r) }) {
		t.Errorf("doctor output must be in English, got:\n%s", output)
	}
	for _, text := range expected {
		if !strings.Contains(output, text) {
			t.Errorf("expected doctor output to contain %q, got:\n%s", text, output)
		}
	}
}

func TestDoctorOutputEnglish(t *testing.T) {
	for _, installed := range []bool{false, true} {
		name := "missing_dependencies"
		if installed {
			name = "installed"
		}
		t.Run(name, func(t *testing.T) {
			home, project, bin := t.TempDir(), t.TempDir(), t.TempDir()
			t.Setenv("HOME", home)
			t.Setenv("PATH", bin)
			t.Chdir(project)
			if err := os.Mkdir(filepath.Join(project, ".git"), 0o755); err != nil {
				t.Fatalf("create project boundary: %v", err)
			}
			expected := []string{
				"python3", "not found (required by hook scripts)",
				"dictionary bundled", "dictionary user", "not created",
				"dictionary project", "not found (run mindforge init dict)",
				"settings.json not found", "config.json not found",
				"Start a new session after installing or updating hooks",
			}
			if installed {
				if err := os.WriteFile(filepath.Join(bin, "python3"),
					[]byte("#!/bin/sh\nprintf 'Python 3.12.0\\n'\n"), 0o755); err != nil {
					t.Fatalf("create test Python executable: %v", err)
				}
				for _, path := range []string{
					filepath.Join(home, ".claude", "MindForge"),
					filepath.Join(home, ".claude", "zh-guard"),
					filepath.Join(home, ".kimi-code"),
				} {
					if err := os.MkdirAll(path, 0o755); err != nil {
						t.Fatalf("create diagnostic fixture directory: %v", err)
					}
				}
				for _, path := range []string{
					filepath.Join(home, ".claude", "MindForge", "terminology.tsv"),
					filepath.Join(project, projectDictName),
				} {
					if err := os.WriteFile(path, []byte("old\tnew\tnote\n"), 0o644); err != nil {
						t.Fatalf("create dictionary fixture: %v", err)
					}
				}
				expected = []string{
					"Python 3.12.0", "dictionary bundled", "dictionary user",
					"dictionary project", "1 entries", "legacy directory",
					"support is planned; not installed",
					"Start a new session after installing or updating hooks",
				}
			}
			output := captureDoctorOutput(t, func() {
				if err := runDoctor(nil); err != nil {
					t.Fatalf("run doctor: %v", err)
				}
			})
			assertDoctorEnglish(t, output, expected...)
		})
	}
}

func TestDoctorPlatformMessagesEnglish(t *testing.T) {
	for _, platform := range []struct {
		name string
		path string
		run  func(string)
	}{
		{"claude", filepath.Join(".claude", "settings.json"), doctorClaude},
		{"zcode", filepath.Join(".zcode", "cli", "config.json"), doctorZcode},
		{"codex", filepath.Join(".codex", "hooks.json"), doctorCodex},
	} {
		t.Run(platform.name, func(t *testing.T) {
			for _, scenario := range []struct {
				name     string
				config   string
				expected string
			}{
				{"missing", "", "not found"},
				{"invalid_json", "{invalid", "failed to parse"},
				{"unregistered", "{}", "not registered"},
				{"registered", `{"hooks":{"Stop":[{"hooks":[{"command":"python3 /mindforge/hooks/inspect.py"}]}]}}`, "registered 1/1"},
			} {
				t.Run(scenario.name, func(t *testing.T) {
					home := t.TempDir()
					path := filepath.Join(home, platform.path)
					if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
						t.Fatalf("create platform directory: %v", err)
					}
					config, expected := scenario.config, scenario.expected
					if platform.name == "codex" && scenario.name == "missing" {
						expected = "not registered"
					}
					if platform.name == "zcode" && scenario.name == "registered" {
						config = `{"hooks":{"enabled":true,"events":{"Stop":[{"hooks":[{"command":"python3 /mindforge/hooks/inspect.py"}]}]}}}`
					}
					if config != "" {
						if err := os.WriteFile(path, []byte(config), 0o644); err != nil {
							t.Fatalf("write platform configuration: %v", err)
						}
					}
					output := captureDoctorOutput(t, func() { platform.run(home) })
					assertDoctorEnglish(t, output, platform.name, expected)
				})
			}
		})
	}
}

func TestDoctorZcodeDisabledWarningEnglish(t *testing.T) {
	home := t.TempDir()
	path := filepath.Join(home, ".zcode", "cli", "config.json")
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatalf("create zcode directory: %v", err)
	}
	config := `{"hooks":{"enabled":false,"events":{"Stop":[{"hooks":[{"command":"python3 /mindforge/hooks/inspect.py"}]}]}}}`
	if err := os.WriteFile(path, []byte(config), 0o644); err != nil {
		t.Fatalf("write zcode configuration: %v", err)
	}
	output := captureDoctorOutput(t, func() { doctorZcode(home) })
	assertDoctorEnglish(t, output, "registered but hooks.enabled is not true", "inactive")
}
