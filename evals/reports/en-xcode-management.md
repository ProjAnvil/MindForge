# Skill Evaluation Report: xcode-management

- Path: `/Users/yuhaochen/Documents/codebase/projanvil/MindForge/skills/en/xcode-management`
- Overall: **92.0 / 100**  Grade: **A**
- Parts: behavior 100.0, writing 73.3, lint 100.0

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
| Semantic accuracy | 0.70 | The name and description broadly match the skill's focus on Xcode project management and file automation, but the description overpromises wide-ranging 'expert' coverage (build settings, SPM, CocoaPods, extensions) while the actual content is largely built around one script. |
| Examples & edge cases | 0.72 | Numerous concrete bash examples, exit codes, and a dedicated troubleshooting section cover key failure paths, though a few commands (e.g., -newer .git/ORIG_HEAD, the comm/grep one-liner) are fragile and could fail silently. |
| Actionability | 0.78 | Workflows are numbered and provide executable commands with flags, but ambiguity around whether script paths are relative to the skill directory or project root may confuse execution. |

> A well-structured, example-rich skill doc that is largely actionable, though its grand 'expert' framing oversells a skill that in practice centers on a single file-adding script.

## Reference Coverage

| Reference | Reached | Origin |
|---|---|---|
| scripts/add_files_to_xcode.py | unreached | scanned |

## Improvement Suggestions

1. Revise the description to narrow or qualify claims of expert coverage for build settings, SPM, CocoaPods, and extensions so it matches the script-centered content.
2. Replace fragile example commands such as `-newer .git/ORIG_HEAD` and the `comm`/`grep` one-liner with more robust equivalents and explicit failure checks in the examples and troubleshooting section.
3. Clarify in the workflows whether each script path is relative to the skill directory or the project root, and use a consistent base path or variable in the commands.

