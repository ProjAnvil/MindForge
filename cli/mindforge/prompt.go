package main

import (
	"bufio"
	"fmt"
	"strconv"
	"strings"
)

// promptMultiSelect prints numbered items and reads a comma/space
// separated selection. Empty input selects the defaults (a comma-joined
// name list). Unsupported items are refused with the reason printed.
func promptMultiSelect(label string, items []string, defaults string, r *bufio.Reader) ([]string, error) {
	fmt.Printf("? %s\n", label)
	for i, it := range items {
		fmt.Printf("  [%d] %s\n", i+1, it)
	}
	fmt.Printf("选择（编号，逗号或空格分隔；回车=%s）: ", defaults)
	line, err := r.ReadString('\n')
	if err != nil && line == "" {
		return nil, fmt.Errorf("读取输入失败: %w", err)
	}
	line = strings.TrimSpace(line)
	if line == "" {
		return splitList(defaults), nil
	}
	var picked []int
	seen := map[int]bool{}
	for _, tok := range splitList(line) {
		n, err := strconv.Atoi(tok)
		if err != nil || n < 1 || n > len(items) || seen[n] {
			return nil, fmt.Errorf("无效选择 %q（输入 1-%d 的编号）", tok, len(items))
		}
		seen[n] = true
		picked = append(picked, n)
	}
	// Map numbers back to platform names ("claude  配置: ..." → "claude").
	names := make([]string, 0, len(picked))
	for _, n := range picked {
		names = append(names, strings.Fields(items[n-1])[0])
	}
	return names, nil
}

// promptSelect prints numbered items and reads a single choice.
// Empty input selects defaults (an index string like "1").
func promptSelect(label string, items []string, defaults string, r *bufio.Reader) (string, error) {
	fmt.Printf("? %s\n", label)
	for i, it := range items {
		fmt.Printf("  [%d] %s\n", i+1, it)
	}
	fmt.Printf("选择（回车=%s）: ", defaults)
	line, err := r.ReadString('\n')
	if err != nil && line == "" {
		return "", fmt.Errorf("读取输入失败: %w", err)
	}
	line = strings.TrimSpace(line)
	if line == "" {
		line = defaults
	}
	n, err := strconv.Atoi(line)
	if err != nil || n < 1 || n > len(items) {
		return "", fmt.Errorf("无效选择 %q（输入 1-%d 的编号）", line, len(items))
	}
	return items[n-1], nil
}
