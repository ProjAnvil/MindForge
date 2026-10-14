# Agent Evaluation Report: code-reviewer

- Path: `/Users/yuhaochen/Documents/codebase/projanvil/MindForge/agents/en/code-reviewer.md`
- Overall: **84.7 / 100**  Grade: **B**
- Parts: behavior 95.0, writing 57.5, lint 100.0

## Behavior Tests

### ✅ behavior-en-code-reviewer (95 pts)
- ✔ `llm_judge(The response is a structured c, threshold=0.6)` 0.95 (threshold 0.60) — The answer is a structured, severity-prioritized code review that identifies concrete issues such as silently swallowed payment/mailer exceptions, bare excepts, an oversized multi-responsibility method, validation gaps, and logging/readability problems, and it provides actionable fixes.

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
| Delegation fit | 0.80 | The description clearly names the specialty and trigger ('comprehensive code reviews') so a main agent can route confidently, though it lacks explicit negative triggers or disambiguation from a generic reviewer. |
| Prompt quality | 0.90 | Role, principles, five-step process, checklist, feedback template, and a worked example make the output contract highly explicit and executable. |
| Boundaries | 0.25 | No statement of what the agent must not do or when to hand back, and the granted Edit/Write tools directly contradict a read-only review role, while the DO/DON'T list only covers tone rather than scope. |
| Conciseness | 0.35 | The file is heavily padded with overlapping sections (Core Principles vs. Review Checklist vs. Common Issues, and Best Practices vs. Notes/DO-DON'T) plus a long duplicate example, consuming far more tokens than the task requires. |

> A thorough, well-structured reviewer prompt whose actionable output contract is strong but which is bloated with redundant sections and dangerously lacks scope boundaries and a read-only tool set.

## Challenge (adversarial probes)

> challenger fell back to judge (same model; credibility reduced)

| Type | Trigger | Verdict | Note |
|---|---|---|---|
| route | Before I merge this PR, can you sanity-check whether the new notification service will become a maintenance nightmare? I don't want nitpicks, just whether the design/boundaries are sane. | ✘ break | no Task call was made; the router answered directly |
| route | Our caching layer feels gross. Can you poke holes in the abstractions and tell me if we're violating SOLID before it spreads? | ✘ break | no Task call was made; the router answered directly |
| route | The team keeps saying this module is hard to change. Can you diagnose whether it's an architecture/design-pattern problem or just bad naming? | ✘ break | no Task call was made; the router answered directly |
| no-route | Add retry logic with exponential backoff to the Go payment client. | ✘ break | delegated to ['golang-backend-engineer'] |
| no-route | Write JUnit tests for the new TaxCalculator class. | ✘ break | delegated to ['java-unit-test'] |
| no-route | Design an event-driven architecture for the new inventory system and write an ADR comparing Kafka vs Pulsar. | ✘ break | delegated to ['system-architect'] |
| ambiguous | Review this PR for architectural issues and then implement the refactor you recommend. | ✔ survived |  |
| ambiguous | This frontend component is messy and has a state bug. Can you review the design and fix the bug? | ✘ break | The answer asks for the missing component code and offers to perform both design review and bug fix itself, but never splits the design review to a code-reviewer or the bug fix to a frontend-engineer nor clarifies routing, missing the expected mixed-scope handling. |

Suggested case for break `Before I merge this PR, can you sanity-check whether the new notification service will become a maintenance nightmare? I don't want nitpicks, just whether the design/boundaries are sane.`:

```python
new_case("probe-route")
    .given(router_agent(AGENTS_DIR, llm=router_llm))
    .when(task("Before I merge this PR, can you sanity-check whether the new notification service will become a maintenance nightmare? I don't want nitpicks, just whether the design/boundaries are sane."))
    .then(delegates_to('code-reviewer'))
```

Suggested case for break `Our caching layer feels gross. Can you poke holes in the abstractions and tell me if we're violating SOLID before it spreads?`:

```python
new_case("probe-route")
    .given(router_agent(AGENTS_DIR, llm=router_llm))
    .when(task("Our caching layer feels gross. Can you poke holes in the abstractions and tell me if we're violating SOLID before it spreads?"))
    .then(delegates_to('code-reviewer'))
```

Suggested case for break `The team keeps saying this module is hard to change. Can you diagnose whether it's an architecture/design-pattern problem or just bad naming?`:

```python
new_case("probe-route")
    .given(router_agent(AGENTS_DIR, llm=router_llm))
    .when(task("The team keeps saying this module is hard to change. Can you diagnose whether it's an architecture/design-pattern problem or just bad naming?"))
    .then(delegates_to('code-reviewer'))
```

Suggested case for break `Add retry logic with exponential backoff to the Go payment client.`:

```python
new_case("probe-no-route")
    .given(router_agent(AGENTS_DIR, llm=router_llm))
    .when(task('Add retry logic with exponential backoff to the Go payment client.'))
    .then(no_delegation())
```

Suggested case for break `Write JUnit tests for the new TaxCalculator class.`:

```python
new_case("probe-no-route")
    .given(router_agent(AGENTS_DIR, llm=router_llm))
    .when(task('Write JUnit tests for the new TaxCalculator class.'))
    .then(no_delegation())
```

Suggested case for break `Design an event-driven architecture for the new inventory system and write an ADR comparing Kafka vs Pulsar.`:

```python
new_case("probe-no-route")
    .given(router_agent(AGENTS_DIR, llm=router_llm))
    .when(task('Design an event-driven architecture for the new inventory system and write an ADR comparing Kafka vs Pulsar.'))
    .then(no_delegation())
```

Suggested case for break `This frontend component is messy and has a state bug. Can you review the design and fix the bug?`:

```python
new_case("probe-ambiguous")
    .given(router_agent(AGENTS_DIR, llm=router_llm))
    .when(task('This frontend component is messy and has a state bug. Can you review the design and fix the bug?'))
    .then(llm_judge(judge, criteria='Ambiguous/mixed scope. Main agent should ask or split: design review to code-reviewer, bug fix to frontend-engineer; not the whole task to code-reviewer.'))
```

## Improvement Suggestions

1. In the code-reviewer skill definition, add a Boundaries/scope section (and update the DO/DON'T list) stating the agent must not edit/write files and should hand back after review, and remove Edit/Write from the granted tools in favor of read-only tools.
2. Merge the overlapping Core Principles, Review Checklist, and Common Issues sections into one review checklist, and fold Best Practices into the Notes/DO-DON'T list to eliminate duplicated guidance.
3. Replace the long duplicate example with a single concise example (or delete the duplicate) to reduce token usage while preserving the key review behavior.

