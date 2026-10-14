# Agent Evaluation Report: code-reviewer

- Path: `/Users/yuhaochen/Documents/codebase/projanvil/MindForge/agents/zh-cn/code-reviewer.md`
- Overall: **95.9 / 100**  Grade: **A**
- Parts: behavior 100.0, writing 86.2, lint 100.0

## Behavior Tests

### ✅ behavior-zh-cn-code-reviewer (100 pts)
- ✔ `llm_judge(回复是一份结构化的代码评审：指出了给定代码的具体问题——例如, threshold=0.6)` 1.00 (threshold 0.60) — The answer is a structured, severity-ranked code review that identifies concrete service.py issues—silently swallowed payment/mail exceptions, undifferentiated boolean returns, excessive parameters, logging/readability flaws, missing type hints, and missing tests—and provides actionable fixes.

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
| Delegation fit | 0.90 | The description clearly signals architecture/design/quality review expertise and purpose, so a main agent can route with confidence. |
| Prompt quality | 0.95 | Role, boundaries, review workflow, detailed checklist, and a structured output contract are all explicit and actionable. |
| Boundaries | 0.95 | The 'review-only' constraint is crisp, with explicit no-edit/no-commit rules and clear handback triggers (implementation, ADR, missing context). |
| Conciseness | 0.65 | The extensive checklist and language-specific notes risk token bloat, though most content is purposeful and non-redundant. |

> A thorough, well-bounded reviewer definition with strong delegation fit and output contract, held back only by verbosity in its checklist.

## Challenge (adversarial probes)

> challenger fell back to judge (same model; credibility reduced)

| Type | Trigger | Verdict | Note |
|---|---|---|---|
| route | 我有个 Python 数据管道脚本，明天要合并，但总觉得异常处理和上下文管理器那里有点别扭。你能不能只看代码和跑现有测试，帮我判断有没有正确性和可测试性问题？别改，给我一个按严重程度排的报告就行。 | ✘ break | no Task call was made; the router answered directly |
| route | 我们 Go 服务里 handler、service、repository 的依赖方向我看不太懂，有人说违反 DIP，有人说只是包组织问题。你帮我从架构和设计模式角度审一下，指出具体文件和行，给建议但不要动代码。 | ✔ survived |  |
| route | 这个 Spring Boot 接口的代码审查交给谁比较合适？我想知道有没有 OWASP 类问题和错误处理缺陷，只出审查意见，不要重构。 | ✘ break | no Task call was made; the router answered directly |
| no-route | 这段 Java 代码的审查意见我们收到了，你现在直接按意见重构 service 层并提交 commit，顺便把测试也补了。 | ✔ survived |  |
| no-route | 帮我评审一下这个新功能的代码值不值得做，顺便写成用户故事和验收标准，再排个优先级。 | ✘ break | delegated to ['code-reviewer', 'product-manager'] |
| no-route | 我们在两个消息队列之间纠结，你帮我评审现有代码后直接拍板技术选型，并写一份 ADR。 | ✔ survived |  |
| ambiguous | 这个单体拆微服务的方案你帮我把把关，看看现有代码的分层和耦合有没有问题，也告诉我到底该不该拆、怎么拆。 | ✔ survived |  |
| ambiguous | 这个 Python 模块的测试写得很薄，你帮我审一下测试代码质量，然后把缺失的边界用例直接补上并跑覆盖率。 | ✔ survived |  |

Suggested case for break `我有个 Python 数据管道脚本，明天要合并，但总觉得异常处理和上下文管理器那里有点别扭。你能不能只看代码和跑现有测试，帮我判断有没有正确性和可测试性问题？别改，给我一个按严重程度排的报告就行。`:

```python
new_case("probe-route")
    .given(router_agent(AGENTS_DIR, llm=router_llm))
    .when(task('我有个 Python 数据管道脚本，明天要合并，但总觉得异常处理和上下文管理器那里有点别扭。你能不能只看代码和跑现有测试，帮我判断有没有正确性和可测试性问题？别改，给我一个按严重程度排的报告就行。'))
    .then(delegates_to('code-reviewer'))
```

Suggested case for break `这个 Spring Boot 接口的代码审查交给谁比较合适？我想知道有没有 OWASP 类问题和错误处理缺陷，只出审查意见，不要重构。`:

```python
new_case("probe-route")
    .given(router_agent(AGENTS_DIR, llm=router_llm))
    .when(task('这个 Spring Boot 接口的代码审查交给谁比较合适？我想知道有没有 OWASP 类问题和错误处理缺陷，只出审查意见，不要重构。'))
    .then(delegates_to('code-reviewer'))
```

Suggested case for break `帮我评审一下这个新功能的代码值不值得做，顺便写成用户故事和验收标准，再排个优先级。`:

```python
new_case("probe-no-route")
    .given(router_agent(AGENTS_DIR, llm=router_llm))
    .when(task('帮我评审一下这个新功能的代码值不值得做，顺便写成用户故事和验收标准，再排个优先级。'))
    .then(no_delegation())
```

## Improvement Suggestions

1. In the behavior-zh-cn-code-reviewer skill prompt, condense the extensive checklist into grouped, imperative review steps to reduce token usage while preserving all current coverage.
2. In the same skill's language-specific notes, replace verbose prose with a compact zh-CN-specific reference table or short bullet list to cut token bloat.
3. After condensing, rerun the behavior-zh-cn-code-reviewer test to confirm the reduced prompt still passes the existing expectations.

