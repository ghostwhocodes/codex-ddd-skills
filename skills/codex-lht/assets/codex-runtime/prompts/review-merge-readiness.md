Review the current internal CodexLHT task branch for merge readiness.

Read:
- `<boundary-prompt>`
- `<runtime-root-rel>/LONG_HORIZON.md`
- `<task-root-rel>/<task-slug>/Prompt.md`
- `<task-root-rel>/<task-slug>/Contract.md`
- `<task-root-rel>/<task-slug>/Plan.md`
- `<task-root-rel>/<task-slug>/Documentation.md`
- `<task-root-rel>/<task-slug>/Closeout.md`

Then inspect the current diff or branch changes with a code-review mindset.

Focus on:
- bugs
- behavioral regressions
- missing validation
- unmet contract obligations or invalid claimed handoff target
- missing or contradictory `events.jsonl` evidence, or a failing
  `<runtime-command-prefix>/check-contract.py` result
- boundary violations where product/runtime code depends on `<runtime-root-rel>/**`,
  `<task-root-rel>/**`, or task-local workflow state
- contract or architecture-boundary risks
- unnecessary legacy, compatibility, migration, duplicate-surface, or
  transitional code that was preserved or introduced without explicit
  authorization
- cleanup, locking, or lifecycle mistakes
- obvious local maintainability, architecture, or performance issues left
  behind in code the task touched without a documented blocker
- gaps between the implemented work and the documented workstream history
- validation anomalies that were dismissed without root-cause evidence
- restart, replay, rerun, idempotency, and durable-state risks when the task
  changes persisted state or recovery behavior

Policy hard fail:

- Immediately report a material finding for any violation of repository-local
  policies listed in `Contract.md` or stored under `ai/policies/`.
- Immediately report a material finding if the change preserves or introduces
  unnecessary legacy, compatibility, migration, duplicate-surface, or
  transitional code without explicit task or repository authorization.
- Immediately report a material finding if the task touched an area with
  obvious local maintainability, design, or performance issues that could have
  been improved safely and left them unaddressed without a documented blocker.
- "Out of scope" is not sufficient justification for leaving safe local cleanup
  undone in code the task already changed.
- Immediately report a material finding for any product/runtime dependency on
  CodexLHT task files, wrapper state, or generated review context unless the
  task explicitly authorizes that dependency.
- The correct review recommendation is removal unless the task includes an
  explicit user instruction authorizing the exception.

Wrapper review phase state:

- This review runs before the wrapper records a clean `wrapper_review`
  `success`, clears `ReviewResume.md`, runs `sync-task-closeout.py`, and runs
  the final `check-contract.py` verification.
- Do not treat expected pre-success wrapper state as a material finding by
  itself. Expected pre-success state includes a latest wrapper review status of
  `findings`, active `ReviewResume.md`, `Closeout.md` machine
  `merge_readiness` still marked `pending`, missing synced `REQ-*` or handoff
  events, and a failing `check-contract.py` result when those failures are
  caused only by the fact that this clean review has not succeeded and synced
  closeout yet.
- Still report a material finding when those symptoms are tied to a real
  closeout defect: unaddressed `ReviewResume.md` content, contradictory
  closeout claims, stale or missing validation after current changes, missing
  product evidence, a code regression, a boundary violation, or instructions
  that require manual closeout outside the wrapper.
- If expected pre-success wrapper state is the only remaining concern, return
  `status: "clean"` and list that state only as residual risk or expected
  wrapper finalization work. That lets the wrapper record the authoritative
  success, clear stale review context, sync closeout, and run the strict
  contract checker in the correct order.

Findings should come first, ordered by severity with file references.
If no material findings are present, say so explicitly and list only residual risks.
If this review is being used for task closeout, any material finding blocks
completion until it is fixed or documented as an explicit residual risk
accepted by the task spec.
