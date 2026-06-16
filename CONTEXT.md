# Codex DDD Skills

A compact Codex skill set for starting and maintaining software repositories
with shared domain language, durable decisions, issue-tracker handoff,
test-first implementation, diagnosis loops, and architecture improvement.

## Language

**Agent context**:
Repo-local instructions and configuration that tell Codex how to work in a
project. This usually means an `AGENTS.md` section plus files under
`docs/agents/`.
_Avoid_: Claude config, slash-command config

**Repository guide**:
The root `AGENTS.md` in this skill bundle. It tells contributors how this
repository is organized, which validation commands to run, and how to preserve
the skill layout. It is not the same thing as generated **Agent context** in a
target repository.
_Avoid_: generated setup output, target agent config

**Issue tracker**:
The tool or convention that hosts a repo's issues: GitHub Issues, GitLab
Issues, local markdown files, or another workflow described by the user. Skills
like `to-issues`, `to-prd`, and `triage` read from and write to it.
_Avoid_: backlog manager, backlog backend

**Domain glossary**:
The `CONTEXT.md` file that defines the project's canonical domain vocabulary.
It is a glossary, not a product spec or implementation guide.
_Avoid_: context dump, project notes

**Context map**:
A root `CONTEXT-MAP.md` that points Codex to multiple domain glossaries in a
monorepo or multi-context system.

**ADR**:
An architectural decision record under `docs/adr/`, or under a context-specific
`docs/adr/` folder in a multi-context repo.

**Validation suite**:
The repository checks that keep the plugin installable and the skills
discoverable. `scripts/validate-plugin.sh` is the fast local gate;
`scripts/integration-test.sh` adds Docker-based checks; setting
`RUN_LIVE_CODEX_TESTS=1` also exercises `setup-project-context` through the
local Codex CLI.

**Triage role**:
A canonical state-machine label applied to an **Issue** during triage, such as
`needs-triage`, `needs-info`, or `ready-for-agent`. Each role maps to a real
label string in the **Issue tracker** via `docs/agents/triage-labels.md`.

## Relationships

- `setup-project-context` creates **Agent context** for a target repo.
- The **Repository guide** explains how to change this skill bundle.
- **Agent context** records the **Issue tracker**, **Triage role** mapping, and
  domain-doc layout.
- A **Domain glossary** defines canonical project terms used by engineering
  skills.
- An **ADR** records a durable architectural decision that future agents should
  respect.
- The **Validation suite** guards plugin metadata, skill metadata, README
  coverage, runtime helpers, and the optional live setup flow.

## Flagged Ambiguities

- "Context" can mean conversation history, repo instructions, or domain
  glossary. In this repo, use **Agent context** for repo instructions and
  **Domain glossary** for `CONTEXT.md`.
- `AGENTS.md` can mean this repo's **Repository guide** or generated **Agent
  context** in a target repo. Name which one you mean.
- "Ticket" and "issue" were mixed in the imported material. Use **Issue** unless
  quoting a tracker that calls the unit something else.
