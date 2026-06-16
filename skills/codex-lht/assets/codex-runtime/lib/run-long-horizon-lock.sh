#!/usr/bin/env bash

require_codex_cli() {
  if ! command -v codex >/dev/null 2>&1; then
    echo "codex CLI is not installed or not on PATH." >&2
    exit 1
  fi
}

require_task_files() {
  if ! task_dir="$(codexlht_require_initialized_task_dir "${task_slug}")"; then
    exit 1
  fi
}

acquire_runner_lock() {
  local runner_path="$1"
  shift
  local lock_args=("$@")
  local lock_path="${CODEXLHT_RUNNER_LOCK_PATH}"
  local lock_acquired_marker lock_wrapper_exit

  if ! command -v flock >/dev/null 2>&1; then
    echo "flock is required for internal long-horizon run locking." >&2
    exit 1
  fi

  if [[ "${CODEX_LHT_LOCK_HELD:-0}" == "1" ]]; then
    unset CODEX_LHT_LOCK_HELD
    return 0
  fi

  mkdir -p "$(dirname "${lock_path}")"
  lock_acquired_marker="$(mktemp "${TMPDIR:-/tmp}/codex-lht-lock-acquired.XXXXXX")"
  rm -f "${lock_acquired_marker}"
  trap 'rm -f "${lock_acquired_marker}"' EXIT

  set +e
  flock -n --close \
    "${lock_path}" \
    "${BASH}" \
    -c '
      marker=$1
      shift
      : > "${marker}"
      exec "$@"
    ' \
    "${BASH}" \
    "${lock_acquired_marker}" \
    env \
    CODEX_LHT_LOCK_HELD=1 \
    "${BASH}" \
    "${runner_path}" \
    "${lock_args[@]}"
  lock_wrapper_exit=$?
  set -e

  if [[ ! -f "${lock_acquired_marker}" ]]; then
    echo "Another internal long-horizon Codex run is already active for this checkout." >&2
    echo "Wait for it to finish or stop it before starting a new run." >&2
    rm -f "${lock_acquired_marker}"
    trap - EXIT
    exit 1
  fi

  rm -f "${lock_acquired_marker}"
  trap - EXIT
  exit "${lock_wrapper_exit}"
}

find_same_checkout_validation_processes() {
  local pid cwd cmd process_pattern

  [[ -d /proc ]] || return 0
  command -v pgrep >/dev/null 2>&1 || return 0
  process_pattern="${CODEXLHT_STALE_PROCESS_PATTERN:-run-task-command\\.sh}"

  while IFS= read -r pid; do
    [[ -z "${pid}" ]] && continue
    [[ "${pid}" == "$$" ]] && continue
    [[ "${pid}" == "${BASHPID}" ]] && continue

    cwd="$(readlink -f "/proc/${pid}/cwd" 2>/dev/null || true)"
    [[ -z "${cwd}" ]] && continue
    [[ "${cwd}" == "${CODEXLHT_REPO_ROOT}" || "${cwd}" == "${CODEXLHT_REPO_ROOT}/"* ]] || continue

    cmd="$(tr '\0' ' ' < "/proc/${pid}/cmdline" 2>/dev/null || true)"
    [[ -z "${cmd}" ]] && continue

    printf '%s\t%s\t%s\n' "${pid}" "${cwd}" "${cmd}"
  done < <(pgrep -f "${process_pattern}" || true)
}

refuse_stale_validation_processes() {
  local stale_validation_processes
  stale_validation_processes="$(find_same_checkout_validation_processes || true)"
  if [[ -n "${stale_validation_processes}" ]]; then
    echo "Refusing to start because stale validation processes are still active in this checkout." >&2
    echo "Inspect and clean them up before rerunning this internal long-horizon task." >&2
    printf '%s\n' "${stale_validation_processes}" >&2
    exit 1
  fi
}
