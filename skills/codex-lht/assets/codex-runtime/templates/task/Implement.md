# __TASK_TITLE__ Implement Runbook

Date: __DATE__

## Purpose

This file tells Codex how to operate during internal long-horizon runs for `__TASK_SLUG__`.

## Source Of Truth

- `Prompt.md` defines the target.
- `Contract.md` defines the machine-checkable closeout boundary.
- `Plan.md` defines the advisory workstream sequence and validation requirements.
- `Documentation.md` is the live execution log.
- `Closeout.md` is the structured final evidence the wrapper syncs into `events.jsonl`.
- `__BOUNDARY_PROMPT__` defines the repository context and boundaries.

## Operating Rules

- Start by reading `__BOUNDARY_PROMPT__` and the task-local run files.
- Identify the next incomplete workstream from `Documentation.md` and `Plan.md`.
- Complete one active workstream at a time.
- Treat every change as an opportunity to improve the touched area; leave it
  clearer, simpler, and more maintainable than you found it.
- Keep edits scoped to the active workstream, but expand the change when safe
  adjacent cleanup or performance repair is needed to avoid reinforcing poor
  structure.
- Do not preserve or introduce legacy, compatibility, migration,
  duplicate-surface, or transitional code unless the task or repository
  instructions explicitly require it.
- When the touched area contains obvious local design, maintainability,
  duplication, coupling, naming, error-handling, or performance problems,
  improve them as part of the same change when safe to do so.
- Do not treat safe local cleanup in code you are already changing as out of
  scope; if worthwhile cleanup cannot be completed safely, record the blocker
  and exact next action in `Documentation.md`.
- Follow repository-specific policies from `Contract.md`, `ai/policies/`, and
  the configured boundary prompt.
- Run the workstream validation commands before considering the workstream complete.
- Run contract-relevant validation commands through `__RUNTIME_COMMAND_PREFIX__/run-task-command.sh`
  so `events.jsonl` captures deterministic validation facts.
- Keep `Closeout.md` current so wrapper-owned closeout facts can be synced
  before final contract verification.
- Do not run wrapper-owned closeout commands such as
  `sync-task-closeout.py` or `check-contract.py` from inside a managed
  wrapper run; prepare `Closeout.md` and let the wrapper finalizer run them.
- If validation fails or a run is interrupted, inspect for stale validation or
  wrapper processes, leaked child processes, same-checkout overlap, and lock
  contention before rerunning anything.
- Debug validation anomalies to root cause; do not dismiss them as
  "intermittent", "unrelated", or "just a flake" without evidence.
- If validation fails, fix the failure immediately and rerun validation.
- Update `Documentation.md` after each workstream.
- Keep `Contract.md` and `Closeout.md` aligned with the actual completion state.
- Never solve a workflow problem by making product/runtime code depend on
  `__RUNTIME_ROOT_REF__/**` or `__TASK_ROOT_REL__/**`.
- Do not stop merely because one internal workstream is complete; continue until the task is complete unless truly blocked.

## Execution Loop

1. Read the active workstream objective, acceptance criteria, validation commands, and decision notes.
2. Inspect the relevant code and existing implementation before changing anything.
3. Implement what is needed to satisfy the workstream and any safe, tightly
   coupled adjacent cleanup or performance changes required to leave the
   touched area in a better state.
4. Run the listed validation commands.
   For contract-relevant checks, use `__RUNTIME_COMMAND_PREFIX__/run-task-command.sh`.
5. If validation fails or a run is interrupted, inspect for stale runners,
   leaked wrappers, same-checkout overlap, and lock contention before rerunning.
6. Repair any failures until validation passes, and record anomaly, evidence,
   root cause, and repair in `Documentation.md`.
7. Update `Documentation.md`, `Contract.md`, and `Closeout.md` as needed.
8. Before marking the task complete, run a merge-readiness self-review using
   the review prompt and reopen the task immediately if it finds a material
   issue.
9. Before marking the task complete, update `Closeout.md` with the evidence the
   wrapper finalizer needs for closeout sync and final contract verification.
10. Before marking the task complete, confirm the work satisfies `Contract.md`;
    if not, keep going even if the planned workstreams are exhausted.
11. Move to the next useful workstream.

## Stop Conditions

Stop only if:

- the environment cannot run required validations
- the repo is missing information needed to continue safely
- a product decision is required that is not covered by `Prompt.md`
- existing conflicting local changes make safe continuation unclear

When stopped:

- record the blocker in `Documentation.md`
- record the last successful workstream
- record the next exact action required to resume

## Completion Rule

- For runtime-behavior or code-change tasks, do not treat the task as done
  until the declared validation evidence is recorded and `Closeout.md` is
  ready for wrapper-owned closeout verification.
