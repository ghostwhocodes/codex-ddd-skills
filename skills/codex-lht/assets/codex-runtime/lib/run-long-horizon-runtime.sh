#!/usr/bin/env bash

initialize_run_state() {
  session_dir="${HOME}/.codex/sessions"
  run_id="lht-$(date -u +'%Y%m%dT%H%M%SZ')-${BASHPID}"
  run_started_at_utc="$(date -u +'%Y-%m-%d %H:%M:%S UTC')"
  run_started_at_iso="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  run_started_epoch="$(now_epoch)"
  codex_exit=0
  slice_index=0

  export CODEX_LHT_RUN_ID="${run_id}"
}

now_epoch() {
  python3 - <<'PY'
import time
print(f"{time.time():.6f}")
PY
}

duration_seconds_between() {
  local start_epoch="$1"
  local end_epoch="$2"
  START_EPOCH="${start_epoch}" END_EPOCH="${end_epoch}" python3 - <<'PY'
import os
start = float(os.environ["START_EPOCH"])
end = float(os.environ["END_EPOCH"])
print(f"{max(0.0, end - start):.6f}")
PY
}

record_task_event() {
  local event_name="$1"
  shift
  local -a event_args=(
    --repo-root "${CODEXLHT_REPO_ROOT}"
    --task "${task_slug}"
    --event "${event_name}"
    --run-id "${run_id}"
  )
  event_args+=("$@")

  python3 "${script_dir}/record-task-event.py" "${event_args[@]}" >/dev/null
}

record_runner_decision() {
  local decision_id="$1"
  local decision="$2"
  local note="$3"

  record_task_event "runner_decision" \
    --decision-id "${decision_id}" \
    --decision "${decision}" \
    --slice-index "${slice_index}" \
    --note "${note}"
}

closeout_sync_is_pending_only() {
  local output="$1"

  CLOSEOUT_SYNC_OUTPUT="${output}" python3 - <<'PY'
import json
import os
import sys

raw = os.environ.get("CLOSEOUT_SYNC_OUTPUT", "")
try:
    payload = json.loads(raw)
except json.JSONDecodeError:
    sys.exit(1)

errors = payload.get("errors")
if not isinstance(errors, list) or not errors:
    sys.exit(1)

allowed_prefixes = (
    "Closeout.md still has pending requirements:",
    "Closeout.md still has pending reviews:",
)

if all(isinstance(item, str) and item.startswith(allowed_prefixes) for item in errors):
    sys.exit(0)

sys.exit(1)
PY
}

run_codex_prompt() {
  local prompt_text="$1"

  if codex \
    -a never \
    exec \
    -C "${CODEXLHT_REPO_ROOT}" \
    -s "${sandbox_mode}" \
    -m "${model}" \
    -c "model_reasoning_effort=\"${reasoning_effort}\"" \
    -c "plan_mode_reasoning_effort=\"${reasoning_effort}\"" \
    "${extra_args[@]}" \
    "${prompt_text}"; then
    return 0
  else
    return $?
  fi
}
