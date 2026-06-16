# CodexLHT Architecture Handoff

Use this reference when a selected deepening candidate should become a durable
long-horizon task, implementation prompt, remediation prompt, or review handoff.

## Relationship

`improve-codebase-architecture` owns the architecture analysis:

- selected candidate and why it matters
- agreed seam and interface direction
- behavior that must move behind the seam
- dependency direction and adapter expectations
- rejected shortcuts and why they are unsafe
- validation and review obligations

CodexLHT owns execution mechanics inside the target repository:

- task scaffolding under `ai/tasks/<task-slug>/`
- repo-local scripts under `codex/`
- contract checking, validation events, closeout sync, and review loops

The interface between them is a source artifact under
`ai/analysis/rearchitect/`. Treat that artifact as the stable spec input for
CodexLHT, not as a replacement for CodexLHT task files.

## Discovery

From the target repository root, check for a repo-local runtime:

```bash
test -x ./codex/init-long-horizon-task.sh &&
test -x ./codex/run-long-horizon.sh &&
test -f ./codex/check-contract.py
```

If present, use those repo-local scripts. If absent, write the analysis handoff
and any nearest project-native handoff artifacts the user asked for, such as an
implementation prompt, runbook, issue draft, or remediation prompt. Tell the
user that only CodexLHT-specific scaffolding and execution must wait until
CodexLHT is installed into that repository.

If a global `codex-lht` skill exists, it may help install or operate the
runtime, but this skill must not depend on that global skill being available.
The target repo's `codex/` directory is the source of truth once installed.

## Analysis Artifact

Create `ai/analysis/rearchitect/` if needed. Write one stable Markdown file,
for example:

```text
ai/analysis/rearchitect/<task-slug>-architecture-handoff.md
```

The handoff must include:

1. Selected candidate: the chosen deepening opportunity and the user decision
   that selected it.
2. Current friction: concrete files, call sites, tests, and failure modes that
   make the current module shallow or hard to change.
3. Target seam: the module/interface that should own the behavior, with domain
   vocabulary from `CONTEXT.md` and architecture vocabulary from `LANGUAGE.md`.
4. Behavior movement: what behavior moves behind the seam, what stays outside,
   and what gets deleted.
5. Dependency rules: allowed dependencies, forbidden reverse dependencies, and
   any adapter expectations.
6. Rejected shortcuts: pass-through modules, private-helper extractions,
   compatibility shims, release-history prose, or preservation work the user
   explicitly rejected.
7. Validation plan: product-level behavior tests, seam-level tests, migration
   checks, and any full-repo validation gate.
8. Review fail conditions: explicit conditions that should block closeout.
9. Open decisions: only unresolved choices that genuinely block execution.

Every substantive requirement in the handoff or task must be expressed twice:

- **Coding goal** — what the coding agent must build, preserve, move, delete,
  or validate.
- **Review rule** — what the review agent must block if the coding agent
  shortcuts, drifts, preserves abandoned behavior, weakens the seam, or claims
  completion without evidence.

The review rules are fail conditions, not explanatory prose.

Do not mark the handoff ready if it only says "refactor X" or "extract Y".
It must say what behavior moves, what interface carries it, and what a reviewer
must reject.

## Task Scaffolding

When CodexLHT is installed, initialize the task from the analysis artifact:

```bash
./codex/init-long-horizon-task.sh \
  --task <task-slug> \
  --title "<task title>" \
  --spec ai/analysis/rearchitect/<task-slug>-architecture-handoff.md
```

Then edit the generated task files. Preserve the repo-local CodexLHT template
shape; do not replace it with copied instructions from this skill.

`Prompt.md` should contain:

- objective in product/domain terms
- concrete scope and out-of-scope sections
- hard constraints from the handoff
- deliverables tied to the target seam
- validation expectations
- the analysis artifact as a source reference

`Contract.md` should contain stable IDs:

- requirement IDs for each behavior movement or deletion obligation
- validation IDs for each command or durable evidence item
- review IDs for architecture-specific review gates
- policy IDs only for reusable repo-local policy files under `ai/policies/`

`Plan.md` and `Implement.md` should make the coding path resumable after
context compaction, but must not become completion authority. Completion is
owned by `Contract.md`, `Closeout.md`, and repo-local contract checking.

`Documentation.md` should record selected decisions, known risks, validation
history, and the next action.

`Closeout.md` should start with one pending evidence row for each requirement
and review ID. Keep it aligned with `Contract.md`.

## Review Fail Conditions

For architecture-deepening tasks, include review rules that block:

- a pass-through module when the task requires a deep module
- leaving the hard behavior in the old caller under a new private helper name
- dependency drift across the agreed seam
- tests that only prove private helpers while missing product-level behavior
- keeping abandoned compatibility, migration, or release-history work unless the
  user explicitly authorized it
- domain-specific shortcuts that contradict the selected candidate or project
  spec
- broad rewrites outside the selected candidate without a recorded reason
- claiming completion without contract-relevant validation evidence

Write review rules as fail conditions, not explanatory prose. A review agent
should be able to reject the work directly from them.

## Closeout

Before handoff:

- run contract-relevant validations through the repo-local CodexLHT wrapper when
  available, for example `./codex/run-task-command.sh`
- update `Documentation.md` with what changed and which validations ran
- update `Closeout.md` evidence for every requirement and review ID
- run the repo-local contract check, usually
  `python3 ./codex/check-contract.py --task <task-slug> --pretty`
- record skipped validation only with a concrete blocker and residual risk

Do not hand-edit `events.jsonl` to fake completion. The repo-local wrapper owns
event recording.
