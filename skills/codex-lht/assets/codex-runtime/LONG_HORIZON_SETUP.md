# CodexLHT Setup

This repository carries a repo-local CodexLHT helper for long-running,
contract-gated work.

## Boundaries

- Helper runtime lives under `__RUNTIME_ROOT_REF__/`.
- Long-horizon task docs live under `__TASK_ROOT_REL__/`.
- Reusable policy docs live under `ai/policies/`.
- Product/runtime code should not depend on `__RUNTIME_ROOT_REF__/` or `__TASK_ROOT_REL__/`.
- Repository-specific toolchain setup belongs in the configured boundary prompt
  or a file sourced through `CODEXLHT_ENV_FILE`, not in the generic helper
  runtime.

## Helper Runtime Features

- `Contract.md` and `Closeout.md` task files
- deterministic `events.jsonl` evidence logs
- validation wrapper at `__RUNTIME_COMMAND_PREFIX__/run-task-command.sh`
- contract checker at `__RUNTIME_COMMAND_PREFIX__/check-contract.py`
- closeout sync at `__RUNTIME_COMMAND_PREFIX__/sync-task-closeout.py`
- run summary tool at `__RUNTIME_COMMAND_PREFIX__/summarize-long-horizon-run.py`
- reusable policy checking through `ai/policies/<policy-id>/Policy.md`
- wrapper-owned blocking review mode with structured JSON review output
- task-local `ReviewResume.md` context for review-driven relaunches
