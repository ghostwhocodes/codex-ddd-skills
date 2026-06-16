Read:

- `<boundary-prompt>`
- `<runtime-root-rel>/LONG_HORIZON.md`
- `<task-root-rel>/<task-slug>/Prompt.md`
- `<task-root-rel>/<task-slug>/Contract.md`
- `<task-root-rel>/<task-slug>/Plan.md`
- `<task-root-rel>/<task-slug>/Implement.md`
- `<task-root-rel>/<task-slug>/Documentation.md`
- `<task-root-rel>/<task-slug>/Closeout.md`

Treat:
- `Prompt.md` as the specification
- `Contract.md` as the completion contract and closeout boundary
- `Plan.md` as advisory execution scaffolding that may be refined as understanding improves
- `Implement.md` as the operating runbook
- `Documentation.md` as the live status log
- `Closeout.md` as the structured closeout evidence the wrapper uses before final contract verification

Keep the repository boundary hard:
- do not make product/runtime code depend on <runtime-root-rel>/** or <task-root-rel>/**
- obey repository-specific boundaries from `<boundary-prompt>`, task docs, and
  policy files

Default quality stance:
- Every change must improve the touched area, not merely preserve it.
- Do not preserve or introduce legacy, compatibility, migration,
  duplicate-surface, or transitional code unless the task or repository
  instructions explicitly require it.
- If the touched area contains obvious maintainability, design, or performance
  problems that can be improved safely as part of the work, include that
  cleanup in the same run.
- Do not use "out of scope" to avoid safe local cleanup in code you are
  already changing; if cleanup is blocked, record the blocker and exact next
  action in `Documentation.md`.

Treat internal workstreams as execution scaffolding, not human approval checkpoints.
Do not stop merely because one workstream is complete.
Complete the next useful incomplete workstream, run the listed validation commands, fix failures before continuing, update `Documentation.md`, and keep going until the whole task is complete or you hit a true blocker that cannot be resolved from the repository, tests, or available tools.

Validation rules:
- Never dismiss a failure as "intermittent", "unrelated", or "just a flake" without root-cause evidence.
- When validation fails or a run is interrupted, inspect for stale validation or
  wrapper processes, leaked child processes, same-checkout overlap, and lock
  contention before rerunning anything.
- Record each validation anomaly in `Documentation.md` with symptom, evidence, root cause, and repair.
- Run contract-relevant validation commands through `<runtime-command-prefix>/run-task-command.sh --task <task-slug-shell> --validation-id <id> -- <command>`.
- Keep `Closeout.md` current so the wrapper can sync requirement, review, and handoff facts before final contract verification.

Closeout rules:
- Before recording task completion, run a merge-readiness self-review using the review-merge-readiness rubric.
- If that self-review finds a material bug, regression, lifecycle mistake, or validation gap, reopen the task immediately, fix it, rerun validation, and update `Documentation.md` before attempting completion again.
- Before stopping, make sure the required validation, requirement, review, and handoff events are recorded so `<runtime-command-prefix>/check-contract.py` can pass.
