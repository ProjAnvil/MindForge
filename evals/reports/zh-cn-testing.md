# Skill Evaluation Report: testing

- Path: `/Users/yuhaochen/Documents/codebase/projanvil/MindForge/skills/zh-cn/testing`
- Overall: **94.0 / 100**  Grade: **A**
- Parts: behavior 100.0, writing 80.0, lint 100.0

## Behavior Tests

### ✅ ref-language-specific-patterns (100 pts)
- ✔ `reference_read(references/language-specific-patterns.md)` 1.00 (threshold 1.00) — read 1 time(s)

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
| Semantic accuracy | 0.95 | The name and description accurately summarize a comprehensive testing skill covering unit/integration tests, TDD/BDD, mocks, and automation guidance. |
| Examples & edge cases | 0.75 | The document provides useful naming, assertion, mocking, and boundary-condition examples, but most examples are templates or snippets rather than concrete failure-path test cases. |
| Actionability | 0.70 | It gives clear high-level workflows and response steps, yet lacks runnable language-specific commands, complete test samples, or unambiguous implementation details. |

> A solid conceptual testing reference, but it would be more actionable with concrete runnable examples and deeper language-specific failure-path coverage.

## Reference Coverage

| Reference | Reached | Origin |
|---|---|---|
| references/language-specific-patterns.md | 1× | both |

## Improvement Suggestions

1. In the workflow/response-steps sections, add runnable language-specific commands and complete copy-paste test samples so readers can execute the guidance without translating templates.
2. In the examples & edge cases section, add concrete failure-path test cases that show expected failures and assertions instead of relying mostly on templates or snippets.
3. In the implementation guidance, add unambiguous step-by-step details for setup and sequencing so the workflow leaves no implementation choices implicit.

