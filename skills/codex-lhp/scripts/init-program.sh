#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "${script_dir}/.." && pwd)"
template_dir="${skill_dir}/assets/program-template"

repo_root=""
program_id=""
program_title=""
spec_root="ai/specs"
force=0

usage() {
  cat <<EOF
Usage: init-program.sh --repo <path> --program <id> [options]

Options:
  --title <title>       Human-readable program title. Defaults to the id.
  --spec-root <path>    Controlling spec root. Default: ai/specs.
  --force               Overwrite existing program files.
EOF
}

validate_program_id() {
  if [[ ! "${program_id}" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
    echo "Invalid program id: ${program_id}" >&2
    echo "Program id must be a single path segment using only ASCII letters, digits, '.', '_' and '-', and must start with a letter or digit." >&2
    exit 1
  fi
}

prepare_program_dir() {
  local current expected_program_dir_real part program_dir_real program_root program_root_real program_root_rel repo_root_real
  local -a program_root_parts

  program_root="${repo_root}/ai/programs"
  case "${program_root}/" in
    "${repo_root}/"*) ;;
    *)
      echo "Refusing to use program root outside repository: ${program_root}" >&2
      exit 1
      ;;
  esac

  program_root_rel="${program_root#"${repo_root}/"}"
  IFS='/' read -r -a program_root_parts <<< "${program_root_rel}"
  current="${repo_root}"
  for part in "${program_root_parts[@]}"; do
    [[ -z "${part}" || "${part}" == "." ]] && continue
    if [[ "${part}" == ".." ]]; then
      echo "Refusing to use program root with parent traversal: ${program_root}" >&2
      exit 1
    fi
    current="${current}/${part}"
    if [[ -L "${current}" ]]; then
      echo "Refusing to use symlinked program root path: ${current}" >&2
      exit 1
    fi
  done

  mkdir -p "${program_root}"

  if [[ -L "${program_dir}" ]]; then
    echo "Refusing to use symlinked program directory: ${program_dir}" >&2
    exit 1
  fi

  mkdir -p "${program_dir}"

  repo_root_real="$(cd "${repo_root}" && pwd -P)"
  program_root_real="$(cd "${program_root}" && pwd -P)"
  program_dir_real="$(cd "${program_dir}" && pwd -P)"
  expected_program_dir_real="${program_root_real}/${program_id}"

  case "${program_root_real}/" in
    "${repo_root_real}/"*) ;;
    *)
      echo "Refusing to use program root outside repository: ${program_root}" >&2
      exit 1
      ;;
  esac

  if [[ "${program_dir_real}" != "${expected_program_dir_real}" ]]; then
    echo "Refusing to use program directory outside ${program_root}: ${program_dir}" >&2
    exit 1
  fi
}

while (($#)); do
  case "$1" in
    --repo)
      repo_root="${2:?missing repo path}"
      shift 2
      ;;
    --program)
      program_id="${2:?missing program id}"
      shift 2
      ;;
    --title)
      program_title="${2:?missing title}"
      shift 2
      ;;
    --spec-root)
      spec_root="${2:?missing spec root}"
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
      echo "Unknown argument: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

if [[ -z "${repo_root}" || -z "${program_id}" ]]; then
  usage >&2
  exit 1
fi

validate_program_id
repo_root="$(cd "${repo_root}" && pwd)"
program_title="${program_title:-${program_id//-/ }}"
program_dir="${repo_root}/ai/programs/${program_id}"
today="$(date +%F)"

prepare_program_dir

render_template() {
  local src="$1"
  local dst="$2"

  if [[ -e "${dst}" && ${force} -ne 1 ]]; then
    echo "Refusing to overwrite existing file without --force: ${dst}" >&2
    exit 1
  fi

  CODEXLHP_RENDER_PROGRAM_ID="${program_id}" \
  CODEXLHP_RENDER_PROGRAM_TITLE="${program_title}" \
  CODEXLHP_RENDER_DATE="${today}" \
  CODEXLHP_RENDER_SPEC_ROOT="${spec_root}" \
    awk '
      BEGIN {
        keys[1] = "__PROGRAM_ID__"
        keys[2] = "__PROGRAM_TITLE__"
        keys[3] = "__DATE__"
        keys[4] = "__SPEC_ROOT__"

        replacements[keys[1]] = ENVIRON["CODEXLHP_RENDER_PROGRAM_ID"]
        replacements[keys[2]] = ENVIRON["CODEXLHP_RENDER_PROGRAM_TITLE"]
        replacements[keys[3]] = ENVIRON["CODEXLHP_RENDER_DATE"]
        replacements[keys[4]] = ENVIRON["CODEXLHP_RENDER_SPEC_ROOT"]
      }

      function render_line(value,    out, i, pos, best_pos, best_key) {
        out = ""
        while (1) {
          best_pos = 0
          best_key = ""
          for (i = 1; i <= 4; i++) {
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

for name in Program.md SpecBreakdown.md Milestones.md DependencyGraph.md ReviewGates.md State.md; do
  render_template "${template_dir}/${name}" "${program_dir}/${name}"
done

events_path="${program_dir}/events.jsonl"
if [[ -e "${events_path}" && ${force} -ne 1 ]]; then
  echo "Refusing to overwrite existing file without --force: ${events_path}" >&2
  exit 1
fi
: > "${events_path}"

echo "Initialized CodexLHP program scaffold: ${program_dir}"
