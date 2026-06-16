# __TASK_TITLE__ Closeout

Date: __DATE__

## Purpose

This file is the structured closeout input that the internal helper turns into
requirement, review, and handoff events before final contract verification.

## Machine Closeout

```json
{
  "schema_version": 1,
  "requirements": [
    {
      "requirement_id": "REQ-1",
      "status": "pending",
      "summary": "Replace with concise requirement evidence."
    }
  ],
  "reviews": [
    {
      "review_id": "merge_readiness",
      "status": "pending",
      "summary": "Replace with the final merge-readiness result."
    }
  ],
  "handoff_target": "local_complete",
  "summary": "Replace with a concise closeout summary."
}
```

- Keep the IDs in sync with `Contract.md`.
- Allowed requirement statuses: `pending`, `satisfied`, `unsatisfied`.
- Allowed review statuses: `pending`, `passed`, `blocking`.

## Requirement Evidence

- Replace with brief evidence for each requirement ID.
- Include explicit policy evidence for every policy-derived requirement listed
  in `Contract.md`.

## Review Summary

<!-- WRAPPER_CLOSEOUT_REVIEW_SUMMARY:BEGIN -->
- Wrapper-owned review state goes here.
<!-- WRAPPER_CLOSEOUT_REVIEW_SUMMARY:END -->
<!-- Keep volatile latest-wrapper-review timestamps inside the WRAPPER_* blocks.
     Surrounding prose should record only stable evidence or invariants. -->

- Add any stable review evidence or residual-risk notes below the wrapper-owned
  state block.

## Handoff

<!-- WRAPPER_CLOSEOUT_HANDOFF:BEGIN -->
- Wrapper-owned handoff state goes here.
<!-- WRAPPER_CLOSEOUT_HANDOFF:END -->

- Add any stable operator notes tied to the handoff target below the
  wrapper-owned state block.
