#!/usr/bin/env bash
set -euo pipefail

# Links all retained skills in the repository to the local Codex skills dir.

REPO="$(cd "$(dirname "$0")/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
DEST="$CODEX_HOME/skills"

# If the destination is a symlink that resolves into this repo, we'd end up
# writing the per-skill symlinks back into the repo's own skills/ tree. Detect
# and bail out instead of polluting the working copy.
if [ -L "$DEST" ]; then
  resolved="$(readlink -f "$DEST")"
  case "$resolved" in
    "$REPO"|"$REPO"/*)
      echo "error: $DEST is a symlink into this repo ($resolved)." >&2
      echo "Remove it (rm \"$DEST\") and re-run; the script will recreate it as a real dir." >&2
      exit 1
      ;;
  esac
fi

mkdir -p "$DEST"

find "$REPO/skills" -name SKILL.md -not -path '*/node_modules/*' -print0 |
while IFS= read -r -d '' skill_md; do
  src="$(dirname "$skill_md")"
  name="$(basename "$src")"
  target="$DEST/$name"

  if [ -e "$target" ] && [ ! -L "$target" ]; then
    echo "skip $name: $target exists and is not a symlink" >&2
    continue
  fi

  if [ -L "$target" ]; then
    existing_resolved="$(readlink -f "$target" 2>/dev/null || true)"
    if [ -z "$existing_resolved" ]; then
      echo "skip $name: $target is a symlink with an unresolved target" >&2
      continue
    fi

    case "$existing_resolved" in
      "$REPO"|"$REPO"/*) ;;
      *)
        echo "skip $name: $target is a symlink outside this repo ($existing_resolved)" >&2
        continue
        ;;
    esac
  fi

  ln -sfn "$src" "$target"
  echo "linked $name -> $src"
done
