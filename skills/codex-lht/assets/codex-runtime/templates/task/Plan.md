# __TASK_TITLE__ Plan

Date: __DATE__

## Global Rules

- Treat this plan as advisory execution scaffolding, not lifecycle authority.
- Complete workstreams in order unless `Documentation.md` records a justified resequencing.
- Keep each workstream narrow enough to implement, validate, and document in one focused loop.
- Plan workstreams so the touched area is improved, not merely changed.
- Include safe adjacent cleanup or performance repair when the touched area
  contains obvious local design, maintainability, or efficiency problems.
- Do not preserve unnecessary legacy, compatibility, migration,
  duplicate-surface, or transitional code unless explicitly required.
- Run the listed validation commands before marking a workstream complete.
- If validation fails, fix the issue before continuing.
- Validation anomalies require root-cause debugging; do not dismiss them as
  "intermittent", "unrelated", or "just a flake" without evidence.
- Update `Documentation.md` after each workstream.
- If worthwhile adjacent cleanup cannot be completed safely in the current
  workstream, record the blocker and exact next action in `Documentation.md`.
- Keep product/runtime code independent from `__RUNTIME_ROOT_REF__/**` and `__TASK_ROOT_REL__/**`.
- Treat `Contract.md` as the machine-checkable closeout boundary.
- Use `__RUNTIME_COMMAND_PREFIX__/run-task-command.sh` for contract-relevant validation.

## Workstream 1: Replace This

Objective:
Describe one workstream-sized deliverable.

Primary areas:
- list touched modules or files

Acceptance criteria:
- add explicit acceptance criteria
- include any safe adjacent cleanup or performance improvements needed to leave
  the touched area better than before

Validation:
- add the project-specific validation command for this workstream
- include restart, rerun, or idempotency checks when the workstream changes
  durable state, recovery behavior, locking, or wrapper lifecycle behavior

Decision notes:
- add important scope notes

## Closeout Workstream

Objective:
Prove the task is merge-ready after implementation is complete.

Acceptance criteria:
- final required project validation passes
- a merge-readiness self-review finds no material bugs, regressions, lifecycle
  mistakes, or validation gaps
- no obvious touched-area maintainability, architecture, or performance issues
  were left behind without documented blocker or accepted residual risk
- any residual risk is documented explicitly in `Documentation.md`
- `Closeout.md` satisfies `Contract.md`

Validation:
- add the project-specific closeout validation command

Decision notes:
- if a closeout review finds a material issue, reopen the task and fix it
  before completion
