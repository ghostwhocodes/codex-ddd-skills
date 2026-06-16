# CodexLHP Workflow

Use this reference when creating or maintaining `ai/programs/<program>/`.

## Program File Roles

- `Program.md`: objective, scope, authority order, policy list, and program
  completion definition
- `SpecBreakdown.md`: requirement clusters extracted from `ai/specs/**`
- `Milestones.md`: large LHT-sized milestones with task slugs and acceptance
  intent
- `DependencyGraph.md`: prerequisites, blockers, unlock rules, and sequencing
  notes
- `ReviewGates.md`: required review chain before program acceptance
- `State.md`: current milestone state and next-action decisions
- `events.jsonl`: append-only program decisions and state transitions

## Spec Breakdown

Read the controlling spec bundle first. Extract requirements into clusters that
can become meaningful LHT milestones. Avoid tiny tickets; an LHP milestone
should be large enough to produce a coherent reviewed layer, but narrow enough
to validate independently.

For each cluster, record:

- source spec paths
- requirement summary
- implied architecture boundary
- dependencies
- validation expectations
- risks or unclear spec points

## Milestone Planning

Each milestone should include:

- stable `milestone_id`
- proposed or actual LHT `task_slug`
- state
- objective
- scope and explicit non-goals
- upstream dependencies
- downstream unlocks
- acceptance gates

Do not mark a milestone `ready` if its accepted dependencies are missing. Mark
it `blocked` instead and state the precise blocked reason.

## Selecting Next Work

Choose the next LHT by this order:

1. Active remediation required by program review.
2. Ready milestone with all accepted dependencies satisfied.
3. Blocked milestone that needs human narrowing or graph revision.
4. Program graph/spec breakdown update if no milestone is safely runnable.

Do not launch unrelated LHTs in the same checkout and do not review one task as
though it completed another milestone.

## Event Logging

Append JSON lines to `events.jsonl` for program decisions:

```json
{"schema_version":1,"event":"milestone_state_changed","milestone_id":"example","from":"ready","to":"active","reason":"Started LHT task example-task.","ts":"2026-06-15T00:00:00Z"}
```

Useful events:

- `program_initialized`
- `spec_breakdown_updated`
- `milestone_added`
- `milestone_state_changed`
- `dependency_added`
- `dependency_unblocked`
- `review_gate_passed`
- `review_gate_blocked`
- `human_decision_recorded`
