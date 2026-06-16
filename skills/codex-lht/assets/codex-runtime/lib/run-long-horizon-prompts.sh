#!/usr/bin/env bash

escape_sed_replacement() {
  printf '%s' "$1" | sed -e 's/[\\&|]/\\&/g'
}

shell_quote() {
  printf '%q' "$1"
}

render_runner_template() {
  local template="$1"
  local runtime_root_ref runtime_command_prefix
  local escaped_task_slug escaped_task_slug_shell escaped_task_root_rel
  local escaped_boundary_prompt escaped_runtime_root_ref escaped_runtime_command_prefix

  escaped_task_slug="$(escape_sed_replacement "${task_slug}")"
  escaped_task_slug_shell="$(escape_sed_replacement "$(shell_quote "${task_slug}")")"
  escaped_task_root_rel="$(escape_sed_replacement "${CODEXLHT_TASK_ROOT_REL}")"
  escaped_boundary_prompt="$(escape_sed_replacement "${CODEXLHT_BOUNDARY_PROMPT}")"
  if [[ -n "${CODEXLHT_RUNTIME_ROOT_REL}" ]]; then
    runtime_root_ref="${CODEXLHT_RUNTIME_ROOT_REL}"
  else
    runtime_root_ref="${CODEXLHT_RUNTIME_ROOT}"
  fi
  runtime_command_prefix="${CODEXLHT_RUNTIME_COMMAND_PREFIX_SHELL}"
  escaped_runtime_root_ref="$(escape_sed_replacement "${runtime_root_ref}")"
  escaped_runtime_command_prefix="$(escape_sed_replacement "${runtime_command_prefix}")"

  printf '%s' "${template}" \
    | sed \
      -e "s|<task-slug-shell>|${escaped_task_slug_shell}|g" \
      -e "s|<task-slug>|${escaped_task_slug}|g" \
      -e "s|<task-root-rel>|${escaped_task_root_rel}|g" \
      -e "s|<boundary-prompt>|${escaped_boundary_prompt}|g" \
      -e "s|<runtime-root-rel>|${escaped_runtime_root_ref}|g" \
      -e "s|<runtime-command-prefix>|${escaped_runtime_command_prefix}|g"
}

build_runner_prompts() {
  local prompt_template resume_prompt_template review_rubric_template review_rubric

  prompt_template="$(<"${script_dir}/prompts/kickoff-task.md")"
  prompt="$(render_runner_template "${prompt_template}")"

  resume_prompt_template="$(<"${script_dir}/prompts/resume-task.md")"
  resume_prompt="$(render_runner_template "${resume_prompt_template}")"

  review_resume_path="${task_dir}/ReviewResume.md"
  review_rubric_template="$(<"${script_dir}/prompts/review-merge-readiness.md")"
  review_rubric="$(render_runner_template "${review_rubric_template}")"

  read -r -d '' review_prompt <<EOF || true
You are the wrapper-owned independent review phase for CodexLHT task \`${task_slug}\`.

Do not edit files, update task documents, run formatters, or run tests. Inspect
only. Use read-only shell commands as needed.

${review_rubric}

Return only JSON matching the configured schema:
- Set \`status\` to \`findings\` if any material bug, behavioral regression,
  lifecycle mistake, validation gap, documentation contradiction, or contract
  evidence gap should block closeout.
- Set \`status\` to \`clean\` only when there are no material closeout-blocking
  findings.
- Put every closeout-blocking finding in \`material_findings\`.
- Put non-blocking caveats in \`residual_risks\`.
EOF
}

resume_prompt_with_review_context() {
  if [[ ! -f "${review_resume_path}" ]]; then
    printf '%s' "${resume_prompt}"
    return
  fi

  cat <<EOF
${resume_prompt}

## Wrapper Review Resume Context

Read the task-local \`ReviewResume.md\` content below before making edits.

Step back before patching. Identify broader patterns, missing invariants, or
test-harness gaps that allowed the wrapper review findings to appear. Prefer
upstream fixes, contract/test-harness improvements, or invariant-preserving
changes over narrow line-local patches unless the evidence proves a local patch
is the correct fix.

$(<"${review_resume_path}")
EOF
}
