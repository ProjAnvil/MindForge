# Skill Evaluation Report: git-guru

- Path: `/Users/yuhaochen/Documents/codebase/projanvil/MindForge/skills/en/git-guru`
- Overall: **93.8 / 100**  Grade: **A**
- Parts: behavior 100.0, writing 81.7, lint 96.4

## Behavior Tests

### ✅ ref-advanced-features (100 pts)
- ✔ `reference_read(references/advanced-features.md)` 1.00 (threshold 1.00) — read 1 time(s)

### ✅ ref-workflows-scenarios (100 pts)
- ✔ `reference_read(references/workflows-scenarios.md)` 1.00 (threshold 1.00) — read 1 time(s)

## Static Lint

Total 96.4, grade A

| Check | Score | Result |
|---|---|---|
| Metadata (frontmatter / name / description) | 100.0 | ✅ |
| Document structure (sections / substance) | 100.0 | ✅ |
| Trigger coverage (when to use) | 100.0 | ✅ |
| Clarity (placeholders / length) | 75.0 | ✅ |
| Asset references (local file existence) | 100.0 | ✅ |
| Test coverage (cases / examples) | 100.0 | ✅ |

## Writing Review (LLM)

| Dimension | Score | Comment |
|---|---|---|
| Semantic accuracy | 0.90 | The name and rich description accurately frame the skill as advanced Git mastery, and the body's coverage of rebase, worktree, reflog, bisect, commits, and history cleanup matches the stated scope. |
| Examples & edge cases | 0.65 | Examples are plentiful and mostly correct, but the automated bisect script's comment ('Return 0 if bug is present (bad), 1 if fixed (good)') inverts git bisect run's actual exit-code convention (0=good, 1-127=bad), which would mislead users, and section numbering skips 7-8. |
| Actionability | 0.90 | Commands are concrete, sequential, and executable, with explicit response patterns and a safety-first workflow that make the guidance easy to follow. |

> A strong, well-scoped and actionable advanced Git skill whose main weakness is a factually reversed git bisect exit-code comment in the automated script example.

## Reference Coverage

| Reference | Reached | Origin |
|---|---|---|
| references/advanced-features.md | 2× | both |
| references/workflows-scenarios.md | 2× | both |

## Improvement Suggestions

1. [clarity] found unfilled content: unfinished marker (TODO/FIXME/TBD/XXX) → replace the placeholder with real content or remove it
2. [clarity] body is 508 lines, exceeding 500; split details into references/ → move reference material into companion files and link them
3. Correct the automated bisect script's comment in the bisect example to state that exit code 0 means good/fixed and 1–127 means bad/bug present, matching git bisect run's actual convention.

