package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"
)

const projectDictName = "mindforge.zh-dict.tsv"

// runInit handles "mindforge init dict [--lang=zh-cn] [--force]".
// The dictionary is generated in the current directory so users can run it
// at the exact place they want it (usually the project root).
func runInit(args []string) error {
	if len(args) == 0 || args[0] != "dict" {
		return fmt.Errorf("用法: mindforge init dict [--lang=zh-cn] [--force]")
	}
	fs := flag.NewFlagSet("init dict", flag.ContinueOnError)
	lang := fs.String("lang", "zh-cn", "dictionary language (zh-cn)")
	force := fs.Bool("force", false, "overwrite an existing file")
	if err := fs.Parse(args[1:]); err != nil {
		return err
	}
	if *lang != "zh-cn" {
		return fmt.Errorf("暂只支持 --lang=zh-cn")
	}

	cwd, err := os.Getwd()
	if err != nil {
		return err
	}
	target := filepath.Join(cwd, projectDictName)
	if _, err := os.Stat(target); err == nil && !*force {
		return fmt.Errorf("%s 已存在（--force 覆盖）", projectDictName)
	}
	if err := os.WriteFile(target, []byte(dictTemplate()), 0o644); err != nil {
		return err
	}
	fmt.Printf("✓ 已生成 %s（项目级词典）\n", target)
	fmt.Println("  优先级：内置 → 用户级 → 项目级（本文件最优先）")
	fmt.Println("  格式：直译词<TAB>期望写法<TAB>说明[<TAB>动作]；默认 rewrite；明确同义词才标 replace")
	fmt.Println("  提交到仓库即可让整个团队共享；mindforge tidy 可排版体检")
	return nil
}

func dictTemplate() string {
	return `# mindforge.zh-dict.tsv — 项目级中文术语词典（MindForge）
# 优先级：内置 → 用户级 → 本文件；放项目根随仓库共享。
# 格式：直译词<TAB>期望写法<TAB>说明[<TAB>动作]
# 默认 rewrite：结合原句改写，保留原意；明确同义词才标 replace。
# re: 为正则词条，只能按语境改写；拿不准的术语保留英文。

# 示例（删掉行首的 # 启用）：
# 项目旧词	项目写法	按原句改写
# 机械胳膊	机械臂	robot arm	replace
# 病灶分析	分析问题原因	定位问题原因	rewrite
`
}
