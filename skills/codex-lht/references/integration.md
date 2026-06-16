# CodexLHT Integration Reference

Use this reference when installing CodexLHT in a repository or validating this
skill.

## Repository Integration

Install the runtime into a target repository:

```bash
<skill-dir>/scripts/install-runtime.sh --repo <repo-root>
```

Expected repository layout after installation:

```text
<repo-root>/
├── AGENTS.md
├── codex/
│   ├── init-long-horizon-task.sh
│   ├── run-long-horizon.sh
│   ├── run-task-command.sh
│   ├── check-contract.py
│   ├── lib/
│   ├── prompts/
│   ├── schemas/
│   └── templates/
└── ai/
    ├── tasks/
    └── policies/
```

The generic runtime defaults `CODEXLHT_BOUNDARY_PROMPT` to `AGENTS.md`.
Override it when a repository has a different boundary context file:

```bash
CODEXLHT_BOUNDARY_PROMPT=CODEXLHT_CONTEXT.md ./codex/run-long-horizon.sh --task <task>
```

Use `CODEXLHT_ENV_FILE` for project-specific toolchain setup:

```bash
CODEXLHT_ENV_FILE=.codexlht-env ./codex/run-long-horizon.sh --task <task>
```

## Example Project

Use a generated scratch Git repository as the default example project. It
should contain:

- `AGENTS.md` with brief project and validation rules
- `README.md`
- `ai/plans/example.md` or a short inline spec
- a trivial validation command such as `test -f README.md`

This validates the skill without depending on a language runtime, package
manager, network access, or project-specific files.

Minimum validation sequence:

```bash
git init
printf '# Example\n' > README.md
printf '# Agent Rules\n\nUse test -f README.md as validation.\n' > AGENTS.md
mkdir -p ai/plans
printf '# Example task\n\nMake the README exist.\n' > ai/plans/example.md
<skill-dir>/scripts/install-runtime.sh --repo .
./codex/init-long-horizon-task.sh --task example --title "Example" --spec ai/plans/example.md
./codex/run-task-command.sh --task example --validation-id readme-exists -- test -f README.md
python3 ./codex/check-contract.py --task example --pretty
```

The final contract check is expected to fail until `Contract.md` and
`Closeout.md` are edited to use `readme-exists` and satisfied requirement/review
state. That failure proves the contract gate is active.

## Extracting To A Separate Repo

Use a project-local skill folder when the user wants versioned source control.
Use an installed skill folder under `$CODEX_HOME/skills` or `~/.codex/skills`
when the user wants automatic discovery by Codex. A standalone repo can mirror
the skill folder directly when distribution or collaboration becomes useful.
