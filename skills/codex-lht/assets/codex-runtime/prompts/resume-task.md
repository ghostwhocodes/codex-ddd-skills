Resume the internal long-horizon task in `<task-root-rel>/<task-slug>/`.

Read:
- `<boundary-prompt>`
- `<runtime-root-rel>/LONG_HORIZON.md`
- `<task-root-rel>/<task-slug>/Prompt.md`
- `<task-root-rel>/<task-slug>/Contract.md`
- `<task-root-rel>/<task-slug>/Plan.md`
- `<task-root-rel>/<task-slug>/Implement.md`
- `<task-root-rel>/<task-slug>/Documentation.md`
- `<task-root-rel>/<task-slug>/Closeout.md`
- `<task-root-rel>/<task-slug>/ReviewResume.md`, if it exists

Start from the first incomplete workstream or the blocker recorded in `Documentation.md`.
If `ReviewResume.md` exists, treat it as wrapper review context for the next
repair pass. Step back before patching, identify broader patterns or missing
invariants behind the findings, and prefer upstream or test-harness fixes over
line-local patches unless the evidence proves the fix is local.
Do not restart completed workstreams unless the current repository state or failing validation proves they need rework.
Continue the task to the next meaningful stopping point, update `Documentation.md`, and keep the diff scoped to the active workstream.
Treat `Contract.md` as the closeout boundary; do not stop just because the planned workstreams appear exhausted if contract obligations remain unmet.

Validation rules:
- Never dismiss a failure as "intermittent", "unrelated", or "just a flake" without root-cause evidence.
- After any failed or interrupted validation run, inspect for stale validation
  or wrapper processes, leaked child processes, same-checkout overlap, and lock
  contention before rerunning.
- Record each validation anomaly in `Documentation.md` with symptom, evidence, root cause, and repair.
- Run contract-relevant validation commands through `<runtime-command-prefix>/run-task-command.sh --task <task-slug-shell> --validation-id <id> -- <command>`.
- Keep `Closeout.md` current so the wrapper can sync requirement, review, and handoff facts before final contract verification.

Closeout rules:
- Before writing task completion, run a merge-readiness self-review using the `review-merge-readiness` rubric.
- If that review finds a material bug, regression, lifecycle mistake, or validation gap, reopen the task immediately, fix it, rerun validation, and update `Documentation.md` before trying to complete the task again.
- Before stopping, make sure the required validation events are recorded and `Closeout.md` is ready for wrapper sync so `<runtime-command-prefix>/check-contract.py` can pass.
