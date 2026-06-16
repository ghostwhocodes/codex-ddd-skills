# __TASK_TITLE__ Prompt

Date: __DATE__

## Objective

Describe the target outcome for `__TASK_SLUG__`.

## Scope

- fill in task scope

## Out Of Scope

- fill in explicit non-goals

## Hard Constraints

- follow repository-specific boundaries from `__BOUNDARY_PROMPT__` and any
  policy files listed in `Contract.md`
- keep product/runtime code independent from `__RUNTIME_ROOT_REF__/**` and
  `__TASK_ROOT_REL__/**`
- keep changes scoped to the task
- leave touched code better than you found it
- do not preserve or introduce unnecessary legacy, compatibility, migration,
  duplicate-surface, or transitional code unless explicitly required
- improve obvious adjacent maintainability, design, and performance issues in
  the touched area when safe to do so
- if worthwhile adjacent cleanup cannot be completed safely, document the
  blocker and exact next action in `Documentation.md`
- treat internal workstreams as advisory decomposition, not approval checkpoints
- continue until the requested outcome is complete unless truly blocked
- validate each completed workstream
- record contract-relevant validation through `__RUNTIME_COMMAND_PREFIX__/run-task-command.sh`
- if the task changes durable state, restart/resume behavior, replay, recovery,
  or locking behavior, define restart, rerun, replay, and idempotency
  invariants explicitly
- update `Documentation.md` throughout the run

## Deliverables

- fill in concrete deliverables

## Validation Expectations

- fill in workstream-level and closeout validation commands
- include restart/resume/retry or stale-state validation when the task changes
  durable state, recovery, locking, or wrapper lifecycle behavior

## Done When

- fill in exact exit criteria
- keep `Contract.md` and `Closeout.md` aligned with the real completion boundary

## Source References

- __SPEC_REFERENCE__
