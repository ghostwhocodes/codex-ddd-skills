#!/usr/bin/env bash

run_long_horizon_loop() {
  local finalize_exit note
  local slice_started_at slice_started_epoch slice_ended_at slice_ended_epoch slice_duration

  pending_closeout_resume_attempts="${auto_resume_pending_closeout}"
  wrapper_review_enabled=0
  if [[ -n "${auto_review_loop}" ]]; then
    wrapper_review_enabled=1
  fi
  review_resume_attempts="${auto_review_loop:-0}"
  next_prompt="${prompt}"
  next_prompt_kind="initial"

  while true; do
    slice_index=$((slice_index + 1))
    slice_started_at="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    slice_started_epoch="$(now_epoch)"
    if run_codex_prompt "${next_prompt}"; then
      codex_exit=0
    else
      codex_exit=$?
    fi
    slice_ended_at="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
    slice_ended_epoch="$(now_epoch)"
    slice_duration="$(duration_seconds_between "${slice_started_epoch}" "${slice_ended_epoch}")"
    record_task_event "run_slice_completed" \
      --slice-kind "${next_prompt_kind}" \
      --slice-index "${slice_index}" \
      --exit-code "${codex_exit}" \
      --started-at "${slice_started_at}" \
      --ended-at "${slice_ended_at}" \
      --duration-seconds "${slice_duration}"

    if [[ ${codex_exit} -ne 0 ]]; then
      record_runner_decision \
        "slice_nonzero_exit" \
        "stop" \
        "Codex ${next_prompt_kind} slice ${slice_index} exited ${codex_exit}; stopping without closeout sync."
      break
    fi

    if finalize_zero_exit_run; then
      record_runner_decision \
        "contract_satisfied" \
        "stop_success" \
        "Finalize succeeded after ${next_prompt_kind} slice ${slice_index}; contract was satisfied and handoff is ready."
      codex_exit=0
      break
    else
      finalize_exit=$?
    fi

    if [[ ${finalize_exit} -eq ${FINALIZE_PENDING_CLOSEOUT} ]]; then
      if [[ ${pending_closeout_resume_attempts} -gt 0 || ${review_resume_attempts} -gt 0 ]]; then
        note="Pending closeout remained after a zero-exit ${next_prompt_kind} run; relaunching with the resume prompt."
        record_task_event "task_incomplete" --note "${note}"
        record_runner_decision \
          "pending_closeout_resume" \
          "resume" \
          "Closeout remained pending after ${next_prompt_kind} slice ${slice_index}; pending-closeout attempts remaining: ${pending_closeout_resume_attempts}; review-loop attempts remaining: ${review_resume_attempts}."
        echo "Closeout remained pending after a zero-exit ${next_prompt_kind} run; relaunching Codex with the resume prompt." >&2
        if [[ ${pending_closeout_resume_attempts} -gt 0 ]]; then
          pending_closeout_resume_attempts=$((pending_closeout_resume_attempts - 1))
        else
          review_resume_attempts=$((review_resume_attempts - 1))
        fi
        next_prompt="${resume_prompt}"
        next_prompt_kind="resume"
        continue
      fi

      note="Pending closeout remained after the final zero-exit ${next_prompt_kind} run; no auto-resume attempts remain."
      record_task_event "task_incomplete" --note "${note}"
      record_runner_decision \
        "pending_closeout_exhausted" \
        "stop" \
        "Closeout remained pending after ${next_prompt_kind} slice ${slice_index}; no pending-closeout or review-loop attempts remain."
      echo "Closeout remained pending after a zero-exit ${next_prompt_kind} run, and no auto-resume attempts remain." >&2
      codex_exit=1
      break
    fi

    if [[ ${finalize_exit} -eq ${FINALIZE_REVIEW_FINDINGS} ]]; then
      if [[ ${review_resume_attempts} -gt 0 ]]; then
        note="Wrapper review found material findings after a zero-exit ${next_prompt_kind} run; relaunching with the resume prompt."
        record_task_event "task_incomplete" --note "${note}"
        record_runner_decision \
          "wrapper_review_findings_resume" \
          "resume" \
          "Wrapper review found material findings after ${next_prompt_kind} slice ${slice_index}; review-loop attempts remaining before decrement: ${review_resume_attempts}."
        echo "Wrapper review found material findings after a zero-exit ${next_prompt_kind} run; relaunching Codex with the resume prompt (${review_resume_attempts} review-loop attempt(s) remaining before relaunch)." >&2
        review_resume_attempts=$((review_resume_attempts - 1))
        next_prompt="$(resume_prompt_with_review_context)"
        next_prompt_kind="resume"
        continue
      fi

      note="Wrapper review found material findings after the final zero-exit ${next_prompt_kind} run; no auto-review attempts remain."
      record_task_event "task_incomplete" --note "${note}"
      record_runner_decision \
        "wrapper_review_findings_exhausted" \
        "stop" \
        "Wrapper review found material findings after ${next_prompt_kind} slice ${slice_index}; no review-loop attempts remain."
      echo "Wrapper review found material findings after a zero-exit ${next_prompt_kind} run, and no auto-review attempts remain." >&2
      codex_exit=1
      break
    fi

    record_runner_decision \
      "finalize_failed" \
      "stop" \
      "Finalize failed with wrapper code ${finalize_exit} after ${next_prompt_kind} slice ${slice_index}; stopping."
    codex_exit=1
    break
  done
}
