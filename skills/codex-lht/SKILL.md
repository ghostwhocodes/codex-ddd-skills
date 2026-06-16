---
name: codex-lht
description: Install and operate a repo-local Codex Long-Horizon Task workflow for contract-gated, resumable work across Codex runs and worktrees. Use when the user asks to create, initialize, resume, validate, close out, reopen, or automate a long-running Codex task; asks about CodexLHT; wants durable task documents under ai/tasks; or needs a repository-local wrapper for validation evidence, closeout contracts, and review-driven repair loops.
---

# CodexLHT

Use this skill to install or operate a repository-local Codex Long-Horizon Task
runtime. CodexLHT keeps long-running work durable through task documents,
machine-readable contracts, validation event logs, and closeout checks.

## Resource Map

- Use `scripts/install-runtime.sh` to copy the bundled runtime into a target
  repository.
- Use `scripts/validate-task.sh` to run the bundled contract checker for a task.
- Use `assets/codex-runtime/` as the source runtime. Do not load these files
  unless installing, patching, or debugging the runtime.
- Read `references/workflow.md` when operating an installed CodexLHT task.
- Read `references/integration.md` when installing CodexLHT into a repository,
  converting a repo-local helper into a skill, or choosing a validation example.

## Install Runtime

When a repository does not already have CodexLHT installed, install it with:

```bash
<skill-dir>/scripts/install-runtime.sh --repo <repo-root>
```

The installer copies the bundled runtime to `<repo-root>/codex`. It refuses to
overwrite changed files unless `--force` is supplied.

After installation, confirm the repository has a boundary prompt file matching
`CODEXLHT_BOUNDARY_PROMPT`. The generic runtime defaults to `AGENTS.md`.
Repository-specific setup belongs in `AGENTS.md`, task docs, policy files, or a
file sourced through `CODEXLHT_ENV_FILE`.

## Standard Task Flow

Create a scaffold:

```bash
./codex/init-long-horizon-task.sh \
  --task <task-slug> \
  --title "<Task Title>" \
  --spec <path-or-short-description>
```

Launch in a worktree:

```bash
./codex/start-long-horizon-worktree.sh --task <task-slug>
```

Run or resume in the current checkout:

```bash
./codex/run-long-horizon.sh --task <task-slug>
```

Record validation evidence:

```bash
./codex/run-task-command.sh \
  --task <task-slug> \
  --validation-id <validation-id> \
  -- <project-validation-command>
```

Check contract satisfaction:

```bash
python3 ./codex/check-contract.py --task <task-slug> --pretty
```

## Operating Rules

- Treat `Prompt.md` as the task spec and `Contract.md` as the completion
  boundary.
- Treat `Plan.md` as advisory. Completion requires the machine contract and
  closeout evidence to agree.
- The generic runtime defaults to an improvement stance: leave touched code
  better than you found it, avoid unnecessary legacy or compatibility code,
  and include safe adjacent maintainability or performance cleanup in the same
  run when warranted.
- Keep validation IDs stable once a task is in flight.
- Run contract-relevant validations through `run-task-command.sh` so
  `events.jsonl` records durable evidence.
- Keep repository-specific policy outside the generic runtime. Put reusable
  policies under `ai/policies/<policy-id>/Policy.md` and list them in
  `Contract.md`.
- Do not make product/runtime code depend on `codex/`, `ai/tasks/`, or
  `ai/policies/`.

## Reopen After Review

When a completed or handed-off task needs repair after human review:

1. Add a repair milestone to `Plan.md`.
2. Write `ReviewResume.md` with the review findings and repair guidance.
3. Append a reopen entry to `Documentation.md`.
4. Mark affected `Closeout.md` entries as `pending`.
5. Run `python3 ./codex/sync-task-closeout.py --task <task-slug>`.
6. Confirm `python3 ./codex/check-contract.py --task <task-slug> --pretty`
   fails for the intentionally reopened task.
7. Resume with `./codex/run-long-horizon.sh --task <task-slug>`.
