#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
IMAGE_NAME="${IMAGE_NAME:-codex-ddd-skills-integration}"

cd "$REPO"

docker build -t "$IMAGE_NAME" -f docker/integration/Dockerfile docker/integration

docker run --rm \
  -v "$REPO:/work:ro" \
  -w /work \
  "$IMAGE_NAME" \
  bash -lc '
    set -euo pipefail

    scripts/validate-plugin.sh
    tests/codex-lht-runtime-security.sh

    tmp_home="$(mktemp -d)"
    trap "rm -rf \"$tmp_home\"" EXIT

    CODEX_HOME="$tmp_home/codex" scripts/link-skills.sh

    source_count="$(find skills -mindepth 2 -maxdepth 2 -name SKILL.md | wc -l | tr -d " ")"
    linked_count="$(find "$tmp_home/codex/skills" -mindepth 1 -maxdepth 1 -type l | wc -l | tr -d " ")"
    if [ "$source_count" != "$linked_count" ]; then
      echo "FAIL: linked skill count ($linked_count) did not match source skill count ($source_count)" >&2
      exit 1
    fi

    scripts/list-skills.sh
  '

if [ "${RUN_LIVE_CODEX_TESTS:-0}" = "1" ]; then
  tests/live-codex-setup-project-context.sh
else
  echo "skipping live Codex setup-project-context test; set RUN_LIVE_CODEX_TESTS=1 to enable"
fi
