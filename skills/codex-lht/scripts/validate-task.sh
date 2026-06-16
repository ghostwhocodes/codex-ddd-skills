#!/usr/bin/env bash
set -euo pipefail

repo_root=""
task_slug=""
target_rel="codex"

usage() {
  cat <<EOF
Usage: validate-task.sh --repo <path> --task <slug> [--target codex]

Runs the CodexLHT contract checker for a task in a repository.
EOF
}

while (($#)); do
  case "$1" in
    --repo)
      repo_root="${2:?missing repo path}"
      shift 2
      ;;
    --task)
      task_slug="${2:?missing task slug}"
      shift 2
      ;;
    --target)
      target_rel="${2:?missing target path}"
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

if [[ -z "${repo_root}" || -z "${task_slug}" ]]; then
  usage >&2
  exit 1
fi

cd "${repo_root}"
python3 "./${target_rel}/check-contract.py" --task "${task_slug}" --pretty
