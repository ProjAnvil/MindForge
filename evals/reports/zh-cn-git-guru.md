# Skill Evaluation Report: git-guru

- Path: `/Users/yuhaochen/Documents/codebase/projanvil/MindForge/skills/zh-cn/git-guru`
- Overall: **90.6 / 100**  Grade: **A**
- Parts: behavior 100.0, writing 70.0, lint 97.9

## Behavior Tests

### ✅ ref-advanced-features (100 pts)
- ✔ `reference_read(references/advanced-features.md)` 1.00 (threshold 1.00) — read 1 time(s)

### ✅ ref-workflows-scenarios (100 pts)
- ✔ `reference_read(references/workflows-scenarios.md)` 1.00 (threshold 1.00) — read 1 time(s)

## Static Lint

Total 97.9, grade A

| Check | Score | Result |
|---|---|---|
| Metadata (frontmatter / name / description) | 100.0 | ✅ |
| Document structure (sections / substance) | 100.0 | ✅ |
| Trigger coverage (when to use) | 100.0 | ✅ |
| Clarity (placeholders / length) | 85.0 | ✅ |
| Asset references (local file existence) | 100.0 | ✅ |
| Test coverage (cases / examples) | 100.0 | ✅ |

## Writing Review (LLM)

| Dimension | Score | Comment |
|---|---|---|
| Semantic accuracy | 0.90 | The name and description accurately reflect the skill's scope (interactive rebase, worktree, reflog, bisect, commit conventions, history cleanup), and the body stays consistent with that promise. |
| Examples & edge cases | 0.50 | The bash snippets are mostly correct but thin and partly unreliable (e.g., `git reflog | grep "commit message"` and a bare `git reset --hard` after locating a lost commit), and no failure paths such as rebase conflicts, failed bisect, or unrecoverable reflog expiry are demonstrated. |
| Actionability | 0.70 | Core commands and the safety ordering (reflog → backup branch → recover) are explicit and executable, but several steps lack verification/rollback detail and the substantive guidance lives only in unshown reference files. |

> A well-scoped and safety-conscious skill whose high-level principles are strong, but it would benefit from more realistic, correct command examples and explicit failure-recovery paths in the main document.

## Reference Coverage

| Reference | Reached | Origin |
|---|---|---|
| references/advanced-features.md | 2× | both |
| references/workflows-scenarios.md | 2× | both |

## Improvement Suggestions

1. [clarity] found unfilled content: unfinished marker (TODO/FIXME/TBD/XXX) → replace the placeholder with real content or remove it
2. In the examples section, replace the unreliable `git reflog | grep "commit message"` and bare `git reset --hard` snippets with an explicit inspect-then-backup-then-recover sequence that includes the exact commit hash variable and verification before destructive reset.
3. In the examples and edge cases section, add failure-path walkthroughs for rebase conflicts, failed bisect, and unrecoverable reflog expiry, each showing the detection command and the rollback or recovery action.

