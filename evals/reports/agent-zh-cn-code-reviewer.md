# Agent Evaluation Report: code-reviewer

- Path: `/Users/yuhaochen/Documents/codebase/projanvil/MindForge/agents/zh-cn/code-reviewer.md`
- Overall: **88.8 / 100**  Grade: **B**
- Parts: behavior 100.0, writing 62.5, lint 100.0

## Behavior Tests

### ✅ behavior-zh-cn-code-reviewer (100 pts)
- ✔ `llm_judge(回复是一份结构化的代码评审：指出了给定代码的具体问题——例如, threshold=0.6)` 1.00 (threshold 0.60) — The answer is a structured, severity-ordered code review that identifies concrete issues in service.py—such as silently swallowed payment exceptions, an overburdened method with many dependencies, poor return semantics, magic strings/log formatting, and missing tests—and provides actionable remediation steps.

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
| Delegation fit | 0.85 | 描述清晰界定了架构/设计模式/代码质量审查的专长领域,主智能体可据此判断何时路由,但未点明具体触发场景(如 PR 审查、重构评审)。 |
| Prompt quality | 0.90 | 角色定位、审查重点、流程步骤与反馈模板(含代码审查总结结构)都写得非常明确,输出契约清晰可执行。 |
| Boundaries | 0.45 | 虽列出沟通层面的「不应该做」清单,却缺少范围边界与交接条件,尤其授予了 Edit/Write 工具与「只审查不建议改代码」的定位存在潜在冲突。 |
| Conciseness | 0.30 | 篇幅过长且高度重复(两处「最佳实践」、多处内容交叠),远超必要 token 预算,大量条目可合并精简。 |

> 内容专业、输出模板扎实,但边界模糊、工具权限与审查定位不符,且篇幅冗长重复,建议精简并明确只读权限与交接规则。

## Challenge (adversarial probes)

> challenger fell back to judge (same model; credibility reduced)

| Type | Trigger | Verdict | Note |
|---|---|---|---|
| route | I have a PR that technically works but feels gross. Before I merge, can you play architecture skeptic and tell me where it will hurt in six months? No edits, just a prioritized review of abstraction boundaries, SOLID, and hidden coupling. | ✔ survived |  |
| route | Our new hire wrote this module. I suspect it is a God object and maybe Singleton abuse. Can you inspect it and tell me if I am overreacting, with concrete file/line examples and suggestions? | ✘ break | no Task call was made; the router answered directly |
| route | Take a look at this Go package. I do not need implementation work, but I need an expert opinion on package organization, interface design, and whether error handling and concurrency patterns follow best practices. | ✘ break | no Task call was made; the router answered directly |
| no-route | Refactor this 500-line Java class into smaller classes and apply the Strategy pattern. | ✔ survived |  |
| no-route | Write unit tests for this Java service with JUnit, Mockito, and AssertJ, aiming for 90% coverage. | ✘ break | delegated to ['java-unit-test'] |
| no-route | Design a new microservice architecture for our payments platform and write ADRs comparing gRPC vs REST. | ✘ break | delegated to ['system-architect'] |
| ambiguous | Review this Svelte component for accessibility and state management; if there are issues, please fix them. | ✘ break | The answer sensibly asks for the missing component code, but it does not resolve the review-vs-implementation ambiguity or split the work between code-reviewer for review findings and frontend-engineer for Svelte fixes as expected, instead routing all review and fixes to frontend-engineer. |
| ambiguous | Our Java service has a SAST finding for SQL injection. Assess whether it is exploitable and then patch it. | ✔ survived |  |

Suggested case for break `Our new hire wrote this module. I suspect it is a God object and maybe Singleton abuse. Can you inspect it and tell me if I am overreacting, with concrete file/line examples and suggestions?`:

```python
new_case("probe-route")
    .given(router_agent(AGENTS_DIR, llm=router_llm))
    .when(task('Our new hire wrote this module. I suspect it is a God object and maybe Singleton abuse. Can you inspect it and tell me if I am overreacting, with concrete file/line examples and suggestions?'))
    .then(delegates_to('code-reviewer'))
```

Suggested case for break `Take a look at this Go package. I do not need implementation work, but I need an expert opinion on package organization, interface design, and whether error handling and concurrency patterns follow best practices.`:

```python
new_case("probe-route")
    .given(router_agent(AGENTS_DIR, llm=router_llm))
    .when(task('Take a look at this Go package. I do not need implementation work, but I need an expert opinion on package organization, interface design, and whether error handling and concurrency patterns follow best practices.'))
    .then(delegates_to('code-reviewer'))
```

Suggested case for break `Write unit tests for this Java service with JUnit, Mockito, and AssertJ, aiming for 90% coverage.`:

```python
new_case("probe-no-route")
    .given(router_agent(AGENTS_DIR, llm=router_llm))
    .when(task('Write unit tests for this Java service with JUnit, Mockito, and AssertJ, aiming for 90% coverage.'))
    .then(no_delegation())
```

Suggested case for break `Design a new microservice architecture for our payments platform and write ADRs comparing gRPC vs REST.`:

```python
new_case("probe-no-route")
    .given(router_agent(AGENTS_DIR, llm=router_llm))
    .when(task('Design a new microservice architecture for our payments platform and write ADRs comparing gRPC vs REST.'))
    .then(no_delegation())
```

Suggested case for break `Review this Svelte component for accessibility and state management; if there are issues, please fix them.`:

```python
new_case("probe-ambiguous")
    .given(router_agent(AGENTS_DIR, llm=router_llm))
    .when(task('Review this Svelte component for accessibility and state management; if there are issues, please fix them.'))
    .then(llm_judge(judge, criteria='Ambiguous. Main agent should ask whether the user wants review or implementation, or split: code-reviewer for review findings, frontend-engineer for Svelte fixes.'))
```

## Improvement Suggestions

1. In the skill's tool permissions, remove Edit/Write or explicitly restrict them to non-mutating use to resolve the conflict with the 'review only, do not suggest code changes' positioning.
2. In the skill prompt, add explicit scope boundaries and handoff conditions so reviewers know what is in-scope, out-of-scope, and when to stop or escalate.
3. In the skill content, merge the two 'best practices' sections and overlapping items into one concise checklist to reduce token usage.

