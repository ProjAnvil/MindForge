# Skill Evaluation Report: api-design

- Path: `/Users/yuhaochen/Documents/codebase/projanvil/MindForge/skills/en/api-design`
- Overall: **95.0 / 100**  Grade: **A**
- Parts: behavior 100.0, writing 83.3, lint 100.0

## Behavior Tests

### ✅ ref-pagination-rate-limiting (100 pts)
- ✔ `reference_read(references/pagination-rate-limiting.md)` 1.00 (threshold 1.00) — read 1 time(s)

### ✅ ref-openapi-template (100 pts)
- ✔ `reference_read(references/openapi-template.md)` 1.00 (threshold 1.00) — read 1 time(s)

### ✅ ref-common-patterns (100 pts)
- ✔ `reference_read(references/common-patterns.md)` 1.00 (threshold 1.00) — read 1 time(s)

### ✅ ref-graphql-patterns (100 pts)
- ✔ `reference_read(references/graphql-patterns.md)` 1.00 (threshold 1.00) — read 1 time(s)

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
| Semantic accuracy | 0.90 | The name 'api-design' and its description accurately reflect the skill's content, though GraphQL is promised prominently yet only covered via an external reference link. |
| Examples & edge cases | 0.75 | Examples are correct and include error formats, status codes, idempotency races, and pagination field-name warnings, but failure paths for versioning/auth flows and any inline GraphQL examples are largely absent. |
| Actionability | 0.85 | The six-phase design process, concrete request/response snippets, and checklist-style questions make the guidance directly executable, though several key artifacts are deferred to unverified reference files. |

> A well-structured, accurate API design skill with strong conventions and clear process guidance, held back mainly by thin inline coverage of GraphQL and edge-case failure examples.

## Reference Coverage

| Reference | Reached | Origin |
|---|---|---|
| references/common-patterns.md | 1× | both |
| references/graphql-patterns.md | 1× | both |
| references/openapi-template.md | 1× | both |
| references/pagination-rate-limiting.md | 2× | both |

## Improvement Suggestions

1. Add failure-path examples for versioning and auth flows in the relevant sections, showing invalid or unsupported versions, missing or expired credentials, and insufficient permissions with status codes and error payloads.
2. Add at least one inline GraphQL example in the GraphQL patterns section, ideally covering an error or authorization failure case to match the edge-case coverage of the REST examples.

