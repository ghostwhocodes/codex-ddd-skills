#!/usr/bin/env bash

readonly REVIEW_PARSE_FINDINGS=10
readonly WRAPPER_REVIEW_FINDINGS=30
readonly WRAPPER_REVIEW_FAILED=31

parse_review_output_status() {
  local review_output_path="$1"

  python3 - "${review_output_path}" <<'PY'
import json
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
try:
    raw = path.read_text(encoding="utf-8").strip()
except OSError as exc:
    print(f"Unable to read wrapper review output: {exc}", file=sys.stderr)
    sys.exit(2)

if raw.startswith("```"):
    match = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, flags=re.DOTALL)
    if match is not None:
        raw = match.group(1).strip()

try:
    payload = json.loads(raw)
except json.JSONDecodeError as exc:
    print(f"Wrapper review output is not valid JSON: {exc}", file=sys.stderr)
    sys.exit(2)

if not isinstance(payload, dict):
    print("Wrapper review output must be a JSON object.", file=sys.stderr)
    sys.exit(2)

status = payload.get("status")
findings = payload.get("material_findings")
if not isinstance(findings, list):
    print("Wrapper review output is missing list field `material_findings`.", file=sys.stderr)
    sys.exit(2)

if findings:
    print("findings")
    sys.exit(10)

if status == "clean":
    print("clean")
    sys.exit(0)

if status == "findings":
    print("findings")
    sys.exit(10)

print("Wrapper review output has invalid `status`.", file=sys.stderr)
sys.exit(2)
PY
}

record_wrapper_review_success() {
  local review_timestamp="$1"

  python3 "${script_dir}/update-wrapper-review-state.py" \
    --task-dir "${task_dir}" \
    --status success \
    --timestamp "${review_timestamp}"
}

record_wrapper_review_findings() {
  local review_output_path="$1"
  local review_timestamp="$2"

  python3 "${script_dir}/update-wrapper-review-state.py" \
    --task-dir "${task_dir}" \
    --status findings \
    --timestamp "${review_timestamp}" \
    --review-output "${review_output_path}"
}

run_wrapper_review_step() {
  local review_output_dir review_output_path review_codex_exit review_parse_output review_parse_exit
  local step_started_at step_started_epoch step_ended_at step_ended_epoch step_duration step_status

  review_output_dir="${CODEXLHT_ARTIFACT_ROOT}/reviews"
  mkdir -p "${review_output_dir}"
  review_output_path="$(mktemp "${review_output_dir}/codex-lht-review.XXXXXX.json")"
  step_started_at="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  step_started_epoch="$(now_epoch)"
  set +e
  codex \
    -a never \
    exec \
    -C "${CODEXLHT_REPO_ROOT}" \
    "${review_extra_args[@]}" \
    -s read-only \
    -m "${review_model}" \
    -c "model_reasoning_effort=\"${review_reasoning_effort}\"" \
    -c "plan_mode_reasoning_effort=\"${review_reasoning_effort}\"" \
    --output-schema "${script_dir}/schemas/merge-readiness-review.schema.json" \
    -o "${review_output_path}" \
    "${review_prompt}"
  review_codex_exit=$?
  set -e

  if [[ ${review_codex_exit} -eq 0 ]]; then
    set +e
    review_parse_output="$(parse_review_output_status "${review_output_path}" 2>&1)"
    review_parse_exit=$?
    set -e
  else
    review_parse_output="Wrapper review Codex run exited ${review_codex_exit}; output path: ${review_output_path}"
    review_parse_exit=2
  fi

  case "${review_parse_exit}" in
    0)
      step_status="success"
      ;;
    "${REVIEW_PARSE_FINDINGS}")
      step_status="findings"
      ;;
    *)
      step_status="failed"
      ;;
  esac

  step_ended_at="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  step_ended_epoch="$(now_epoch)"
  step_duration="$(duration_seconds_between "${step_started_epoch}" "${step_ended_epoch}")"
  record_task_event "runner_step_completed" \
    --step-id "wrapper_review" \
    --status "${step_status}" \
    --started-at "${step_started_at}" \
    --ended-at "${step_ended_at}" \
    --duration-seconds "${step_duration}" \
    --note "${review_output_path}"

  case "${review_parse_exit}" in
    0)
      if ! record_wrapper_review_success "${step_ended_at}"; then
        printf '%s\n' "Failed to record wrapper review success." >&2
        return "${WRAPPER_REVIEW_FAILED}"
      fi
      return 0
      ;;
    "${REVIEW_PARSE_FINDINGS}")
      if ! record_wrapper_review_findings "${review_output_path}" "${step_ended_at}"; then
        printf '%s\n' "Failed to record wrapper review findings." >&2
        return "${WRAPPER_REVIEW_FAILED}"
      fi
      printf '%s\n' "Wrapper review found material closeout-blocking findings." >&2
      printf '%s\n' "Review output: ${review_output_path}" >&2
      return "${WRAPPER_REVIEW_FINDINGS}"
      ;;
    *)
      printf '%s\n' "${review_parse_output}" >&2
      return "${WRAPPER_REVIEW_FAILED}"
      ;;
  esac
}
