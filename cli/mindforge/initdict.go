package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"

	mf "github.com/ProjAnvil/MindForge"
)

const projectDictName = "mindforge.zh-dict.tsv"

// runInit handles "mindforge init dict [--lang=zh-cn] [--force]".
// The dictionary is generated in the current directory so users can run it
// at the exact place they want it (usually the project root).
func runInit(args []string) error {
	if len(args) == 0 || args[0] != "dict" {
		return fmt.Errorf("usage: mindforge init dict [--lang=zh-cn] [--force]")
	}
	fs := flag.NewFlagSet("init dict", flag.ContinueOnError)
	lang := fs.String("lang", "zh-cn", "dictionary language (zh-cn)")
	force := fs.Bool("force", false, "overwrite an existing file")
	if err := fs.Parse(args[1:]); err != nil {
		return err
	}
	if *lang != "zh-cn" {
		return fmt.Errorf("only --lang=zh-cn is currently supported")
	}

	cwd, err := os.Getwd()
	if err != nil {
		return err
	}
	target := filepath.Join(cwd, projectDictName)
	if _, err := os.Stat(target); err == nil && !*force {
		return fmt.Errorf("%s already exists (use --force to overwrite)", projectDictName)
	}
	template, err := mf.Assets.ReadFile(mf.ProjectDictTemplatePath)
	if err != nil {
		return fmt.Errorf("read project dictionary template: %w", err)
	}
	if err := os.WriteFile(target, template, 0o644); err != nil {
		return err
	}
	fmt.Printf("✓ 已生成 %s（项目级词典）\n", target)
	fmt.Println("  优先级：内置 → 用户级 → 项目级（本文件最优先）")
	fmt.Println("  格式：词语<TAB>建议写法（可空）<TAB>含义或语境说明（可空）")
	fmt.Println("  也可只登记词语；默认写作 hook 不读取词典或调用检查工具")
	fmt.Println("  提交到仓库即可让整个团队共享；可用词典整理脚本排版体检")
	return nil
}
