---
name: prototype
description: Build a disposable project-local prototype to test architecture, state, logic, API, or UI ideas before committing production code. Use when the user wants to prototype, spike, sanity-check a module boundary or data model, mock up UI options, explore design choices, or try something without meeting normal production coverage gates yet.
---

# Prototype

A prototype is **throwaway code that answers a question** inside the current project. It may skip production coverage, polish, and durability while the question is being explored. The debt is acceptable only because the prototype is clearly isolated and ends with an explicit delete-or-promote decision.

## Pick a branch

Identify which question is being answered — from the user's prompt, the surrounding code, or by asking if the user is around:

- **"Does this architecture / module seam / state model feel right?"** → [LOGIC.md](LOGIC.md). Build a tiny interactive app or harness that pushes the module idea through cases that are hard to reason about on paper.
- **"What should this look like?"** → [UI.md](UI.md). Generate several radically different UI variations on a single route, switchable via a URL search param and a floating bottom bar.

The two branches produce very different artifacts — getting this wrong wastes the whole prototype. If the question is genuinely ambiguous and the user isn't reachable, default to whichever branch better matches the surrounding code (a backend module → logic; a page or component → UI) and state the assumption at the top of the prototype.

## Rules that apply to both

1. **Throwaway from day one, and clearly marked as such.** Locate prototype code in a project-local prototype area that keeps it out of production packaging and coverage expectations. Prefer an existing convention such as `prototypes/`, `scratch/`, `.scratch/`, `spikes/`, or `dev/prototypes/`. If none exists, create the smallest obvious location near the target module or route, with `prototype` or `spike` in the path/name.
2. **One command to run.** Whatever the project's existing task runner supports — `pnpm <name>`, `python <path>`, `bun <path>`, etc. The user must be able to start it without thinking.
3. **No production gates while exploring.** Do not force the prototype through normal source coverage, lint strictness, production build integration, or architectural cleanup while the question is still open. If the repo requires config to exclude the prototype from coverage/build output, make the smallest scoped exclusion and label it as prototype-only.
4. **No persistence by default.** State lives in memory. Persistence is the thing the prototype is _checking_, not something it should depend on. If the question explicitly involves a database, hit a scratch DB or a local file with a clear "PROTOTYPE - wipe me" name.
5. **Skip the polish.** No tests, no error handling beyond what makes the prototype _runnable_, no abstractions unless the abstraction is the question. The point is to learn something fast and then delete it.
6. **Surface the state.** After every action (logic) or on every variant switch (UI), print or render the full relevant state so the user can see what changed.
7. **Delete or promote when done.** When the prototype has answered its question, either delete it or refactor the validated idea into the real codebase with production coverage, updated docs, and any relevant ADR/domain-language updates.

## When done

The _answer_ is the only thing worth keeping from a prototype. Capture it somewhere durable (commit message, ADR, issue, or a `NOTES.md` next to the prototype) along with the question it was answering.

If promoting the result, switch back to normal engineering discipline:

- move the validated logic/UI/API into production modules
- add or update behavior-focused tests through `tdd`
- update `CONTEXT.md` or ADRs through `grill-with-docs` when new language or durable decisions emerged
- remove prototype-only coverage/build exclusions
- delete the disposable prototype shell
