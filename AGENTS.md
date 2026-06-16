# Repository Guidelines

## Project Structure & Module Organization

This repository is a Codex plugin and skill bundle. Skill sources live under
`skills/<skill-name>/`; each skill has a `SKILL.md` and should include
`agents/openai.yaml`. Longer instructions belong in per-skill `references/`,
`scripts/`, or `assets/` directories when needed. Plugin metadata is in
`.codex-plugin/plugin.json`. Validation and local helper scripts live in
`scripts/`, integration fixtures live in `docker/integration/`, and executable
tests live in `tests/`.

## Build, Test, and Development Commands

- `scripts/list-skills.sh` lists all skill entry points in deterministic order.
- `scripts/link-skills.sh` symlinks this bundle into
  `${CODEX_HOME:-$HOME/.codex}/skills` for local use.
- `scripts/validate-plugin.sh` checks manifest fields, skill metadata, README
  coverage, removed upstream artifacts, and license files.
- `scripts/integration-test.sh` runs deterministic validation in Docker.
- `RUN_LIVE_CODEX_TESTS=1 scripts/integration-test.sh` also runs the live
  `setup-project-context` flow through the local Codex CLI.

## Coding Style & Naming Conventions

Use POSIX-friendly Bash with `set -euo pipefail` for scripts. Keep Markdown
direct, task-oriented, and specific to Codex behavior. Skill directories use
lowercase kebab-case, matching the `name:` in `SKILL.md` frontmatter. Keep YAML
metadata concise and quote values only when needed.

## Testing Guidelines

Run `scripts/validate-plugin.sh` before any commit that changes skills,
metadata, README coverage, or helper scripts. Run `scripts/integration-test.sh`
when changing linking, validation, Docker fixtures, or runtime scripts. Use the
live test only when Codex CLI credentials are available and the change affects
`setup-project-context` or CLI invocation behavior.

## Commit & Pull Request Guidelines

History currently uses short imperative commit subjects, for example
`import codexlht and add a codexlhp`. Keep commits focused and mention the
skill or script touched. Pull requests should describe the behavior changed,
list validation commands run, and call out any live Codex test coverage or
reason it was skipped.

## Agent-Specific Instructions

When editing a skill, read its `SKILL.md` first and preserve progressive
disclosure: keep the entry file short, and move detailed variants into
references or scripts. Do not reintroduce removed upstream material such as
`CLAUDE.md`, deprecated skill folders, or unrelated personal utilities.
