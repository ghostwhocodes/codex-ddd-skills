#!/usr/bin/env bash
set -euo pipefail

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
runtime_dir="${repo_dir}/skills/codex-lht/assets/codex-runtime"
tmp_dir="$(mktemp -d)"
trap 'rm -rf "${tmp_dir}"' EXIT

export CODEXLHT_REPO_ROOT="${tmp_dir}/repo"
export CODEXLHT_TASK_ROOT_REL="ai/tasks"
mkdir -p "${CODEXLHT_REPO_ROOT}"

fail() {
  echo "FAIL: $*" >&2
  exit 1
}

run_expect_fail() {
  local output status
  set +e
  output="$("$@" 2>&1)"
  status=$?
  set -e
  if [[ ${status} -eq 0 ]]; then
    printf '%s\n' "${output}" >&2
    fail "command unexpectedly succeeded: $*"
  fi
  printf '%s\n' "${output}"
}

assert_contains() {
  local haystack="$1"
  local needle="$2"
  if [[ "${haystack}" != *"${needle}"* ]]; then
    printf '%s\n' "${haystack}" >&2
    fail "expected output to contain: ${needle}"
  fi
}

side_effect="${tmp_dir}/validation-side-effect"
missing_output="$(
  run_expect_fail \
    "${runtime_dir}/run-task-command.sh" \
    --task missing-task \
    --validation-id smoke \
    -- \
    sh -c "touch '${side_effect}'"
)"
assert_contains "${missing_output}" "Task directory does not exist:"
if [[ -e "${side_effect}" ]]; then
  fail "validation command ran before missing-task preflight"
fi

partial_task_dir="${CODEXLHT_REPO_ROOT}/ai/tasks/partial-task"
partial_side_effect="${tmp_dir}/partial-validation-side-effect"
mkdir -p "${partial_task_dir}"
partial_output="$(
  run_expect_fail \
    "${runtime_dir}/run-task-command.sh" \
    --task partial-task \
    --validation-id smoke \
    -- \
    sh -c "touch '${partial_side_effect}'"
)"
assert_contains "${partial_output}" "Missing task file:"
if [[ -e "${partial_side_effect}" ]]; then
  fail "validation command ran before initialized-task preflight"
fi
if [[ -e "${partial_task_dir}/events.jsonl" ]]; then
  fail "uninitialized task preflight created an event log"
fi

partial_record_output="$(
  run_expect_fail \
    python3 "${runtime_dir}/record-task-event.py" \
    --repo-root "${CODEXLHT_REPO_ROOT}" \
    --task partial-task \
    --event validation_passed \
    --validation-id smoke \
    --exit-code 0 \
    --command true
)"
assert_contains "${partial_record_output}" "Missing task file:"
if [[ -e "${partial_task_dir}/events.jsonl" ]]; then
  fail "direct record-task-event created an event log for an uninitialized task"
fi

partial_closeout_output="$(
  run_expect_fail \
    python3 "${runtime_dir}/sync-task-closeout.py" \
    --repo-root "${CODEXLHT_REPO_ROOT}" \
    --task partial-task
)"
assert_contains "${partial_closeout_output}" "Missing task file:"
if [[ -e "${partial_task_dir}/events.jsonl" ]]; then
  fail "sync-task-closeout created an event log for an uninitialized task"
fi

partial_review_state_output="$(
  run_expect_fail \
    python3 "${runtime_dir}/update-wrapper-review-state.py" \
    --task-dir "${partial_task_dir}" \
    --status success
)"
assert_contains "${partial_review_state_output}" "Missing task file:"
if [[ -e "${partial_task_dir}/events.jsonl" ]]; then
  fail "update-wrapper-review-state created an event log for an uninitialized task"
fi

traversal_check_output="$(
  run_expect_fail \
    python3 "${runtime_dir}/check-contract.py" \
    --repo-root "${CODEXLHT_REPO_ROOT}" \
    --task ../../escape
)"
assert_contains "${traversal_check_output}" "Invalid task slug"

traversal_record_output="$(
  run_expect_fail \
    python3 "${runtime_dir}/record-task-event.py" \
    --repo-root "${CODEXLHT_REPO_ROOT}" \
    --task ../escape \
    --event validation_passed \
    --validation-id smoke \
    --exit-code 0 \
    --command true
)"
assert_contains "${traversal_record_output}" "Invalid task slug"

traversal_closeout_output="$(
  run_expect_fail \
    python3 "${runtime_dir}/sync-task-closeout.py" \
    --repo-root "${CODEXLHT_REPO_ROOT}" \
    --task ../escape
)"
assert_contains "${traversal_closeout_output}" "Invalid task slug"

traversal_summary_output="$(
  run_expect_fail \
    python3 "${runtime_dir}/summarize-long-horizon-run.py" \
    --repo-root "${CODEXLHT_REPO_ROOT}" \
    --task ../escape \
    --json
)"
assert_contains "${traversal_summary_output}" "Invalid task slug"

traversal_runner_output="$(
  run_expect_fail \
    "${runtime_dir}/run-long-horizon.sh" \
    --task ../escape
)"
assert_contains "${traversal_runner_output}" "Invalid task slug"

traversal_worktree_output="$(
  CODEXLHT_REPO_ROOT="${repo_dir}" \
    run_expect_fail \
      "${runtime_dir}/start-long-horizon-worktree.sh" \
      --task ../escape \
      --no-run
)"
assert_contains "${traversal_worktree_output}" "Invalid task slug"

traversal_merge_output="$(
  run_expect_fail \
    "${runtime_dir}/merge-task-branch.sh" \
    --task ../escape
)"
assert_contains "${traversal_merge_output}" "Invalid task slug"

task_root_output="$(
  CODEXLHT_TASK_ROOT_REL="../tasks" \
    run_expect_fail \
      python3 "${runtime_dir}/check-contract.py" \
      --repo-root "${CODEXLHT_REPO_ROOT}" \
      --task valid-task
)"
assert_contains "${task_root_output}" "Task root must not contain parent traversal"

"${runtime_dir}/init-long-horizon-task.sh" \
  --task valid-task \
  --title "Valid Task" \
  --spec ai/specs/valid-task.md \
  >/dev/null

"${runtime_dir}/run-task-command.sh" \
  --task valid-task \
  --validation-id smoke \
  -- \
  true \
  >/dev/null

grep -q '"validation_id": "smoke"' \
  "${CODEXLHT_REPO_ROOT}/ai/tasks/valid-task/events.jsonl" \
  || fail "valid validation event was not recorded"

echo "codex-lht runtime security regressions passed"
