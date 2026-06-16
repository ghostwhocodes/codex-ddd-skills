# __TASK_TITLE__ Contract

Date: __DATE__

## Completion Policy

- `Prompt.md` defines the intended outcome and hard constraints.
- `Contract.md` defines the machine-checkable boundary for when the internal
  helper may stop.
- `Plan.md` is advisory decomposition only; it is not lifecycle authority and
  it does not prove completion.
- `Documentation.md` is a human-readable execution log and evidence index; it
  is not completion authority on its own.
- `Closeout.md` is the structured closeout input the wrapper uses before final
  contract verification.

## Machine Contract

```json
{
  "schema_version": 1,
  "requirement_ids": ["REQ-1"],
  "validation_ids": ["replace-with-validation-id"],
  "review_ids": ["merge_readiness"],
  "allowed_handoff_targets": ["local_complete"],
  "policy_ids": []
}
```

- Keep these IDs stable once a task is in flight.
- `validation_ids` must match wrapper-recorded validation events in
  `events.jsonl`.
- `review_ids` must match wrapper-synced review events derived from
  `Closeout.md`.
- `policy_ids` opts the task into reusable machine-checkable policy files under
  `ai/policies/<policy-id>/Policy.md`.

## Active Policies

- Add policy IDs only for reusable repository-local policy files that actually
  apply to this task.
- Keep policy text in `ai/policies/<policy-id>/Policy.md`; do not encode
  repository-specific policy in the generic CodexLHT runtime.

## Requirement IDs

- `REQ-1`: Replace with a stable, testable requirement.

## Required Obligations

- Replace this section with flat checklist items tied to stable requirement
  IDs where useful.
- If the task changes runtime behavior, locking, prompts, or stateful helper
  logic, include explicit restart, reopen, and idempotency obligations.

## Validation Requirements

- List exact validation commands or durable evidence requirements needed before
  closeout.
- For CodexLHT helper work, include explicit helper tests when applicable.
- For repository code or runtime changes, include the project's normal full
  verification gate unless a concrete blocker is recorded explicitly.

## Review Requirements

- A merge-readiness review must report no unresolved blocking findings.
- Any residual risk accepted for closeout must be recorded explicitly in
  `Documentation.md` and referenced from the final review artifact.

## Allowed Handoff Target

- `local_complete`
