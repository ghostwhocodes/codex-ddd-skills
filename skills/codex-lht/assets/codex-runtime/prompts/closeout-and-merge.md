Prepare the current internal CodexLHT task branch for merge.

Read:
- `<boundary-prompt>`
- `<runtime-root-rel>/LONG_HORIZON.md`
- `<task-root-rel>/<task-slug>/Prompt.md`
- `<task-root-rel>/<task-slug>/Contract.md`
- `<task-root-rel>/<task-slug>/Plan.md`
- `<task-root-rel>/<task-slug>/Documentation.md`
- `<task-root-rel>/<task-slug>/Closeout.md`

Then:

1. confirm the task is actually complete according to `Contract.md`, `Plan.md`, and `Documentation.md`
2. confirm `Closeout.md` is consistent with the intended final state
3. review the current diff for merge blockers
4. summarize any remaining risks
5. if the branch is merge-ready, provide the exact Git steps to commit, merge into `master`, and clean up the worktree

Do not merge automatically in this step unless explicitly asked.
