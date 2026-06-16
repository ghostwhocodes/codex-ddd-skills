#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
skill_dir="$(cd "${script_dir}/.." && pwd)"
source_dir="${skill_dir}/assets/codex-runtime"

repo_root=""
target_rel="codex"
force=0

usage() {
  cat <<EOF
Usage: install-runtime.sh --repo <path> [--target codex] [--force]

Copies the bundled CodexLHT runtime into a repository. Existing files that
differ are refused unless --force is supplied.
EOF
}

while (($#)); do
  case "$1" in
    --repo)
      repo_root="${2:?missing repo path}"
      shift 2
      ;;
    --target)
      target_rel="${2:?missing target path}"
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

if [[ -z "${repo_root}" ]]; then
  echo "--repo is required." >&2
  usage >&2
  exit 1
fi

repo_root="$(cd "${repo_root}" && pwd -P)"
target_dir="${repo_root}/${target_rel}"
runtime_command_prefix="./${target_rel}"
runtime_command_prefix_shell="$(printf '%q' "${runtime_command_prefix}")"

if [[ ! -d "${source_dir}" ]]; then
  echo "Bundled runtime not found: ${source_dir}" >&2
  exit 1
fi

path_is_under_repo() {
  local path_real="$1"

  case "${path_real}/" in
    "${repo_root}/"*) return 0 ;;
    *) return 1 ;;
  esac
}

validate_target_dir() {
  local current current_real part
  local -a target_parts

  if [[ "${target_rel}" == /* ]]; then
    echo "Refusing to use absolute runtime target: ${target_rel}" >&2
    exit 1
  fi

  IFS='/' read -r -a target_parts <<< "${target_rel}"
  current="${repo_root}"
  for part in "${target_parts[@]}"; do
    [[ -z "${part}" || "${part}" == "." ]] && continue
    if [[ "${part}" == ".." ]]; then
      echo "Refusing to use runtime target with parent traversal: ${target_rel}" >&2
      exit 1
    fi

    current="${current}/${part}"
    if [[ -d "${current}" ]]; then
      current_real="$(cd "${current}" && pwd -P)"
      if ! path_is_under_repo "${current_real}"; then
        echo "Refusing to use runtime target outside repository: ${target_rel}" >&2
        exit 1
      fi
    elif [[ -e "${current}" || -L "${current}" ]]; then
      echo "Refusing to use runtime target path component that is not a directory: ${current}" >&2
      exit 1
    fi
  done
}

validate_target_dir
mkdir -p "${target_dir}"
target_dir="$(cd "${target_dir}" && pwd -P)"
if ! path_is_under_repo "${target_dir}"; then
  echo "Refusing to use runtime target outside repository: ${target_rel}" >&2
  exit 1
fi

render_installed_doc() {
  CODEXLHT_INSTALL_TASK_ROOT_REL="ai/tasks" \
  CODEXLHT_INSTALL_RUNTIME_ROOT_REF="${target_rel}" \
  CODEXLHT_INSTALL_RUNTIME_COMMAND_PREFIX="${runtime_command_prefix_shell}" \
  awk '
    BEGIN {
      keys[1] = "__TASK_ROOT_REL__"
      keys[2] = "__RUNTIME_ROOT_REF__"
      keys[3] = "__RUNTIME_COMMAND_PREFIX__"

      replacements[keys[1]] = ENVIRON["CODEXLHT_INSTALL_TASK_ROOT_REL"]
      replacements[keys[2]] = ENVIRON["CODEXLHT_INSTALL_RUNTIME_ROOT_REF"]
      replacements[keys[3]] = ENVIRON["CODEXLHT_INSTALL_RUNTIME_COMMAND_PREFIX"]
    }

    function render_line(value,    out, i, pos, best_pos, best_key) {
      out = ""
      while (1) {
        best_pos = 0
        best_key = ""
        for (i = 1; i <= 3; i++) {
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
  ' "$1" > "$2"
}

while IFS= read -r rel_path; do
  src="${source_dir}/${rel_path}"
  dst="${target_dir}/${rel_path}"
  mkdir -p "$(dirname "${dst}")"

  case "${rel_path}" in
    LONG_HORIZON.md|LONG_HORIZON_SETUP.md)
      rendered_tmp="$(mktemp)"
      render_installed_doc "${src}" "${rendered_tmp}"
      if [[ -e "${dst}" && ${force} -ne 1 ]] && ! cmp -s "${rendered_tmp}" "${dst}"; then
        rm -f "${rendered_tmp}"
        echo "Refusing to overwrite changed file without --force: ${dst}" >&2
        exit 1
      fi
      cp "${rendered_tmp}" "${dst}"
      rm -f "${rendered_tmp}"
      chmod --reference="${src}" "${dst}"
      ;;
    *)
      if [[ -e "${dst}" && ${force} -ne 1 ]] && ! cmp -s "${src}" "${dst}"; then
        echo "Refusing to overwrite changed file without --force: ${dst}" >&2
        exit 1
      fi
      cp -p "${src}" "${dst}"
      ;;
  esac
done < <(cd "${source_dir}" && find . -type f ! -path '*/__pycache__/*' | sed 's|^\./||' | LC_ALL=C sort)

while IFS= read -r rel_path; do
  chmod +x "${target_dir}/${rel_path}"
done < <(cd "${source_dir}" && find . -type f \( -name '*.sh' -o -name '*.py' \) ! -path '*/__pycache__/*' | sed 's|^\./||' | LC_ALL=C sort)

echo "Installed CodexLHT runtime: ${target_dir}"
