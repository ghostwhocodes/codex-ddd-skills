#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${script_dir}/env.sh"

source "${script_dir}/lib/run-long-horizon-args.sh"
source "${script_dir}/lib/run-long-horizon-lock.sh"
source "${script_dir}/lib/run-long-horizon-prompts.sh"
source "${script_dir}/lib/run-long-horizon-runtime.sh"
source "${script_dir}/lib/run-long-horizon-review.sh"
source "${script_dir}/lib/run-long-horizon-finalize.sh"
source "${script_dir}/lib/run-long-horizon-loop.sh"
source "${script_dir}/lib/run-long-horizon-summary.sh"

original_args=("$@")

task_slug=""
sandbox_mode="${CODEXLHT_DEFAULT_SANDBOX}"
model="${CODEXLHT_DEFAULT_MODEL}"
reasoning_effort="${CODEXLHT_DEFAULT_REASONING_EFFORT}"
review_model="${CODEXLHT_REVIEW_MODEL}"
review_reasoning_effort="${CODEXLHT_REVIEW_REASONING_EFFORT}"
auto_resume_pending_closeout=0
auto_review_loop=""
extra_args=()
review_extra_args=()

parse_runner_args "$@"
build_review_extra_args

require_task_files
require_codex_cli

mkdir -p "${CODEXLHT_ARTIFACT_ROOT}"
acquire_runner_lock "$0" "${original_args[@]}"
refuse_stale_validation_processes

build_runner_prompts

cd "${CODEXLHT_REPO_ROOT}"
initialize_run_state
run_long_horizon_loop
find_latest_rollout_path
emit_nonzero_exit_hint
emit_run_summary

exit "${codex_exit}"
