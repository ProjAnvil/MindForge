# Skill Evaluation Report: python-development

- Path: `/Users/yuhaochen/Documents/codebase/projanvil/MindForge/skills/zh-cn/python-development`
- Overall: **91.5 / 100**  Grade: **A**
- Parts: behavior 100.0, writing 71.7, lint 100.0

## Behavior Tests

### ✅ ref-django-patterns (100 pts)
- ✔ `reference_read(references/django-patterns.md)` 1.00 (threshold 1.00) — read 1 time(s)

### ✅ ref-fastapi-patterns (100 pts)
- ✔ `reference_read(references/fastapi-patterns.md)` 1.00 (threshold 1.00) — read 1 time(s)

### ✅ ref-testing-patterns (100 pts)
- ✔ `reference_read(references/testing-patterns.md)` 1.00 (threshold 1.00) — read 1 time(s)

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
| Semantic accuracy | 0.85 | The name and description accurately frame a broad Python development skill with web frameworks, async, and best practices, though the content is more web-framework-centric than the 'data processing' description implies. |
| Examples & edge cases | 0.55 | Examples illustrate good and bad patterns but contain correctness issues such as deprecated Pydantic @validator, an aiohttp relative URL, and awaiting synchronous SQLAlchemy Session commit/rollback, with limited edge-case coverage. |
| Actionability | 0.75 | Response patterns give clear high-level steps and project layouts, but the referenced pattern files are not included and many rules remain principles rather than executable instructions. |

> A well-structured and broadly accurate Python skill whose actionability is decent, but its examples need modernization and correction to avoid teaching outdated or invalid patterns.

## Reference Coverage

| Reference | Reached | Origin |
|---|---|---|
| references/django-patterns.md | 1× | both |
| references/fastapi-patterns.md | 2× | both |
| references/testing-patterns.md | 1× | both |

## Improvement Suggestions

1. In the Examples & edge cases section, replace the deprecated Pydantic @validator with @field_validator, change the aiohttp relative URL to an absolute URL, and remove await from synchronous SQLAlchemy Session.commit/rollback calls to fix the demonstrated correctness issues.
2. In the Actionability section, include the referenced pattern files or inline their key snippets so readers do not have to locate missing files.
3. In the Examples & edge cases and Actionability sections, convert remaining principles into executable instructions and add edge-case examples such as validation failures, URL resolution, and transaction error/rollback flows.

