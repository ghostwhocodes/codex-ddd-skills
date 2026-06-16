#!/usr/bin/env bash

find_latest_rollout_path() {
  latest_rollout_path=""
  if [[ -d "${session_dir}" ]]; then
    latest_rollout_path="$(
      find "${session_dir}" -type f -name 'rollout-*.jsonl' -newermt "${run_started_at_utc}" -printf '%T@ %p\n' \
        | LC_ALL=C sort -n \
        | tail -n 1 \
        | cut -d' ' -f2- \
        || true
    )"
  fi
}

emit_nonzero_exit_hint() {
  if [[ ${codex_exit} -ne 0 ]] && [[ -n "${latest_rollout_path}" ]] && rg -q '"type":"task_complete"' "${latest_rollout_path}"; then
    echo "Codex rollout recorded task_complete before a nonzero exit: ${latest_rollout_path}" >&2
  fi

  if [[ ${codex_exit} -ne 0 ]]; then
    if [[ -n "${latest_rollout_path}" ]]; then
      echo "Codex exited with code ${codex_exit}; inspect rollout: ${latest_rollout_path}" >&2
    else
      echo "Codex exited with code ${codex_exit}." >&2
    fi
  fi
}

emit_run_summary() {
  local run_ended_at_iso run_ended_epoch run_duration_seconds
  local summary_args

  run_ended_at_iso="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  run_ended_epoch="$(now_epoch)"
  run_duration_seconds="$(duration_seconds_between "${run_started_epoch}" "${run_ended_epoch}")"

  summary_args=(
    --repo-root "${CODEXLHT_REPO_ROOT}"
    --task "${task_slug}"
    --run-id "${run_id}"
    --run-started-at "${run_started_at_iso}"
    --run-ended-at "${run_ended_at_iso}"
    --run-duration-seconds "${run_duration_seconds}"
  )

  if [[ -n "${latest_rollout_path}" ]]; then
    summary_args+=(--rollout-path "${latest_rollout_path}")
  fi

  python3 "${script_dir}/summarize-long-horizon-run.py" "${summary_args[@]}" >&2
}
