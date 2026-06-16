---
name: codex-lhp
description: Create and maintain Codex Long-Horizon Program plans that orchestrate multiple CodexLHT tasks from repository specs. Use when the user asks to read ai/specs, create or update an ai/programs program directory, break a spec into large LHT milestones, track milestone dependencies and blocked states, decide which LHT is ready to run next, enforce program-level review gates, or distinguish LHT-complete from program-accepted work.
---

# CodexLHP

Use this skill for program-level orchestration above CodexLHT. CodexLHP plans
and governs many LHT runs; it does not execute a workstream itself.

## Resource Map

- Use `scripts/init-program.sh` to create `ai/programs/<program>/`.
- Use `scripts/validate-program.py` to check program graph/state consistency.
- Use `assets/program-template/` as the program document template source.
- Read `references/workflow.md` when creating or updating a program.
- Read `references/review-gates.md` when deciding whether an LHT-complete task
  can become LHP-accepted.

## Core Distinction

- CodexLHT completion means the task-local contract, validations, closeout, and
  task review are satisfied.
- CodexLHP acceptance means the program layer accepts the milestone as
  spec-conformant, architecturally coherent, reviewed, and safe to unblock
  downstream milestones.

A milestone may be LHT-complete but not LHP-accepted.

## Initialize A Program

Create the program scaffold:

```bash
<skill-dir>/scripts/init-program.sh \
  --repo <repo-root> \
  --program <program-id> \
  --title "<Program Title>" \
  --spec-root ai/specs
```

Then read the controlling specs and fill:

- `Program.md`: authority order, objective, global policies
- `SpecBreakdown.md`: extracted requirement clusters
- `Milestones.md`: large LHT-sized milestones
- `DependencyGraph.md`: prerequisites, blockers, unlock rules
- `ReviewGates.md`: AI/human review requirements
- `State.md`: current milestone state and next runnable work

## Maintain A Program

When updating an existing program:

1. Read `AGENTS.md`, relevant `ai/specs/**`, and all files in
   `ai/programs/<program>/`.
2. Inspect linked LHT tasks under `ai/tasks/` and `ai/tasks/completed/`.
3. Update milestone state only from evidence: task contracts, closeout,
   validation events, program review notes, and human decisions.
4. Keep dependency and state changes explicit in `events.jsonl`.
5. Run:

```bash
<skill-dir>/scripts/validate-program.py \
  --repo <repo-root> \
  --program <program-id>
```

## State Rules

Use these milestone states:

- `planned`
- `ready`
- `active`
- `implementation-complete`
- `ai-review`
- `remediation`
- `human-review`
- `accepted`
- `completed`
- `blocked`

Only `ready` milestones may be launched as new LHT tasks. Only `accepted`
milestones may unblock dependent milestones. Move accepted tasks to
`ai/tasks/completed/` only after the program-level acceptance gate passes.

## Relationship To CodexLHT

Use `$codex-lht` for task execution, validation logging, closeout sync, and
task-local contract checks. Use `$codex-lhp` to decide which LHT should exist,
which one is ready to run, whether a completed LHT is accepted, and what remains
blocked.
