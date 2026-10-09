# Skill Evaluation Report: api-design

- Path: `/Users/yuhaochen/Documents/codebase/projanvil/MindForge/skills/zh-cn/api-design`
- Overall: **93.5 / 100**  Grade: **A**
- Parts: behavior 100.0, writing 78.3, lint 100.0

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
| Semantic accuracy | 0.95 | The name and description accurately capture the skill's coverage of RESTful/GraphQL design, versioning, auth, idempotency, and docs, matching the body content well. |
| Examples & edge cases | 0.80 | Strong concrete examples (good/bad URIs, status codes, response/error formats, pagination anti-patterns, idempotency, JWT) but failure-path design is only partially covered and the design-process phases (2-6) are left unelaborated. |
| Actionability | 0.60 | Provides useful templates and principles, but the workflow phases are collapsed into a single vague line and most guidance is declarative reference rather than explicit executable steps. |

> A well-structured, example-rich API design reference whose main weakness is a compressed, non-procedural design workflow that limits step-by-step actionability.

## Reference Coverage

| Reference | Reached | Origin |
|---|---|---|
| references/common-patterns.md | 2× | both |
| references/graphql-patterns.md | 1× | both |
| references/openapi-template.md | 2× | both |
| references/pagination-rate-limiting.md | 4× | both |

## Improvement Suggestions

1. In the workflow section, replace the single vague line describing phases with a numbered step-by-step sequence that gives each phase explicit actions, inputs, and outputs.
2. Throughout the reference guidance, rewrite declarative descriptions into imperative executable steps (e.g., "do X, then Y") instead of only explaining what exists.
3. For each reference topic (pagination/rate limiting, OpenAPI template, common patterns, GraphQL patterns), add a short "how to apply" checklist that turns the existing template or principle into a concrete next action.

