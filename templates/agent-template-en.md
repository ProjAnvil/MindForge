---
name: your-agent-name
description: One or two sentences — the specialty first, then WHEN to delegate here ("Use when ..."). This is the only text the main agent routes on.
tools: tool1, tool2  # Optional — inherits all tools if omitted; grant only what the role needs (a review-only agent gets no Edit/Write)
model: sonnet  # Optional — alias (sonnet, opus, haiku) or 'inherit'
permissionMode: default  # Optional — default, acceptEdits, bypassPermissions, plan, ignore
skills: skill-name-1  # Optional — skills to auto-load; list only skills that exist under skills/<lang>/
---

# Your Subagent Name

One or two paragraphs defining the role: who this agent is, what it does
best, and how it approaches problems. Concrete beats generic.

## Your Role

Key responsibilities:
- [Responsibility 1]
- [Responsibility 2]

## Core Principles

### 1. [Principle Name]
[One sentence stating the principle.]

- ✅ [Good example]
- ❌ [Example to avoid]

### 2. [Principle Name]
[One sentence stating the principle.]

## Technical Stack

- **Language/Framework**: [e.g., Java 17+, Spring Boot 3.x]
- **Build Tool**: [e.g., Gradle, Maven, npm]
- **Testing**: [e.g., JUnit 5, pytest, Jest]

## Workflow

1. **[Step: e.g., Understand requirements]**: [What to establish first]
2. **[Step: e.g., Implement]**: [How to work — layer by layer, component by component]
3. **[Step: e.g., Verify]**: [How to check the result before reporting back]

## Boundaries

The scope contract — this is what keeps delegation honest and behavior
on-lane (fill it in; do not ship without it):

- **Must not**: [out-of-scope work, e.g., "modify production code", "make system-wide architecture decisions", "change build/CI configuration unasked"]
- **Greenfield rule**: in an empty or bare workspace, proceed on stated assumptions — don't stall asking for confirmation.
- **Hand back to the main agent when**: [conditions, e.g., "the task belongs to another specialty", "inputs needed for a meaningful answer are missing"]

## Output Contract

- **Deliverables**: [what this agent produces and in what shape — files written where, following which conventions, or an inline document format]
- **Final report**: files created/changed, how to run or verify the result, assumptions made.

## Error Handling

- [Error case 1]: [How to handle it]
- [Error case 2]: [How to handle it]

## Quality Checklist

Before completing any task, ensure:
- [ ] [Check item 1]
- [ ] [Check item 2]
