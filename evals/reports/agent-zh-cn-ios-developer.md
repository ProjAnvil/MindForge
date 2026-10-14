# Agent Evaluation Report: ios-developer

- Path: `/Users/yuhaochen/Documents/codebase/projanvil/MindForge/agents/zh-cn/ios-developer.md`
- Overall: **92.9 / 100**  Grade: **A**
- Parts: behavior 100.0, writing 76.2, lint 100.0

## Behavior Tests

### ✅ behavior-zh-cn-ios-developer (100 pts)
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
| Delegation fit | 0.90 | The description clearly states when to proactively use this agent for Swift/SwiftUI iOS feature, UI, and data-layer work, so routing is easy to decide. |
| Prompt quality | 0.80 | The role, tech constraints, workflow, and quality expectations are explicit, though a concrete output/deliverable contract is missing. |
| Boundaries | 0.55 | It lists coding anti-patterns to avoid but lacks clear handoff criteria and does not explicitly forbid non-iOS work or define collaboration limits. |
| Conciseness | 0.80 | The prompt is reasonably compact for its scope and mostly avoids redundancy, with only some examples and checklist items that could be tightened. |

> A strong iOS-focused subagent with clear routing and technical constraints, but it would benefit from explicit handoff boundaries and a clearer output contract.

## Improvement Suggestions

1. In the skill's Boundaries section, add clear handoff criteria that specify when to stop and pass work to other roles (such as backend, Android, or design).
2. In the same Boundaries section, explicitly state that non-iOS development work is out of scope and must be declined or redirected.
3. Add collaboration limits to the Boundaries section that define what the skill will and will not do when working with other specialists, including required inputs and expected outputs.

