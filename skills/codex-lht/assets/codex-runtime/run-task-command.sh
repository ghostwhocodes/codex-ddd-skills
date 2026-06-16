#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${script_dir}/env.sh"

task_slug=""
validation_id=""
command_args=()

usage() {
  cat <<EOF
Usage: ${CODEXLHT_RUNTIME_COMMAND_PREFIX_SHELL}/run-task-command.sh --task <slug> --validation-id <id> -- <command...>
EOF
}

while (($#)); do
  case "$1" in
    --task)
      task_slug="${2:?missing task slug}"
      shift 2
      ;;
    --validation-id)
      validation_id="${2:?missing validation id}"
      shift 2
      ;;
    --)
      shift
      while (($#)); do
        command_args+=("$1")
        shift
      done
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "${task_slug}" || -z "${validation_id}" ]]; then
  usage >&2
  exit 1
fi

if [[ ${#command_args[@]} -eq 0 ]]; then
  echo "A command is required after --." >&2
  exit 1
fi

if ! task_dir="$(codexlht_require_initialized_task_dir "${task_slug}")"; then
  exit 1
fi

started_at="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
start_epoch="$(
  python3 - <<'PY'
import time
print(f"{time.time():.6f}")
PY
)"

set +e
"${command_args[@]}"
command_exit=$?
set -e

ended_at="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
end_epoch="$(
  python3 - <<'PY'
import time
print(f"{time.time():.6f}")
PY
)"
duration_seconds="$(
  START_EPOCH="${start_epoch}" END_EPOCH="${end_epoch}" python3 - <<'PY'
import os
start = float(os.environ["START_EPOCH"])
end = float(os.environ["END_EPOCH"])
print(f"{max(0.0, end - start):.6f}")
PY
)"

event_type="validation_failed"
if [[ ${command_exit} -eq 0 ]]; then
  event_type="validation_passed"
fi

command_display="$(printf '%q ' "${command_args[@]}")"
command_display="${command_display% }"

python3 "${script_dir}/record-task-event.py" \
  --repo-root "${CODEXLHT_REPO_ROOT}" \
  --task "${task_slug}" \
  --event "${event_type}" \
  --validation-id "${validation_id}" \
  --exit-code "${command_exit}" \
  --command "${command_display}" \
  --run-id "${CODEX_LHT_RUN_ID:-}" \
  --started-at "${started_at}" \
  --ended-at "${ended_at}" \
  --duration-seconds "${duration_seconds}"

exit "${command_exit}"
