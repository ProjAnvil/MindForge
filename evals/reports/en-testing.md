# Skill Evaluation Report: testing

- Path: `/Users/yuhaochen/Documents/codebase/projanvil/MindForge/skills/en/testing`
- Overall: **91.0 / 100**  Grade: **A**
- Parts: behavior 100.0, writing 70.0, lint 100.0

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
| Semantic accuracy | 0.85 | The name and description accurately reflect the skill's coverage of unit/integration testing, TDD/BDD, mocking, and coverage guidance, though the promised 'multiple languages' and 'test automation' content is only referenced, not delivered in-doc. |
| Examples & edge cases | 0.55 | Examples are largely language-agnostic placeholders (e.g., [Prepare test objects]) rather than concrete runnable cases, and while failure paths like null inputs and exceptions are listed, no worked failure-path examples are shown. |
| Actionability | 0.70 | The Red-Green-Refactor cycle, concrete coverage targets, and mock-vs-don't-mock rules are explicit and usable, but many sections are opinionated checklists without rationale and the templates require the reader to fill in blanks themselves. |

> A well-organized and readable testing skill with clear principles and numeric targets, but its heavy reliance on abstract placeholders and deferral of real examples to a reference file keeps it from being fully concrete or executable on its own.

## Reference Coverage

| Reference | Reached | Origin |
|---|---|---|
| references/language-specific-patterns.md | 1× | both |

## Improvement Suggestions

1. Replace placeholder examples such as [Prepare test objects] with concrete, runnable, language-specific test snippets in the Examples & edge cases section.
2. Add a brief rationale for each rule in the opinionated checklist sections to explain why the practice matters.
3. Turn fill-in-the-blank templates into completed worked examples or annotate each blank with sample values so readers can apply them without guessing.

