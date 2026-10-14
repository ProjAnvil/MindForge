# Agent Evaluation Report: python-test-engineer

- Path: `/Users/yuhaochen/Documents/codebase/projanvil/MindForge/agents/en/python-test-engineer.md`
- Overall: **87.6 / 100**  Grade: **B**
- Parts: behavior 100.0, writing 58.8, lint 100.0

## Behavior Tests

### ✅ behavior-en-python-test-engineer (100 pts)
- ✔ `tool_args_contain('Read', 'app.py')` 1.00 (threshold 1.00) — 1 call(s) to Read containing 'app.py'
- ✔ `tool_args_contain('Write', 'def test_')` 1.00 (threshold 1.00) — 1 call(s) to Write containing 'def test_'

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
| Delegation fit | 0.85 | Description clearly signals Python test generation with named frameworks, so a main agent can route test-writing tasks without ambiguity. |
| Prompt quality | 0.70 | Role, naming conventions, AAA structure, and coverage strategy are explicit, but the output contract (exact artifact shape, where files go, run/verify step) is only implied. |
| Boundaries | 0.30 | No hard 'must not' rules (e.g., don't modify production code, don't over-mock, when to hand back to the main agent) are stated, and Write/Bash tools are granted without guardrails. |
| Conciseness | 0.50 | Content is repetitive across Expertise/Role/Technologies, and it claims api-design and database-design skills not listed in the frontmatter, wasting tokens and creating inconsistency. |

> A well-structured, domain-rich tester prompt that would benefit from explicit tool-use boundaries and a tighter, less redundant body aligned with its declared skills.

## Improvement Suggestions

1. Add a Boundaries section to the skill prompt with explicit hard 'must not' rules (e.g., do not modify production code, do not over-mock, and define when to hand back to the main agent) plus guardrails for the granted Write/Bash tools.
2. Add an Output Contract section to the skill prompt that specifies the exact test artifact shape, where files go, and the run/verify step the agent must complete.
3. Remove repetitive content across Expertise, Role, and Technologies in the skill prompt and delete api-design and database-design claims that are not listed in the frontmatter.

