package main

import (
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestInitDictGeneratesTemplate(t *testing.T) {
	dir := t.TempDir()
	t.Chdir(dir)
	if err := runInit([]string{"dict"}); err != nil {
		t.Fatalf("runInit: %v", err)
	}
	data, err := os.ReadFile(filepath.Join(dir, projectDictName))
	if err != nil {
		t.Fatalf("词典未生成: %v", err)
	}
	text := string(data)
	if !strings.Contains(text, "re:") || !strings.Contains(text, "直译词") {
		t.Error("模板缺格式说明")
	}
	// All example lines stay commented so an empty dict blocks nothing.
	for _, line := range strings.Split(text, "\n") {
		if strings.Contains(line, "\t") && !strings.HasPrefix(line, "#") {
			t.Errorf("模板中存在未注释的活词条（会误伤）: %s", line)
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
		t.Error("已存在时应报错")
	}
	if err := runInit([]string{"dict", "--force"}); err != nil {
		t.Errorf("--force 覆盖失败: %v", err)
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
		t.Errorf("应发现项目根词典，实际 ok=%v path=%s", ok, got)
	}
	// Remove the project dict: from inside the project, walking up must
	// stop at proj/.git — the dict sitting in base (outside the project)
	// must never be discovered. (Without a .git boundary, walking further
	// up is documented behavior.)
	if err := os.Remove(filepath.Join(proj, projectDictName)); err != nil {
		t.Fatal(err)
	}
	if _, ok := findProjectDict(sub); ok {
		t.Error("项目根之外的词典不应被发现（.git 边界）")
	}
}

func TestCountTSVEntries(t *testing.T) {
	text := "# 注释\n\n病灶实验\t消融实验\t说明\n@sync 0.9.9\nre:第\\d 刀\t第 N 刀\t正则\n坏行缺列\n"
	if n := countTSVEntries(text); n != 2 {
		t.Errorf("应数出 2 条（注释、@sync、缺列行不算），实际 %d", n)
	}
}
