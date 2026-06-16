Read:

- `<boundary-prompt>`
- `<runtime-root-rel>/LONG_HORIZON.md`
- `<task-root-rel>/<task-slug>/Prompt.md`
- `<task-root-rel>/<task-slug>/Contract.md`
- `<task-root-rel>/<task-slug>/Documentation.md`

Use:
- `Prompt.md` as the spec
- `Contract.md` as the closeout boundary
- `Documentation.md` as current state

Then rewrite `Plan.md` and, if needed, tighten `Implement.md` and `Closeout.md`
so the task is executable as an internal long-horizon Codex run.

Requirements:
- break the work into workstream-sized increments
- each workstream must be small enough to implement, validate, and document in one loop
- each workstream must include exact acceptance criteria
- each workstream must include explicit validation commands
- the plan must not claim lifecycle authority that belongs to `Contract.md`
- keep the plan compatible with this repository's real module layout, policies,
  and build commands
- shape workstreams so touched areas are left better than they were found
- plan adjacent cleanup or performance repair when the touched area contains
  obvious local design, maintainability, or efficiency problems
- do not preserve unnecessary legacy, compatibility, migration,
  duplicate-surface, or transitional code unless explicitly required by the
  spec or boundary docs
- keep product/runtime code independent from `<runtime-root-rel>/**` and `<task-root-rel>/**`
- use `<runtime-command-prefix>/run-task-command.sh --task <task-slug> --validation-id <id> -- <command>` for contract-relevant validation commands
- include a closeout workstream that runs final validation and a
  merge-readiness review before completion
- if the task changes durable state, replay, recovery, startup gates, or
  locking, include explicit restart, rerun, and idempotency expectations
- state that validation anomalies require root-cause debugging and must not be dismissed as "intermittent", "unrelated", or "just a flake" without evidence
- if worthwhile adjacent cleanup cannot be completed safely in the current
  plan, record the blocker and exact next action in `Documentation.md`
- record planning assumptions or unresolved sequencing risks in `Documentation.md`

Do not implement product code in this step unless a tiny documentation-only fix is required to make the plan coherent.
