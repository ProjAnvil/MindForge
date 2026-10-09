# Skill Evaluation Report: session-summary

- Path: `/Users/yuhaochen/Documents/codebase/projanvil/MindForge/skills/en/session-summary`
- Overall: **90.7 / 100**  Grade: **A**
- Parts: behavior 100.0, writing 70.0, lint 98.3

## Behavior Tests

### ✅ generic (100 pts)
- ✔ `output_contains(['Postgres'])` 1.00 (threshold 1.00)

## Static Lint

Total 98.3, grade A

| Check | Score | Result |
|---|---|---|
| Metadata (frontmatter / name / description) | 100.0 | ✅ |
| Document structure (sections / substance) | 90.0 | ✅ |
| Trigger coverage (when to use) | 100.0 | ✅ |
| Clarity (placeholders / length) | 100.0 | ✅ |
| Asset references (local file existence) | 100.0 | ✅ |
| Test coverage (cases / examples) | 100.0 | ✅ |

## Writing Review (LLM)

| Dimension | Score | Comment |
|---|---|---|
| Semantic accuracy | 0.90 | The name and description accurately capture the skill's purpose of producing a session handover summary with tasks, decisions, and next steps, matching the body's format and responsibilities. |
| Examples & edge cases | 0.50 | The handover template serves as a concrete example, but there is no coverage of failure paths such as empty sessions, blocked or incomplete work, or how to handle missing context. |
| Actionability | 0.70 | The responsibilities and output format are clear and executable, though steps like 'Generate Handover Prompt' (missing article) are slightly vague and lack guidance on prioritization or length limits. |

> A well-structured, semantically accurate handover skill whose main weakness is the absence of edge-case and failure-path examples.

## Improvement Suggestions

1. [structure] body is ~246 words; aim for at least 250 → expand thin sections with concrete detail
2. Add explicit failure-path examples to the handover template for empty sessions, blocked or incomplete work, and missing context, specifying how the agent should respond in each case.
3. Add prioritization and length-limit guidance to the output format or responsibilities so the handover prompt tells the agent what to include first and how concise to be.

