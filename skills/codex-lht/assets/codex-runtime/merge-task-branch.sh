#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${script_dir}/env.sh"

task_slug=""
branch_name=""
target_branch="master"

usage() {
  cat <<EOF
Usage: ${CODEXLHT_RUNTIME_COMMAND_PREFIX_SHELL}/merge-task-branch.sh [options]

Options:
  --task <slug>         Task slug. Default branch becomes ${CODEXLHT_BRANCH_PREFIX}/<slug>.
  --branch <name>       Explicit source branch.
  --into <branch>       Target branch to merge into. Default: master
  -h, --help            Show this help.
EOF
}

while (($#)); do
  case "$1" in
    --task)
      task_slug="${2:?missing task slug}"
      shift 2
      ;;
    --branch)
      branch_name="${2:?missing branch name}"
      shift 2
      ;;
    --into)
      target_branch="${2:?missing target branch}"
      shift 2
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

if [[ -n "${task_slug}" ]]; then
  if ! codexlht_task_dir_for_slug "${task_slug}" >/dev/null; then
    exit 1
  fi
  if [[ -z "${branch_name}" ]]; then
    branch_name="${CODEXLHT_BRANCH_PREFIX}/${task_slug}"
  fi
fi

if [[ -z "${branch_name}" ]]; then
  echo "Provide either --task or --branch." >&2
  usage >&2
  exit 1
fi

if [[ -n "$(git -C "${CODEXLHT_REPO_ROOT}" status --short)" ]]; then
  echo "Refusing to merge with a dirty working tree at ${CODEXLHT_REPO_ROOT}." >&2
  exit 1
fi

current_branch="$(git -C "${CODEXLHT_REPO_ROOT}" rev-parse --abbrev-ref HEAD)"
if [[ "${current_branch}" != "${target_branch}" ]]; then
  echo "Refusing to merge: current branch is ${current_branch}, expected ${target_branch}." >&2
  exit 1
fi

if ! git -C "${CODEXLHT_REPO_ROOT}" show-ref --verify --quiet "refs/heads/${branch_name}"; then
  echo "Branch does not exist: ${branch_name}" >&2
  exit 1
fi

echo "Merging ${branch_name} into ${target_branch}..."
git -C "${CODEXLHT_REPO_ROOT}" merge --no-edit "${branch_name}"
