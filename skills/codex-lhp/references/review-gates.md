# CodexLHP Review Gates

Use this reference when deciding whether an LHT-complete milestone is
program-accepted.

## Required Gate Chain

Before `accepted`, require evidence for:

1. LHT implementation validation: task contract passes, closeout is synced, and
   required validations are recorded.
2. AI merge-readiness review: no blocking bugs, regressions, task isolation
   errors, or validation gaps.
3. AI spec-conformance review: implementation satisfies the controlling spec
   cluster and does not overclaim unrelated requirements.
4. AI architecture review: result fits the intended module boundaries and does
   not make downstream work harder.
5. Human review or explicit human waiver: accept, request remediation, narrow
   scope, split the milestone, or revise the graph.

## Acceptance Rules

- Do not use LHT contract satisfaction as program acceptance.
- Do not let `implementation-complete` unblock downstream milestones.
- Move to `remediation` when a review gate finds a blocking issue.
- Move to `accepted` only after all required gates pass or are explicitly
  waived with a human decision recorded in `State.md` and `events.jsonl`.
- Move to `completed` when accepted work is archived or otherwise no longer
  active in the program queue.

## Review Questions

Spec conformance:

- Which spec requirements does the milestone claim?
- Which requirements are intentionally left for later milestones?
- Does the completed LHT overclaim completion of blocked or downstream areas?

Architecture:

- Did the LHT create the intended substrate for dependent milestones?
- Are dependencies real implementation facts or just planned abstractions?
- Did it introduce coupling that makes the next milestone ambiguous?

Program state:

- Are blocked reasons concrete?
- Are downstream unlocks tied only to accepted milestones?
- Is the next runnable milestone unambiguous?
