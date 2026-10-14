# Agent Evaluation Report: java-unit-test

- Path: `/Users/yuhaochen/Documents/codebase/projanvil/MindForge/agents/zh-cn/java-unit-test.md`
- Overall: **92.5 / 100**  Grade: **A**
- Parts: behavior 100.0, writing 75.0, lint 100.0

## Behavior Tests

### ✅ behavior-zh-cn-java-unit-test (100 pts)
- ✔ `tool_args_contain('Read', 'Calculator.java')` 1.00 (threshold 1.00) — 1 call(s) to Read containing 'Calculator.java'
- ✔ `tool_args_contain('Write', '@Test')` 1.00 (threshold 1.00) — 1 call(s) to Write containing '@Test'

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
| Delegation fit | 0.80 | 描述清晰地说明了工具（JUnit/Mockito/AssertJ）与专注领域，并带有'主动用于'的路由信号，足以让主 agent 判断何时调度。 |
| Prompt quality | 0.80 | 角色、命名约定、AAA 结构、覆盖策略和 do/don't 约束都很明确，但输出契约（如是否写入文件、类命名、包路径、交付格式）未显式规定。 |
| Boundaries | 0.55 | 通过'不应该做'列出了一些禁止项，但缺少何时应停止或交回主 agent、以及对非测试任务（如修复生产代码、运行集成测试）的明确边界。 |
| Conciseness | 0.85 | 内容紧凑、无明显冗余，仅结尾引用外部 README 略占篇幅但可接受。 |

> 这是一份结构清晰、约束明确的 Java 单元测试子 agent 定义，主要待改进点是输出交付契约与任务边界的显式化。

## Improvement Suggestions

1. In the skill's Boundaries section, augment the existing '不应该做' list with explicit stop-and-hand-back conditions—such as when production code changes, integration tests, or out-of-scope work are required—so the skill returns control to the main agent at the right time.
2. In the same Boundaries section, add a clear non-test task boundary stating that fixing production code and running integration tests are out of scope and should be flagged for the main agent instead of attempted.

