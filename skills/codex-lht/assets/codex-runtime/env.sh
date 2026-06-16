#!/usr/bin/env bash
set -euo pipefail

if [[ -d "${HOME}/.local/bin" ]]; then
  export PATH="${HOME}/.local/bin:${PATH}"
fi

if [[ -n "${CODEXLHT_ENV_FILE:-}" && -f "${CODEXLHT_ENV_FILE}" ]]; then
  # shellcheck disable=SC1090
  source "${CODEXLHT_ENV_FILE}"
fi

script_source="${BASH_SOURCE:-}"
if [[ -n "${script_source}" ]]; then
  script_path="${BASH_SOURCE[0]}"
elif [[ -n "${ZSH_VERSION:-}" ]]; then
  script_path="$(eval 'printf %s "${(%):-%x}"')"
else
  script_path="$0"
fi

script_dir="$(cd "$(dirname "${script_path}")" && pwd)"
runtime_root="${script_dir}"

if [[ -n "${CODEXLHT_REPO_ROOT:-}" ]]; then
  repo_root="$(cd "${CODEXLHT_REPO_ROOT}" && pwd)"
elif command -v git >/dev/null 2>&1 && git -C "${runtime_root}" rev-parse --show-toplevel >/dev/null 2>&1; then
  repo_root="$(git -C "${runtime_root}" rev-parse --show-toplevel)"
else
  repo_root="$(cd "${runtime_root}/.." && pwd)"
fi

runtime_root_rel=""
case "${runtime_root}/" in
  "${repo_root}/"*)
    runtime_root_rel="${runtime_root#"${repo_root}/"}"
    runtime_root_rel="${runtime_root_rel%/}"
    ;;
esac
if [[ -n "${runtime_root_rel}" ]]; then
  runtime_command_prefix="./${runtime_root_rel}"
else
  runtime_command_prefix="${runtime_root}"
fi
runtime_command_prefix_shell="$(printf '%q' "${runtime_command_prefix}")"

artifact_root=""
runner_lock_path=""
if command -v git >/dev/null 2>&1 && git -C "${repo_root}" rev-parse --git-dir >/dev/null 2>&1; then
  git_dir="$(git -C "${repo_root}" rev-parse --git-dir)"
  if [[ "${git_dir}" != /* ]]; then
    git_dir="${repo_root}/${git_dir}"
  fi
  artifact_root="${git_dir}/codex-lht/artifacts"
  runner_lock_path="${git_dir}/codex-lht/locks/internal-long-horizon.lock"
else
  artifact_root="${repo_root}/target/codex-lht"
  runner_lock_path="${artifact_root}/locks/internal-long-horizon.lock"
fi

export CODEXLHT_REPO_ROOT="${repo_root}"
export CODEXLHT_RUNTIME_ROOT="${runtime_root}"
export CODEXLHT_RUNTIME_ROOT_REL="${runtime_root_rel}"
export CODEXLHT_RUNTIME_COMMAND_PREFIX="${runtime_command_prefix}"
export CODEXLHT_RUNTIME_COMMAND_PREFIX_SHELL="${runtime_command_prefix_shell}"
export CODEXLHT_ARTIFACT_ROOT="${CODEXLHT_ARTIFACT_ROOT:-${artifact_root}}"
export CODEXLHT_RUNNER_LOCK_PATH="${CODEXLHT_RUNNER_LOCK_PATH:-${runner_lock_path}}"
export CODEXLHT_TASK_ROOT_REL="${CODEXLHT_TASK_ROOT_REL:-ai/tasks}"
export CODEXLHT_TASK_ROOT="${repo_root}/${CODEXLHT_TASK_ROOT_REL}"
export CODEXLHT_BRANCH_PREFIX="${CODEXLHT_BRANCH_PREFIX:-codexlht}"
export CODEXLHT_DEFAULT_SANDBOX="${CODEXLHT_DEFAULT_SANDBOX:-danger-full-access}"
export CODEXLHT_DEFAULT_MODEL="${CODEXLHT_DEFAULT_MODEL:-gpt-5.4}"
export CODEXLHT_DEFAULT_REASONING_EFFORT="${CODEXLHT_DEFAULT_REASONING_EFFORT:-xhigh}"
export CODEXLHT_REVIEW_MODEL="${CODEXLHT_REVIEW_MODEL:-${CODEXLHT_DEFAULT_MODEL}}"
export CODEXLHT_REVIEW_REASONING_EFFORT="${CODEXLHT_REVIEW_REASONING_EFFORT:-xhigh}"
export CODEXLHT_BOUNDARY_PROMPT="${CODEXLHT_BOUNDARY_PROMPT:-AGENTS.md}"

codexlht_task_dir_for_slug() {
  local task_slug="$1"
  PYTHONPATH="${CODEXLHT_RUNTIME_ROOT}${PYTHONPATH:+:${PYTHONPATH}}" \
    python3 - "${CODEXLHT_REPO_ROOT}" "${task_slug}" <<'PY'
import sys
from pathlib import Path

from task_contract import ContractError, task_dir_for_slug

try:
    print(task_dir_for_slug(Path(sys.argv[1]).resolve(), sys.argv[2]))
except ContractError as exc:
    print(str(exc), file=sys.stderr)
    sys.exit(1)
PY
}

codexlht_require_task_dir() {
  local task_slug="$1"
  local resolved_task_dir

  if ! resolved_task_dir="$(codexlht_task_dir_for_slug "${task_slug}")"; then
    return 1
  fi
  if [[ ! -d "${resolved_task_dir}" ]]; then
    echo "Task directory does not exist: ${resolved_task_dir}" >&2
    return 1
  fi
  printf '%s\n' "${resolved_task_dir}"
}

codexlht_require_initialized_task_dir() {
  local task_slug="$1"
  local resolved_task_dir file
  local -a required_files

  if ! resolved_task_dir="$(codexlht_require_task_dir "${task_slug}")"; then
    return 1
  fi
  required_files=(
    "${resolved_task_dir}/Prompt.md"
    "${resolved_task_dir}/Contract.md"
    "${resolved_task_dir}/Plan.md"
    "${resolved_task_dir}/Implement.md"
    "${resolved_task_dir}/Documentation.md"
    "${resolved_task_dir}/Closeout.md"
    "${resolved_task_dir}/events.jsonl"
  )
  for file in "${required_files[@]}"; do
    if [[ ! -f "${file}" ]]; then
      echo "Missing task file: ${file}" >&2
      return 1
    fi
  done
  printf '%s\n' "${resolved_task_dir}"
}
