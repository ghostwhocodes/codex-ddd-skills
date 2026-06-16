#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${script_dir}/env.sh"

task_slug=""
task_title=""
spec_reference="replace with a real spec path"
force=0

usage() {
  cat <<EOF
Usage: ${CODEXLHT_RUNTIME_COMMAND_PREFIX_SHELL}/init-long-horizon-task.sh --task <slug> [options]

Options:
  --task <slug>         Task slug, used under ${CODEXLHT_TASK_ROOT_REL}/<slug>.
  --title <title>       Human-readable title. Defaults to the slug.
  --spec <path>         Primary spec or reference path to include in Prompt.md.
  --force               Overwrite existing task files.
  -h, --help            Show this help.
EOF
}

validate_task_slug() {
  if [[ ! "${task_slug}" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
    echo "Invalid task slug: ${task_slug}" >&2
    echo "Task slug must be a single path segment using only ASCII letters, digits, '.', '_' and '-', and must start with a letter or digit." >&2
    exit 1
  fi
}

prepare_task_dir() {
  local current expected_task_dir_real part repo_root_real task_dir_real task_root_real task_root_rel
  local -a task_root_parts

  case "${CODEXLHT_TASK_ROOT}/" in
    "${CODEXLHT_REPO_ROOT}/"*) ;;
    *)
      echo "Refusing to use task root outside repository: ${CODEXLHT_TASK_ROOT}" >&2
      exit 1
      ;;
  esac

  task_root_rel="${CODEXLHT_TASK_ROOT#"${CODEXLHT_REPO_ROOT}/"}"
  IFS='/' read -r -a task_root_parts <<< "${task_root_rel}"
  current="${CODEXLHT_REPO_ROOT}"
  for part in "${task_root_parts[@]}"; do
    [[ -z "${part}" || "${part}" == "." ]] && continue
    if [[ "${part}" == ".." ]]; then
      echo "Refusing to use task root with parent traversal: ${CODEXLHT_TASK_ROOT}" >&2
      exit 1
    fi
    current="${current}/${part}"
    if [[ -L "${current}" ]]; then
      echo "Refusing to use symlinked task root path: ${current}" >&2
      exit 1
    fi
  done

  mkdir -p "${CODEXLHT_TASK_ROOT}"

  if [[ -L "${task_dir}" ]]; then
    echo "Refusing to use symlinked task directory: ${task_dir}" >&2
    exit 1
  fi

  mkdir -p "${task_dir}"

  repo_root_real="$(cd "${CODEXLHT_REPO_ROOT}" && pwd -P)"
  task_root_real="$(cd "${CODEXLHT_TASK_ROOT}" && pwd -P)"
  task_dir_real="$(cd "${task_dir}" && pwd -P)"
  expected_task_dir_real="${task_root_real}/${task_slug}"

  case "${task_root_real}/" in
    "${repo_root_real}/"*) ;;
    *)
      echo "Refusing to use task root outside repository: ${CODEXLHT_TASK_ROOT}" >&2
      exit 1
      ;;
  esac

  if [[ "${task_dir_real}" != "${expected_task_dir_real}" ]]; then
    echo "Refusing to use task directory outside ${CODEXLHT_TASK_ROOT}: ${task_dir}" >&2
    exit 1
  fi
}

while (($#)); do
  case "$1" in
    --task)
      task_slug="${2:?missing task slug}"
      shift 2
      ;;
    --title)
      task_title="${2:?missing task title}"
      shift 2
      ;;
    --spec)
      spec_reference="${2:?missing spec path}"
      shift 2
      ;;
    --force)
      force=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      if [[ -z "${task_slug}" && "$1" != -* ]]; then
        task_slug="$1"
        shift
      else
        echo "Unknown argument: $1" >&2
        usage >&2
        exit 1
      fi
      ;;
  esac
done

if [[ -z "${task_slug}" ]]; then
  echo "--task is required." >&2
  usage >&2
  exit 1
fi
validate_task_slug

if [[ -z "${task_title}" ]]; then
  task_title="${task_slug//-/ }"
fi

task_dir="${CODEXLHT_TASK_ROOT}/${task_slug}"
template_dir="${CODEXLHT_RUNTIME_ROOT}/templates/task"
today="$(date +%F)"
if [[ -n "${CODEXLHT_RUNTIME_ROOT_REL}" ]]; then
  runtime_root_ref="${CODEXLHT_RUNTIME_ROOT_REL}"
else
  runtime_root_ref="${CODEXLHT_RUNTIME_ROOT}"
fi
runtime_command_prefix="${CODEXLHT_RUNTIME_COMMAND_PREFIX_SHELL}"

prepare_task_dir

render_template() {
  local src="$1"
  local dst="$2"

  if [[ -e "${dst}" && ${force} -ne 1 ]]; then
    echo "Refusing to overwrite existing file without --force: ${dst}" >&2
    exit 1
  fi

  CODEXLHT_RENDER_TASK_SLUG="${task_slug}" \
  CODEXLHT_RENDER_TASK_TITLE="${task_title}" \
  CODEXLHT_RENDER_DATE="${today}" \
  CODEXLHT_RENDER_SPEC_REFERENCE="${spec_reference}" \
  CODEXLHT_RENDER_TASK_ROOT_REL="${CODEXLHT_TASK_ROOT_REL}" \
  CODEXLHT_RENDER_RUNTIME_ROOT_REF="${runtime_root_ref}" \
  CODEXLHT_RENDER_RUNTIME_COMMAND_PREFIX="${runtime_command_prefix}" \
  CODEXLHT_RENDER_BOUNDARY_PROMPT="${CODEXLHT_BOUNDARY_PROMPT}" \
    awk '
      BEGIN {
        keys[1] = "__TASK_SLUG__"
        keys[2] = "__TASK_TITLE__"
        keys[3] = "__DATE__"
        keys[4] = "__SPEC_REFERENCE__"
        keys[5] = "__TASK_ROOT_REL__"
        keys[6] = "__RUNTIME_ROOT_REF__"
        keys[7] = "__RUNTIME_COMMAND_PREFIX__"
        keys[8] = "__BOUNDARY_PROMPT__"

        replacements[keys[1]] = ENVIRON["CODEXLHT_RENDER_TASK_SLUG"]
        replacements[keys[2]] = ENVIRON["CODEXLHT_RENDER_TASK_TITLE"]
        replacements[keys[3]] = ENVIRON["CODEXLHT_RENDER_DATE"]
        replacements[keys[4]] = ENVIRON["CODEXLHT_RENDER_SPEC_REFERENCE"]
        replacements[keys[5]] = ENVIRON["CODEXLHT_RENDER_TASK_ROOT_REL"]
        replacements[keys[6]] = ENVIRON["CODEXLHT_RENDER_RUNTIME_ROOT_REF"]
        replacements[keys[7]] = ENVIRON["CODEXLHT_RENDER_RUNTIME_COMMAND_PREFIX"]
        replacements[keys[8]] = ENVIRON["CODEXLHT_RENDER_BOUNDARY_PROMPT"]
      }

      function render_line(value,    out, i, pos, best_pos, best_key) {
        out = ""
        while (1) {
          best_pos = 0
          best_key = ""
          for (i = 1; i <= 8; i++) {
            pos = index(value, keys[i])
            if (pos > 0 && (best_pos == 0 || pos < best_pos)) {
              best_pos = pos
              best_key = keys[i]
            }
          }

          if (best_pos == 0) {
            return out value
          }

          out = out substr(value, 1, best_pos - 1) replacements[best_key]
          value = substr(value, best_pos + length(best_key))
        }
      }

      {
        print render_line($0)
      }
    ' "${src}" > "${dst}"
}

render_template "${template_dir}/Prompt.md" "${task_dir}/Prompt.md"
render_template "${template_dir}/Contract.md" "${task_dir}/Contract.md"
render_template "${template_dir}/Plan.md" "${task_dir}/Plan.md"
render_template "${template_dir}/Implement.md" "${task_dir}/Implement.md"
render_template "${template_dir}/Documentation.md" "${task_dir}/Documentation.md"
render_template "${template_dir}/Closeout.md" "${task_dir}/Closeout.md"

events_path="${task_dir}/events.jsonl"
if [[ -e "${events_path}" && ${force} -ne 1 ]]; then
  echo "Refusing to overwrite existing file without --force: ${events_path}" >&2
  exit 1
fi
: > "${events_path}"

echo "Initialized internal CodexLHT task scaffold: ${task_dir}"
