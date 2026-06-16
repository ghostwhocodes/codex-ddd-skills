#!/usr/bin/env bash

readonly FINALIZE_PENDING_CLOSEOUT=20
readonly FINALIZE_CLOSEOUT_FAILED=21
readonly FINALIZE_CONTRACT_FAILED=22
readonly FINALIZE_REVIEW_FINDINGS=23
readonly FINALIZE_REVIEW_FAILED=24

finalize_zero_exit_run() {
  local closeout_sync_output closeout_sync_exit contract_output contract_exit handoff_target
  local review_exit
  local step_started_at step_started_epoch step_ended_at step_ended_epoch step_duration step_status

  if [[ ${wrapper_review_enabled} -eq 1 ]]; then
    if run_wrapper_review_step; then
      :
    else
      review_exit=$?
      if [[ ${review_exit} -eq ${WRAPPER_REVIEW_FINDINGS} ]]; then
        return "${FINALIZE_REVIEW_FINDINGS}"
      fi
      record_task_event "contract_failed" --note "Wrapper review failed before closeout sync."
      return "${FINALIZE_REVIEW_FAILED}"
    fi
  fi

  step_started_at="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  step_started_epoch="$(now_epoch)"
  set +e
  closeout_sync_output="$(
    CODEX_LHT_ALLOW_ACTIVE_WRAPPER=1 \
      python3 "${script_dir}/sync-task-closeout.py" --repo-root "${CODEXLHT_REPO_ROOT}" --task "${task_slug}"
  )"
  closeout_sync_exit=$?
  set -e
  step_ended_at="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  step_ended_epoch="$(now_epoch)"
  step_duration="$(duration_seconds_between "${step_started_epoch}" "${step_ended_epoch}")"
  step_status="failed"
  if [[ ${closeout_sync_exit} -eq 0 ]]; then
    step_status="success"
  fi
  record_task_event "runner_step_completed" \
    --step-id "closeout_sync" \
    --status "${step_status}" \
    --started-at "${step_started_at}" \
    --ended-at "${step_ended_at}" \
    --duration-seconds "${step_duration}"

  if [[ ${closeout_sync_exit} -ne 0 ]]; then
    if closeout_sync_is_pending_only "${closeout_sync_output}"; then
      printf '%s\n' "${closeout_sync_output}" >&2
      return "${FINALIZE_PENDING_CLOSEOUT}"
    fi

    record_task_event "contract_failed" --note "${closeout_sync_output}"
    echo "Closeout sync failed for task ${task_slug}." >&2
    printf '%s\n' "${closeout_sync_output}" >&2
    return "${FINALIZE_CLOSEOUT_FAILED}"
  fi

  step_started_at="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  step_started_epoch="$(now_epoch)"
  set +e
  contract_output="$(
    CODEX_LHT_ALLOW_ACTIVE_WRAPPER=1 \
      python3 "${script_dir}/check-contract.py" --repo-root "${CODEXLHT_REPO_ROOT}" --task "${task_slug}"
  )"
  contract_exit=$?
  set -e
  step_ended_at="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  step_ended_epoch="$(now_epoch)"
  step_duration="$(duration_seconds_between "${step_started_epoch}" "${step_ended_epoch}")"
  step_status="failed"
  if [[ ${contract_exit} -eq 0 ]]; then
    step_status="success"
  fi
  record_task_event "runner_step_completed" \
    --step-id "contract_check" \
    --status "${step_status}" \
    --started-at "${step_started_at}" \
    --ended-at "${step_ended_at}" \
    --duration-seconds "${step_duration}"

  if [[ ${contract_exit} -ne 0 ]]; then
    record_task_event "contract_failed" --note "${contract_output}"
    echo "Contract check failed for task ${task_slug}." >&2
    printf '%s\n' "${contract_output}" >&2
    return "${FINALIZE_CONTRACT_FAILED}"
  fi

  handoff_target="$(
    printf '%s\n' "${contract_output}" \
      | python3 -c 'import json, sys; print(json.load(sys.stdin)["handoff_target"])'
  )"

  record_task_event "contract_satisfied" --handoff-target "${handoff_target}"
  record_task_event "handoff_ready" --handoff-target "${handoff_target}"
  return 0
}
