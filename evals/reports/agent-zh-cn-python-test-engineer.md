# Agent Evaluation Report: python-test-engineer

- Path: `/Users/yuhaochen/Documents/codebase/projanvil/MindForge/agents/zh-cn/python-test-engineer.md`
- Overall: **88.8 / 100**  Grade: **B**
- Parts: behavior 100.0, writing 62.5, lint 100.0

## Behavior Tests

### ✅ behavior-zh-cn-python-test-engineer (100 pts)
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
| Delegation fit | 0.80 | The description clearly signals test generation in Python with named frameworks and specialties, so a main agent can route on it, though it lacks sharper 'use when' triggers to distinguish it from a general python-development agent. |
| Prompt quality | 0.75 | Role, naming rules, AAA structure, coverage expectations, and a 6-step workflow are explicit, but there is no concrete output contract (file paths, naming of test files, or deliverable format) and the prompt references an external README for templates. |
| Boundaries | 0.45 | The 'should not' list gives some anti-patterns but never states hard limits such as not editing production code or when to hand back to a development/design agent. |
| Conciseness | 0.50 | Framework and tooling lists are duplicated across '核心技术' and '您的角色', and '集成技能' claims api-design and database-design skills not declared in the frontmatter, wasting tokens and creating inconsistency. |

> A solid, well-structured Python test-engineer persona with good conventions and examples, but it needs an explicit output contract, clearer scope boundaries/hand-back rules, and de-duplication of the repeated framework and skill lists.

## Improvement Suggestions

1. In the boundaries/'should not' section, add hard limits that explicitly prohibit editing production code and specify the conditions for handing work back to a development or design agent.
2. In the prompt's output/deliverable instructions, replace the external README template reference with an inline template and define concrete file paths, test-file naming rules, and the required deliverable format.
3. In '核心技术', '您的角色', and '集成技能', remove duplicated framework/tooling lists and either declare the api-design and database-design skills in the frontmatter or remove them from the claimed integration skills.

