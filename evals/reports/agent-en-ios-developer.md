# Agent Evaluation Report: ios-developer

- Path: `/Users/yuhaochen/Documents/codebase/projanvil/MindForge/agents/en/ios-developer.md`
- Overall: **86.1 / 100**  Grade: **B**
- Parts: behavior 100.0, writing 53.8, lint 100.0

## Behavior Tests

### ✅ behavior-en-ios-developer (100 pts)
- ✔ `tool_args_contain('Write', 'SettingsView.swift')` 1.00 (threshold 1.00) — 1 call(s) to Write containing 'SettingsView.swift'
- ✔ `tool_args_contain('Write', 'SwiftUI')` 1.00 (threshold 1.00) — 2 call(s) to Write containing 'SwiftUI'

## Static Lint

Total 100.0, grade A

| Check | Score | Result |
|---|---|---|
| Agent frontmatter (Claude Code load contract) | 100.0 | ✅ |
| Metadata (frontmatter / name / description) | 100.0 | ✅ |
| Delegation (description routes correctly) | 100.0 | ✅ |
| Document structure (sections / substance) | 100.0 | ✅ |
| Clarity (placeholders / length) | 100.0 | ✅ |

## Writing Review (LLM)

| Dimension | Score | Comment |
|---|---|---|
| Delegation fit | 0.70 | Description clearly signals an iOS/SwiftUI specialist tied to relevant skills, so routing is feasible, though it lacks explicit 'use when' triggers to distinguish it from a generic Swift agent. |
| Prompt quality | 0.60 | Role, stack, principles, and workflow are concrete with good ✅/❌ examples, but there is no output contract (deliverable format/summary expectations) and large portions remain unfilled template placeholders. |
| Boundaries | 0.45 | Some 'Don'ts' exist, but there is no statement of scope limits (e.g., non-iOS platforms, backend/DevOps work) or conditions for handing back to the main agent. |
| Conciseness | 0.40 | The useful first half is undercut by duplicated 'Best Practices' and 'Quality Checklist' sections plus empty placeholder blocks that burn tokens without adding guidance. |

> Strong domain content in the opening sections, but the file needs deduplication, placeholder removal, and an explicit boundary/output contract before it is production-ready.

## Improvement Suggestions

1. In the skill file, remove the duplicated Best Practices and Quality Checklist sections and empty placeholder blocks to save tokens and sharpen guidance.
2. In the Boundaries section, add explicit scope limits for non-iOS platforms and backend/DevOps work, along with clear handback conditions for the main agent.
3. In the prompt/skill instructions, add an output contract specifying deliverable format and summary expectations, and add explicit 'use when' triggers to the description to distinguish it from a generic Swift agent.

