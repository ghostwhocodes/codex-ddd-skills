#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if ! command -v codex >/dev/null 2>&1; then
  echo "FAIL: codex CLI is required for live tests" >&2
  exit 1
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "${tmp_dir}"' EXIT

target_repo="${tmp_dir}/target-repo"
codex_home="${tmp_dir}/codex-home"
source_codex_home="${CODEX_HOME:-$HOME/.codex}"

mkdir -p "$target_repo" "$codex_home"
git -C "$target_repo" init >/dev/null

for path in auth.json config.toml installation_id; do
  if [ -f "$source_codex_home/$path" ]; then
    cp "$source_codex_home/$path" "$codex_home/$path"
  fi
done

CODEX_HOME="$codex_home" "$REPO/scripts/link-skills.sh" >/dev/null

prompt='Use the setup-project-context skill in this repository. Do not ask follow-up questions; use these decisions: issue tracker is local markdown, triage labels use the default role strings, and domain docs use single-context layout. Create or update AGENTS.md and docs/agents/issue-tracker.md, docs/agents/triage-labels.md, and docs/agents/domain.md.'

CODEX_HOME="$codex_home" codex exec \
  -c approval_policy=never \
  --sandbox workspace-write \
  -C "$target_repo" \
  "$prompt"

for path in \
  AGENTS.md \
  docs/agents/issue-tracker.md \
  docs/agents/triage-labels.md \
  docs/agents/domain.md
do
  if [ ! -f "$target_repo/$path" ]; then
    echo "FAIL: live setup did not create $path" >&2
    exit 1
  fi
done

grep -q "## Agent skills" "$target_repo/AGENTS.md"
grep -qi "local" "$target_repo/docs/agents/issue-tracker.md"
grep -q "ready-for-agent" "$target_repo/docs/agents/triage-labels.md"
grep -qi "single-context" "$target_repo/docs/agents/domain.md"

echo "live setup-project-context flow passed"
