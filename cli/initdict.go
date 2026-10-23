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
	fmt.Println("  格式：直译词<TAB>期望写法<TAB>说明；# 开头为注释；re: 前缀写正则词条")
	fmt.Println("  提交到仓库即可让整个团队共享；mindforge tidy 可排版体检")
	return nil
}

func dictTemplate() string {
	return `# mindforge.zh-dict.tsv — 项目级中文术语词典（MindForge）
#
# 三级加载（优先级从低到高）：插件内置 → 用户级（~/.claude/MindForge/）→ 本文件。
# 本文件放项目根，随仓库提交，团队共享；hook 从 cwd 向上发现（.git 边界）。
#
# 格式：直译词<TAB>期望写法<TAB>说明
#   1. 期望写法要能直接替换原文里的直译词，不带括号注释、不写整句模板；
#   2. 拿不准译法的名词保留英文原词（token、agent、hook 不译）；
#   3. 有社区定译的用定译（ablation study=消融实验，ground truth=真值）；
#   4. 可变数字等模式用正则词条：第一列以 re: 开头（如 re:第\s*\d+\s*刀）。
#
# 示例（删掉行首的 # 开始写你自己的词条）：
# 项目黑词	项目写法	本项目特有的直译 bad case
# 槽键	slot 的 key	slot key 硬拼成合成词的直译
`
}
