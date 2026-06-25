# Codex DDD Skills

<p align="center">
  <img src="./.github/assets/banner.webp" alt="Codex DDD Skills banner">
</p>

<p align="center">
  <a href="https://ghost-who-codes.blog/open-source/codex-ddd-skills/">Project page on Ghost Who Codes</a>
</p>

Codex skills for maintaining software repositories with shared domain language,
durable architectural decisions, issue-tracker handoff, tight feedback loops,
and regular architecture improvement.

This repository combines Codex-oriented adaptations of selected MIT-licensed
skill material, original skills and scripts, and later repository-specific
contributions including the CodexLHT and CodexLHP workflow code. It preserves
license notices and attribution for upstream sources, including Matt Pocock's
[`mattpocock/skills`](https://github.com/mattpocock/skills), and licenses this
repository under the MIT License; see [`LICENSE`](./LICENSE) and
[`NOTICE.md`](./NOTICE.md).

## What Is Included

This fork keeps the DDD/project-maintenance workflow and removes the imported
personal, deprecated, draft, and unrelated utility skills.

### Engineering

- **[setup-project-context](./skills/setup-project-context/SKILL.md)** — scaffold per-repo agent context in `AGENTS.md` and `docs/agents/`.
- **[prototype](./skills/prototype/SKILL.md)** — build disposable project-local prototypes to test architecture, logic, state, or UI ideas before productionizing them.
- **[grill-with-docs](./skills/grill-with-docs/SKILL.md)** — stress-test a plan against the codebase, sharpen domain language, and update `CONTEXT.md`/ADRs.
- **[to-prd](./skills/to-prd/SKILL.md)** — synthesize the current conversation into a PRD and publish it to the issue tracker.
- **[to-issues](./skills/to-issues/SKILL.md)** — break a plan or PRD into independently-grabbable vertical-slice issues.
- **[triage](./skills/triage/SKILL.md)** — move issues through a small triage-role state machine and produce agent briefs.
- **[frontend-design](./skills/frontend-design/SKILL.md)** — create or refine production-quality web UI with deliberate visual direction, accessibility, responsive layout, and browser verification.
- **[tdd](./skills/tdd/SKILL.md)** — build or fix behavior with a red-green-refactor loop.
- **[diagnose](./skills/diagnose/SKILL.md)** — debug hard failures by first building a deterministic feedback loop.
- **[rust](./skills/rust/SKILL.md)** — apply Rust-specific engineering guidance for idiomatic APIs, ownership, async code, tests, performance, and project structure.
- **[java](./skills/java/SKILL.md)** — apply Java/JVM-specific engineering guidance for idiomatic APIs, Maven/Gradle builds, tests, concurrency, performance, and code review.
- **[zoom-out](./skills/zoom-out/SKILL.md)** — ask for a higher-level map of an unfamiliar code area.
- **[improve-codebase-architecture](./skills/improve-codebase-architecture/SKILL.md)** — find deepening opportunities informed by domain language and ADRs.
- **[codex-lhp](./skills/codex-lhp/SKILL.md)** — create and maintain Codex Long-Horizon Program plans that orchestrate multiple CodexLHT tasks from repository specs.
- **[codex-lht](./skills/codex-lht/SKILL.md)** — install and operate a repo-local Codex Long-Horizon Task workflow for contract-gated, resumable work.

### Productivity

- **[handoff](./skills/handoff/SKILL.md)** — compact the current session into a temporary handoff document.
- **[grill-me](./skills/grill-me/SKILL.md)** — run a codebase-aware design discussion without automatically writing docs.
- **[stop-slop](./skills/stop-slop/SKILL.md)** — remove predictable AI writing patterns from documentation, comments, commit messages, PR descriptions, and user-facing copy.
- **[write-a-skill](./skills/write-a-skill/SKILL.md)** — create or update concise Codex skills with progressive disclosure.

## Suggested Flow

For the full project lifecycle workflow, see [`USAGE.md`](./USAGE.md).

1. Run `setup-project-context` once in a target repository.
2. Use `grill-me` for exploratory design discussion, or `grill-with-docs` when
   the discussion should also update domain language or ADRs.
3. Use `prototype` when an idea needs a fast project-local experiment before it
   is built into production code.
4. Use `to-prd` and `to-issues` to turn settled intent into issue-tracker work.
5. Use `tdd` or `diagnose` while implementing the work.
6. Use `improve-codebase-architecture` periodically to identify module
   deepening opportunities.

## Repository Conventions

For this repository, [`AGENTS.md`](./AGENTS.md) is the contributor guide. It
documents the skill layout, naming rules, validation commands, and PR
expectations for changing this bundle.

The engineering skills expect target repositories to use:

- `AGENTS.md` for agent-facing repo instructions.
- `docs/agents/` for per-repo skill configuration, including issue tracker,
  triage labels, and domain-doc layout.
- `CONTEXT.md` for domain language, or `CONTEXT-MAP.md` for multi-context repos.
- `docs/adr/` for architectural decision records.

If a target repository does not have these files yet, `setup-project-context`
creates the `AGENTS.md` block and `docs/agents/` files. The domain glossary and
ADRs are created lazily by `grill-with-docs` when real terms or decisions are
resolved.

Do not treat this repo's root `AGENTS.md` as a template for target repositories.
Target repos should use `setup-project-context`, then edit their generated
`docs/agents/*.md` files as their issue tracker or domain-doc layout changes.

## Language Skills

Language-specific skills, such as `rust` and `java`, must be both installed and
made visible to the target project.

For Rust projects:

1. Make this skill bundle available to Codex, for example with
   `scripts/link-skills.sh` during local development.
2. Run `setup-project-context` in the target repository.
3. Add a language-skills note to the target repo's `AGENTS.md` so Codex uses
   `rust` whenever it touches `.rs` files, `Cargo.toml`, Cargo workspaces,
   async Rust, Rust tests, or Rust performance-sensitive code.

See [`USAGE.md`](./USAGE.md#rust-projects) for the recommended `AGENTS.md`
snippet.

For Java projects:

1. Make this skill bundle available to Codex, for example with
   `scripts/link-skills.sh` during local development.
2. Run `setup-project-context` in the target repository.
3. Add a language-skills note to the target repo's `AGENTS.md` so Codex uses
   `java` whenever it touches `.java` files, Maven or Gradle build files, JVM
   tests, concurrency, or JVM performance-sensitive code.

See [`USAGE.md`](./USAGE.md#java-projects) for the recommended `AGENTS.md`
snippet.

## Local Helpers

- `scripts/list-skills.sh` lists all retained skills.
- `scripts/link-skills.sh` symlinks retained skills into
  `${CODEX_HOME:-$HOME/.codex}/skills` for local development.
- `scripts/validate-plugin.sh` checks the plugin manifest, skill metadata,
  README coverage, removed upstream artifacts, and licensing files.
- `scripts/integration-test.sh` runs the deterministic validation suite in
  Docker. Set `RUN_LIVE_CODEX_TESTS=1` to also exercise
  `setup-project-context` through the local Codex CLI in a throwaway repo.
  The live test requires usable local Codex authentication.
