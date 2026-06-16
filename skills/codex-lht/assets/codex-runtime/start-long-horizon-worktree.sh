#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${script_dir}/env.sh"

task_slug=""
branch_name=""
worktree_path=""
base_ref="HEAD"
force_sync=0
run_immediately=1
run_args=()
new_worktree=0

usage() {
  cat <<EOF
Usage: ${CODEXLHT_RUNTIME_COMMAND_PREFIX_SHELL}/start-long-horizon-worktree.sh --task <slug> [options] [-- run-long-horizon-args...]

Options:
  --task <slug>         Task slug under ${CODEXLHT_TASK_ROOT_REL}/<slug>.
  --branch <name>       Worktree branch name. Default: ${CODEXLHT_BRANCH_PREFIX}/<task-slug>
  --path <dir>          Worktree directory. Default: <repo>-<task-slug>-codexlht
  --base <ref>          Base ref for the worktree. Default: HEAD
  --force-sync          Overwrite synced scaffold/task files in the worktree.
  --no-run              Create and sync the worktree but do not launch Codex.
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
    --path)
      worktree_path="${2:?missing worktree path}"
      shift 2
      ;;
    --base)
      base_ref="${2:?missing base ref}"
      shift 2
      ;;
    --force-sync)
      force_sync=1
      shift
      ;;
    --no-run)
      run_immediately=0
      shift
      ;;
    --)
      shift
      while (($#)); do
        run_args+=("$1")
        shift
      done
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

if [[ -z "${task_slug}" ]]; then
  echo "--task is required." >&2
  usage >&2
  exit 1
fi

if [[ -z "${CODEXLHT_RUNTIME_ROOT_REL}" ]]; then
  echo "Runtime directory must be inside the repository to start a synced worktree: ${CODEXLHT_RUNTIME_ROOT}" >&2
  exit 1
fi

if ! task_dir="$(codexlht_require_initialized_task_dir "${task_slug}")"; then
  echo "Create it first with ./${CODEXLHT_RUNTIME_ROOT_REL}/init-long-horizon-task.sh --task ${task_slug}" >&2
  exit 1
fi
repo_root_real="$(cd "${CODEXLHT_REPO_ROOT}" && pwd -P)"
case "${task_dir}/" in
  "${repo_root_real}/"*)
    task_dir_rel="${task_dir#"${repo_root_real}/"}"
    ;;
  *)
    echo "Task directory is outside repository: ${task_dir}" >&2
    exit 1
    ;;
esac

branch_name="${branch_name:-${CODEXLHT_BRANCH_PREFIX}/${task_slug}}"
worktree_path="${worktree_path:-${CODEXLHT_REPO_ROOT%/}-${task_slug}-codexlht}"

if ! command -v git >/dev/null 2>&1; then
  echo "git is required." >&2
  exit 1
fi

current_branch="$(git -C "${CODEXLHT_REPO_ROOT}" branch --show-current || true)"
if [[ "${current_branch}" == "${branch_name}" ]]; then
  echo "Refusing to create worktree on the currently checked out branch: ${branch_name}" >&2
  exit 1
fi

abs_path() {
  local path="$1"
  local dir
  local base

  dir="$(dirname "${path}")"
  base="$(basename "${path}")"
  if [[ -d "${path}" ]]; then
    (cd "${path}" && pwd -P)
  else
    (cd "${dir}" && printf '%s/%s\n' "$(pwd -P)" "${base}")
  fi
}

repo_common_dir="$(git -C "${CODEXLHT_REPO_ROOT}" rev-parse --git-common-dir)"
if [[ "${repo_common_dir}" != /* ]]; then
  repo_common_dir="${CODEXLHT_REPO_ROOT}/${repo_common_dir}"
fi
repo_common_dir="$(abs_path "${repo_common_dir}")"

if [[ ! -d "${worktree_path}" ]]; then
  new_worktree=1
  if git -C "${CODEXLHT_REPO_ROOT}" show-ref --verify --quiet "refs/heads/${branch_name}"; then
    git -C "${CODEXLHT_REPO_ROOT}" worktree add "${worktree_path}" "${branch_name}"
  else
    git -C "${CODEXLHT_REPO_ROOT}" worktree add -b "${branch_name}" "${worktree_path}" "${base_ref}"
  fi
else
  worktree_abs="$(abs_path "${worktree_path}")"
  if ! git -C "${worktree_path}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "Refusing to reuse existing directory that is not a Git worktree: ${worktree_path}" >&2
    exit 1
  fi
  existing_top="$(git -C "${worktree_path}" rev-parse --show-toplevel)"
  existing_top="$(abs_path "${existing_top}")"
  if [[ "${existing_top}" != "${worktree_abs}" ]]; then
    echo "Refusing to reuse path that is not the root of a Git worktree: ${worktree_path}" >&2
    echo "Detected worktree root: ${existing_top}" >&2
    exit 1
  fi
  existing_common_dir="$(git -C "${worktree_path}" rev-parse --git-common-dir)"
  if [[ "${existing_common_dir}" != /* ]]; then
    existing_common_dir="${worktree_abs}/${existing_common_dir}"
  fi
  existing_common_dir="$(abs_path "${existing_common_dir}")"
  if [[ "${existing_common_dir}" != "${repo_common_dir}" ]]; then
    echo "Refusing to reuse worktree from a different Git repository: ${worktree_path}" >&2
    exit 1
  fi
  existing_branch="$(git -C "${worktree_path}" branch --show-current || true)"
  if [[ "${existing_branch}" != "${branch_name}" ]]; then
    echo "Refusing to reuse worktree on branch '${existing_branch:-detached HEAD}'; expected '${branch_name}'." >&2
    exit 1
  fi
fi

sync_file() {
  local rel_path="$1"
  local src="${CODEXLHT_REPO_ROOT}/${rel_path}"
  local dst="${worktree_path}/${rel_path}"

  if [[ ! -f "${src}" ]]; then
    echo "Required sync source does not exist: ${src}" >&2
    exit 1
  fi

  mkdir -p "$(dirname "${dst}")"

  if [[ -e "${dst}" && ${force_sync} -ne 1 && ${new_worktree} -ne 1 ]]; then
    if ! cmp -s "${src}" "${dst}"; then
      echo "Refusing to overwrite existing file without --force-sync: ${dst}" >&2
      exit 1
    fi
  else
    cp -f "${src}" "${dst}"
  fi
}

sync_file "${CODEXLHT_BOUNDARY_PROMPT}"
while IFS= read -r rel_path; do
  sync_file "${rel_path}"
done < <(cd "${CODEXLHT_REPO_ROOT}" && find "${CODEXLHT_RUNTIME_ROOT_REL}" -type f ! -path '*/__pycache__/*' | LC_ALL=C sort)
while IFS= read -r rel_path; do
  sync_file "${rel_path}"
done < <(cd "${CODEXLHT_REPO_ROOT}" && find "${task_dir_rel}" -type f ! -path '*/__pycache__/*' | LC_ALL=C sort)

while IFS= read -r script_path; do
  chmod +x "${worktree_path}/${script_path}"
done < <(cd "${CODEXLHT_REPO_ROOT}" && find "${CODEXLHT_RUNTIME_ROOT_REL}" -type f -name '*.sh' ! -path '*/__pycache__/*' | LC_ALL=C sort)

echo "Worktree ready: ${worktree_path}"
echo "Branch: ${branch_name}"

if [[ ${run_immediately} -eq 0 ]]; then
  exit 0
fi

cd "${worktree_path}"
exec "./${CODEXLHT_RUNTIME_ROOT_REL}/run-long-horizon.sh" --task "${task_slug}" "${run_args[@]}"
