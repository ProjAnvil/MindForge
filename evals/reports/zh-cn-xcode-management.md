# Skill Evaluation Report: xcode-management

- Path: `/Users/yuhaochen/Documents/codebase/projanvil/MindForge/skills/zh-cn/xcode-management`
- Overall: **93.0 / 100**  Grade: **A**
- Parts: behavior 100.0, writing 76.7, lint 100.0

## Behavior Tests

### ✅ generic (100 pts)
- ✔ `output_contains(['add_files_to_xcode.py'])` 1.00 (threshold 1.00)

## Static Lint

Total 100.0, grade A

| Check | Score | Result |
|---|---|---|
| Metadata (frontmatter / name / description) | 100.0 | ✅ |
| Document structure (sections / substance) | 100.0 | ✅ |
| Trigger coverage (when to use) | 100.0 | ✅ |
| Clarity (placeholders / length) | 100.0 | ✅ |
| Asset references (local file existence) | 100.0 | ✅ |
| Test coverage (cases / examples) | 100.0 | ✅ |

## Writing Review (LLM)

| Dimension | Score | Comment |
|---|---|---|
| Semantic accuracy | 0.85 | The name and description correctly identify Xcode project management and .pbxproj/file-addition automation, though 'expert' and broad iOS/macOS workflow claims slightly exceed the script-focused content. |
| Examples & edge cases | 0.70 | Examples cover common workflows, dry runs, exit codes, and troubleshooting, but several shell snippets are fragile or misaligned on paths (e.g., ORIG_HEAD, comm/grep, scripts/ vs project root). |
| Actionability | 0.75 | The workflows provide explicit commands and checklists, but ambiguous script locations and auto-detection assumptions leave readers unsure how to execute the tool reliably. |

> The SKILL.md is well organized and practical, but it would be stronger with precise script paths, safer examples, and tighter alignment between its broad Xcode claims and its file-addition focus.

## Reference Coverage

| Reference | Reached | Origin |
|---|---|---|
| scripts/add_files_to_xcode.py | unreached | scanned |

## Improvement Suggestions

1. In the examples, resolve the `scripts/` vs project-root ambiguity by documenting a single expected working directory and updating every command path to match it.
2. For the `ORIG_HEAD`, `comm`, and `grep` snippets, add explicit guards and fallbacks (e.g., checking `ORIG_HEAD` exists and handling empty `grep`/`comm` output) so the examples do not fail in edge cases.
3. In the usage/setup section, state the auto-detection assumptions and provide an explicit override or prerequisite checklist so readers know how to execute the tool reliably.

