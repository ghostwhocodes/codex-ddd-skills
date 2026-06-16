---
name: grill-me
description: Interview the user about a plan, architecture, refactor, API, or product design until reaching shared understanding. Use when the user wants to stress-test an idea, discuss architecture, get grilled on a design, or says "grill me"; use `grill-with-docs` instead when the session should update CONTEXT.md or ADRs.
---

# Grill Me

Interview the user about the plan until the decision tree is clear enough to act on.

## Process

1. Restate the goal and the highest-risk unknowns.
2. Ask one question at a time, resolving dependencies between decisions before moving on.
3. For each question, provide your recommended answer and the trade-off behind it.
4. If a question can be answered by exploring the codebase, explore the codebase instead of asking.
5. Challenge weak assumptions directly: module boundaries, ownership, data shape, user workflow, failure modes, migration path, and testability.
6. End with a concise summary of decisions, open questions, and next actions.

This skill is discussion-only by default. Do not write `CONTEXT.md`, ADRs, PRDs, or issues unless the user asks. If durable documentation becomes clearly useful, suggest switching to `grill-with-docs`.
