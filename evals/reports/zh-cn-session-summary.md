# Skill Evaluation Report: session-summary

- Path: `/Users/yuhaochen/Documents/codebase/projanvil/MindForge/skills/zh-cn/session-summary`
- Overall: **89.5 / 100**  Grade: **B**
- Parts: behavior 100.0, writing 65.0, lint 100.0

## Behavior Tests

### ✅ generic (100 pts)
- ✔ `output_contains(['Postgres'])` 1.00 (threshold 1.00)

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
| Semantic accuracy | 0.90 | The name and description accurately reflect the skill's purpose of summarizing session context for handoff, including tasks, decisions, and next steps. |
| Examples & edge cases | 0.35 | It provides an output template but no concrete worked example and does not address failure paths such as empty sessions, missing context, or blocked-task handling beyond a status label. |
| Actionability | 0.70 | The responsibilities and structured handoff format are clear and executable, but steps remain somewhat generic, lacking guidance on where to source session data or tools to gather state. |

> A well-structured and semantically accurate skill document that would benefit from a concrete example and coverage of edge cases to improve robustness.

## Improvement Suggestions

1. Add a concrete worked example to the handoff output template section that shows a fully populated handoff (inputs, session source, and final structured output) so users can copy the expected format.
2. Add explicit failure-path instructions in the process section for empty sessions, missing context, and blocked tasks, specifying what data to collect, what status to assign, and when to escalate or stop.
3. Add guidance in the responsibilities/steps section on where to source session data and which tools or commands to use to gather current state before producing the handoff.

