package main

import (
	"bufio"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestPromptMultiSelectDefaultsOnEmptyInput(t *testing.T) {
	in := bufio.NewReader(strings.NewReader("\n"))
	picked, err := promptMultiSelect("安装到哪些平台？",
		[]string{"claude  配置: a", "zcode  配置: b"}, "claude,zcode", in)
	if err != nil {
		t.Fatalf("空输入应选默认: %v", err)
	}
	if len(picked) != 2 || picked[0] != "claude" || picked[1] != "zcode" {
		t.Errorf("默认应选 claude+zcode，实际 %v", picked)
	}
}

func TestPromptMultiSelectParsesNumbers(t *testing.T) {
	in := bufio.NewReader(strings.NewReader("2, 1\n"))
	picked, err := promptMultiSelect("选择", []string{"claude  x", "zcode  y"}, "claude", in)
	if err != nil {
		t.Fatalf("编号选择: %v", err)
	}
	if len(picked) != 2 || picked[0] != "zcode" || picked[1] != "claude" {
		t.Errorf("应按输入顺序解析 zcode,claude，实际 %v", picked)
	}
	in2 := bufio.NewReader(strings.NewReader("9\n"))
	if _, err := promptMultiSelect("选择", []string{"a", "b"}, "a", in2); err == nil {
		t.Error("越界编号应报错")
	}
}

func TestPromptSelect(t *testing.T) {
	in := bufio.NewReader(strings.NewReader("2\n"))
	picked, err := promptSelect("语言", []string{"zh-cn: x", "en: y"}, "1", in)
	if err != nil {
		t.Fatal(err)
	}
	if picked != "en: y" {
		t.Errorf("应选第 2 项，实际 %q", picked)
	}
	in2 := bufio.NewReader(strings.NewReader("\n"))
	picked2, _ := promptSelect("语言", []string{"zh-cn: x", "en: y"}, "1", in2)
	if picked2 != "zh-cn: x" {
		t.Errorf("空输入应取默认第 1 项，实际 %q", picked2)
	}
}

// TestInstallInteractiveFlow drives the full interactive install with
// scripted stdin: two prompts, both answered with empty input (defaults).
func TestInstallInteractiveFlow(t *testing.T) {
	home := t.TempDir()
	for _, d := range []string{".claude", ".zcode"} {
		if err := os.MkdirAll(filepath.Join(home, d), 0o755); err != nil {
			t.Fatal(err)
		}
	}
	t.Setenv("HOME", home)
	stdin := strings.NewReader("\n\n")
	if err := runInstall([]string{}, stdin); err != nil {
		t.Fatalf("交互式安装: %v", err)
	}
	// Defaults picked both platforms; registrations present.
	if _, err := os.Stat(filepath.Join(home, ".claude", "settings.json")); err != nil {
		t.Error("claude 未注册（默认应选中）")
	}
	if _, err := os.Stat(filepath.Join(home, ".zcode", "cli", "config.json")); err != nil {
		t.Error("zcode 未注册（默认应选中）")
	}
}
