# CodexLHT Workflow Reference

Use this reference when operating an installed CodexLHT runtime.

## Task Files

- `Prompt.md`: user-facing task spec and hard constraints
- `Contract.md`: machine-readable completion boundary
- `Plan.md`: advisory decomposition and milestone order
- `Implement.md`: execution runbook
- `Documentation.md`: live execution log and validation history
- `Closeout.md`: structured evidence synced into requirement, review, and
  handoff events
- `ReviewResume.md`: optional repair context generated or written after review
- `events.jsonl`: wrapper-authored event stream

## Contract Evidence

Use stable IDs:

- `requirement_ids` in `Contract.md` must appear in `Closeout.md`.
- `validation_ids` in `Contract.md` must appear as passed validation events in
  `events.jsonl`.
- `review_ids` in `Contract.md` must appear as passed review state in
  `Closeout.md` after sync.
- `policy_ids` refer to `ai/policies/<policy-id>/Policy.md`.

## Default Quality Stance

- Leave touched code better than you found it.
- Do not preserve or introduce unnecessary legacy, compatibility, migration,
  duplicate-surface, or transitional code unless explicitly required.
- Improve obvious local maintainability, design, or performance issues in the
  touched area when safe to do so.
- If worthwhile adjacent cleanup cannot be completed safely, document the
  blocker and exact next action in `Documentation.md`.
- Repository-local policies can harden or machine-check these defaults.

Record validation through:

```bash
./codex/run-task-command.sh --task <task> --validation-id <id> -- <command>
```

Then check:

```bash
python3 ./codex/check-contract.py --task <task> --pretty
```

## Review Loop

Use wrapper-owned review when the repository has a clear contract and the user
wants automated blocking review before closeout:

```bash
./codex/run-long-horizon.sh --task <task> --auto-review-loop 3
```

Use pending-closeout resume when a previous run stopped before final evidence
sync or contract verification:

```bash
./codex/run-long-horizon.sh \
  --task <task> \
  --auto-resume-pending-closeout 1
```

## Closeout Expectations

Before final handoff:

- update `Documentation.md` with what changed and which validations ran
- update `Closeout.md` machine JSON and evidence sections
- sync closeout with `sync-task-closeout.py`
- verify with `check-contract.py`
- report any skipped validation with a concrete blocker and residual risk
