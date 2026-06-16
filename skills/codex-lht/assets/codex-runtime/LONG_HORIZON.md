# CodexLHT Workflow

Use `__TASK_ROOT_REL__/<task-slug>/` for workstreams that should survive across
multiple Codex runs or isolated worktrees.

## Task Layout

Each task lives under `__TASK_ROOT_REL__/<task-slug>/` with:

- `Prompt.md`: product or technical spec
- `Contract.md`: machine-checkable completion boundary
- `Plan.md`: advisory decomposition and validation cadence
- `Implement.md`: execution runbook
- `Documentation.md`: live status log and validation history
- `Closeout.md`: structured closeout evidence
- optional `ReviewResume.md`: review-driven repair context
- `events.jsonl`: wrapper-authored event log

Reusable policy files may live under `ai/policies/<policy-id>/Policy.md`.

## Default Implementation Stance

- Every change should leave the touched area of the codebase in a better state
  than before.
- Do not preserve or introduce unnecessary legacy, compatibility, migration,
  duplicate-surface, or transitional code unless a task or repository boundary
  explicitly requires it.
- When the touched area contains obvious local maintainability, design, or
  performance problems, include safe cleanup in the same change.
- If worthwhile adjacent cleanup cannot be completed safely, record the blocker
  and exact next action in `Documentation.md`.
- Use `ai/policies/<policy-id>/Policy.md` when a repository wants stricter or
  machine-checkable extensions of this default stance.

## Standard Flow

Create a task scaffold:

```bash
__RUNTIME_COMMAND_PREFIX__/init-long-horizon-task.sh \
  --task example-task \
  --title "Example Task" \
  --spec ai/plans/example-task.md
```

Create an isolated worktree and launch the task:

```bash
__RUNTIME_COMMAND_PREFIX__/start-long-horizon-worktree.sh --task example-task
```

Run or resume a task in the current checkout:

```bash
__RUNTIME_COMMAND_PREFIX__/run-long-horizon.sh --task example-task
```

Run contract-relevant validation through the wrapper:

```bash
__RUNTIME_COMMAND_PREFIX__/run-task-command.sh \
  --task example-task \
  --validation-id repo-verify \
  -- make test
```

Verify closeout explicitly:

```bash
python3 __RUNTIME_COMMAND_PREFIX__/check-contract.py --task example-task --pretty
```

## Validation Rules

- Prefer targeted commands while working through a milestone.
- Use the repository's normal full verification gate before closeout.
- Record exact validation commands in `Documentation.md`.
- Record validation anomalies separately from command history, including
  symptom, evidence, root cause, and repair.
- Do not dismiss validation failures as unrelated without root-cause evidence.
- Do not run concurrent workspace validation commands in the same checkout
  unless they are explicitly serialized.
