---
name: stop-slop
description: Remove predictable AI writing patterns from prose while preserving technical accuracy. Use when drafting, editing, or reviewing README text, documentation, comments, commit messages, PR descriptions, issue text, articles, or user-facing copy.
---

# Stop Slop

Use this skill to make prose direct, specific, and less obviously generated. Do not flatten a user's voice or remove useful technical precision just to satisfy style rules.

## Editing Pass

1. **Preserve meaning**
   - Keep facts, constraints, commands, API names, and code references intact.
   - Do not make claims stronger than the source text supports.
   - Keep the repo's domain language from `CONTEXT.md` when editing project docs.

2. **Cut generated-writing tells**
   - Remove throat-clearing, filler, vague importance claims, stock contrasts, and meta-commentary.
   - Replace business jargon with plain words.
   - Prefer active voice and named actors.
   - Vary sentence length without adding drama.

3. **Make it concrete**
   - Replace abstract claims with the specific behavior, file, decision, risk, or action.
   - Replace "this matters because" with the consequence.
   - Replace "not X but Y" with Y when X is not needed.

4. **Final read**
   - Read the edited prose aloud mentally.
   - Remove anything that sounds like an announcement about the writing rather than the thing itself.
   - Keep useful warmth; remove performative sincerity.

## Load The Right Reference

- Phrase-level cuts and replacements: [phrases.md](references/phrases.md).
- Structural patterns to rewrite: [structures.md](references/structures.md).
- Before/after examples: [examples.md](references/examples.md).

## Quick Checklist

- No throat-clearing opener.
- No unsupported superlatives or lazy extremes.
- No em dashes unless preserving quoted text or a project style that already uses them.
- No generic "it is important to note" phrasing.
- No passive voice where the actor matters.
- No vague "this is powerful/significant/critical" without naming why.
- No paragraph that ends with a manufactured punchline.

## Attribution

This skill is an original Codex-oriented adaptation informed by Hardik Pandya's
`stop-slop`. See the repository `NOTICE.md` for upstream copyright and license
attribution.
