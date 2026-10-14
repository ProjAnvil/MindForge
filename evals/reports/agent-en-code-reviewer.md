# Agent Evaluation Report: code-reviewer

- Path: `/Users/yuhaochen/Documents/codebase/projanvil/MindForge/agents/en/code-reviewer.md`
- Overall: **95.9 / 100**  Grade: **A**
- Parts: behavior 100.0, writing 86.2, lint 100.0

## Behavior Tests

### ✅ behavior-en-code-reviewer (100 pts)
- ✔ `llm_judge(The response is a structured c, threshold=0.6)` 1.00 (threshold 0.60) — The answer is a structured, severity-prioritized code review that concretely identifies the swallowed payment exception, silent mailer failure, oversized multi-responsibility method, parameter/return issues, logging problems, and missing tests, with actionable fixes and a clear next-steps list.

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
| Delegation fit | 0.85 | The description clearly identifies code review expertise and invocation purpose, though it could name concrete triggers such as PR or diff reviews. |
| Prompt quality | 0.90 | The role, review process, checklist, and structured feedback format are explicit, with only minor ambiguity around the Semantic tool and skill declarations. |
| Boundaries | 1.00 | The agent is explicitly review-only, forbids edits, commits, and refactors, and defines clear hand-back cases for implementation, ADR-level decisions, and missing context. |
| Conciseness | 0.70 | The prompt is well organized but quite long, with extensive checklist and language-specific notes that may exceed an ideal token budget for a single-purpose review subagent. |

> This is a strong, well-bounded reviewer definition; trimming checklist length and adding concrete routing triggers would improve delegation efficiency.

## Challenge (adversarial probes)

> challenger fell back to judge (same model; credibility reduced)

| Type | Trigger | Verdict | Note |
|---|---|---|---|
| route | I don’t need line-by-line nitpicks, but the new retry/backoff logic in our payments service feels off. Could you read through the module and tell me whether the design is going to bite us in production? | ✘ break | no Task call was made; the router answered directly |
| route | Before I merge this PR, can you act as a second set of eyes? The diff touches our domain and infra layers and I’m worried the dependency direction got messy. | ✘ break | no Task call was made; the router answered directly |
| route | Our tech lead said this Go package is 'hard to maintain' but didn’t explain. Can you inspect internal/worker and point out concrete design smells and testability problems? | ✘ break | delegated to ['golang-backend-engineer'], not 'code-reviewer' |
| no-route | The review found three critical issues in auth.py. Please fix them, add regression tests, and commit the changes. | ✔ survived |  |
| no-route | We need to decide whether to migrate billing from REST to GraphQL. Write an ADR comparing the options and recommend one. | ✘ break | delegated to ['system-architect'] |
| no-route | Generate JUnit tests for OrderService, especially the edge cases mentioned in the last review. | ✘ break | delegated to ['java-unit-test'] |
| ambiguous | Review this PR for security issues and, if any are small, just patch them directly on the branch so we can ship today. | ✔ survived |  |
| ambiguous | Look at our authentication service and tell me whether we should refactor it to hexagonal architecture. If yes, update the code to match. | ✔ survived |  |

Suggested case for break `I don’t need line-by-line nitpicks, but the new retry/backoff logic in our payments service feels off. Could you read through the module and tell me whether the design is going to bite us in production?`:

```python
new_case("probe-route")
    .given(router_agent(AGENTS_DIR, llm=router_llm))
    .when(task('I don’t need line-by-line nitpicks, but the new retry/backoff logic in our payments service feels off. Could you read through the module and tell me whether the design is going to bite us in production?'))
    .then(delegates_to('code-reviewer'))
```

Suggested case for break `Before I merge this PR, can you act as a second set of eyes? The diff touches our domain and infra layers and I’m worried the dependency direction got messy.`:

```python
new_case("probe-route")
    .given(router_agent(AGENTS_DIR, llm=router_llm))
    .when(task('Before I merge this PR, can you act as a second set of eyes? The diff touches our domain and infra layers and I’m worried the dependency direction got messy.'))
    .then(delegates_to('code-reviewer'))
```

Suggested case for break `Our tech lead said this Go package is 'hard to maintain' but didn’t explain. Can you inspect internal/worker and point out concrete design smells and testability problems?`:

```python
new_case("probe-route")
    .given(router_agent(AGENTS_DIR, llm=router_llm))
    .when(task("Our tech lead said this Go package is 'hard to maintain' but didn’t explain. Can you inspect internal/worker and point out concrete design smells and testability problems?"))
    .then(delegates_to('code-reviewer'))
```

Suggested case for break `We need to decide whether to migrate billing from REST to GraphQL. Write an ADR comparing the options and recommend one.`:

```python
new_case("probe-no-route")
    .given(router_agent(AGENTS_DIR, llm=router_llm))
    .when(task('We need to decide whether to migrate billing from REST to GraphQL. Write an ADR comparing the options and recommend one.'))
    .then(no_delegation())
```

Suggested case for break `Generate JUnit tests for OrderService, especially the edge cases mentioned in the last review.`:

```python
new_case("probe-no-route")
    .given(router_agent(AGENTS_DIR, llm=router_llm))
    .when(task('Generate JUnit tests for OrderService, especially the edge cases mentioned in the last review.'))
    .then(no_delegation())
```

## Improvement Suggestions

1. In the review subagent's prompt, trim the extensive checklist to only the highest-priority review criteria and remove redundant items to reduce token count.
2. In the review subagent's prompt, move language-specific notes out of the main instructions into an optional appendix or conditional reference so they are included only when relevant.
3. In the review subagent's prompt, add a target token/length limit for the instructions and verify the final prompt stays within it.

