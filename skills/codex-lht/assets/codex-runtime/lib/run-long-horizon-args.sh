#!/usr/bin/env bash

usage() {
  cat <<EOF
Usage: ${CODEXLHT_RUNTIME_COMMAND_PREFIX_SHELL}/run-long-horizon.sh --task <slug> [options] [-- extra-codex-args...]

Options:
  --task <slug>         Task slug under ${CODEXLHT_TASK_ROOT_REL}/<slug>.
  --sandbox <mode>      Codex sandbox mode. Default: ${CODEXLHT_DEFAULT_SANDBOX}
  --model <model>       Codex worker model. Default: ${CODEXLHT_DEFAULT_MODEL}
  --reasoning-effort <effort>
                        Codex worker reasoning effort. Default: ${CODEXLHT_DEFAULT_REASONING_EFFORT}
  --review-model <model>
                        Independent review model. Default: ${CODEXLHT_REVIEW_MODEL}
  --review-reasoning-effort <effort>
                        Independent review reasoning effort. Default: ${CODEXLHT_REVIEW_REASONING_EFFORT}
  --auto-resume-pending-closeout <n>
                        If closeout sync fails only because requirements or
                        reviews remain pending after a zero-exit run, relaunch
                        Codex up to <n> additional times with the resume prompt.
                        Default: 0
  --blocking-review     Run one wrapper-owned read-only merge-readiness review
                        before closeout sync and block completion on findings.
  --auto-review-loop <n>
                        Run the blocking review before closeout sync. If
                        material findings are returned or closeout remains
                        pending, relaunch Codex up to <n> additional times with
                        the resume prompt. 0 means review once without relaunch.
  -h, --help            Show this help.
EOF
}

parse_runner_args() {
  while (($#)); do
    case "$1" in
      --task)
        task_slug="${2:?missing task slug}"
        shift 2
        ;;
      --sandbox)
        sandbox_mode="${2:?missing sandbox mode}"
        shift 2
        ;;
      --model)
        model="${2:?missing model}"
        shift 2
        ;;
      --reasoning-effort)
        reasoning_effort="${2:?missing reasoning effort}"
        shift 2
        ;;
      --review-model)
        review_model="${2:?missing review model}"
        shift 2
        ;;
      --review-reasoning-effort)
        review_reasoning_effort="${2:?missing review reasoning effort}"
        shift 2
        ;;
      --auto-resume-pending-closeout)
        auto_resume_pending_closeout="${2:?missing auto-resume count}"
        shift 2
        ;;
      --blocking-review)
        auto_review_loop="${auto_review_loop:-0}"
        shift
        ;;
      --auto-review-loop)
        auto_review_loop="${2:?missing auto-review loop count}"
        shift 2
        ;;
      --)
        shift
        while (($#)); do
          extra_args+=("$1")
          shift
        done
        ;;
      -h|--help)
        usage
        exit 0
        ;;
      *)
        extra_args+=("$1")
        shift
        ;;
    esac
  done

  if [[ -z "${task_slug}" ]]; then
    echo "--task is required." >&2
    usage >&2
    exit 1
  fi

  if ! [[ "${auto_resume_pending_closeout}" =~ ^[0-9]+$ ]]; then
    echo "--auto-resume-pending-closeout must be a non-negative integer." >&2
    exit 1
  fi

  if [[ -n "${auto_review_loop}" ]] && ! [[ "${auto_review_loop}" =~ ^[0-9]+$ ]]; then
    echo "--auto-review-loop must be a non-negative integer." >&2
    exit 1
  fi
}

build_review_extra_args() {
  local skip_review_arg_value=0
  local extra_arg

  for extra_arg in "${extra_args[@]}"; do
    if [[ ${skip_review_arg_value} -eq 1 ]]; then
      skip_review_arg_value=0
      continue
    fi

    case "${extra_arg}" in
      -s|--sandbox|-C|--cd|--add-dir|-m|--model)
        skip_review_arg_value=1
        ;;
      --sandbox=*|-C=*|--cd=*|--add-dir=*|-m=*|--model=*|--dangerously-bypass-approvals-and-sandbox)
        ;;
      *)
        review_extra_args+=("${extra_arg}")
        ;;
    esac
  done
}
