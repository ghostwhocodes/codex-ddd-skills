#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$REPO"

python3 - <<'PY'
import json
import pathlib
import re
import subprocess
import sys

repo = pathlib.Path.cwd()


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    sys.exit(1)


def read_text(path: pathlib.Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        fail(f"missing required file: {path}")


manifest_path = repo / ".codex-plugin" / "plugin.json"
try:
    manifest = json.loads(read_text(manifest_path))
except json.JSONDecodeError as exc:
    fail(f"{manifest_path} is not valid JSON: {exc}")

required_manifest_fields = {
    "name": str,
    "version": str,
    "description": str,
    "author": dict,
    "repository": str,
    "license": str,
    "skills": str,
    "interface": dict,
}
for field, expected_type in required_manifest_fields.items():
    value = manifest.get(field)
    if not isinstance(value, expected_type) or value in ("", {}):
        fail(f"plugin manifest field {field!r} must be a non-empty {expected_type.__name__}")

if manifest["skills"] != "./skills/":
    fail("plugin manifest field 'skills' must be './skills/'")

interface = manifest["interface"]
for field in ("displayName", "shortDescription", "longDescription", "developerName", "category"):
    if not isinstance(interface.get(field), str) or not interface[field].strip():
        fail(f"plugin interface field {field!r} must be a non-empty string")

for path in (repo / "LICENSE", repo / "NOTICE.md", repo / "README.md"):
    if not path.is_file():
        fail(f"missing required file: {path.relative_to(repo)}")

removed_paths = [
    "CLAUDE.md",
    "skills/deprecated",
    "skills/in-progress",
    "skills/personal",
    "skills/misc",
    "skills/caveman",
    "skills/teach",
]
for removed_path in removed_paths:
    if (repo / removed_path).exists():
        fail(f"removed/deferred upstream artifact still exists: {removed_path}")

skill_files = sorted((repo / "skills").glob("*/SKILL.md"))
if not skill_files:
    fail("no skills found under skills/*/SKILL.md")

skills = []
for skill_file in skill_files:
    skill_dir = skill_file.parent
    skill_name = skill_dir.name
    text = read_text(skill_file)
    match = re.match(r"^---\n(?P<body>.*?)\n---\n", text, flags=re.S)
    if not match:
        fail(f"{skill_file.relative_to(repo)} is missing YAML frontmatter")
    frontmatter = match.group("body")
    name_match = re.search(r"^name:\s*(.+?)\s*$", frontmatter, flags=re.M)
    description_match = re.search(r"^description:\s*(.+?)\s*$", frontmatter, flags=re.M)
    if not name_match:
        fail(f"{skill_file.relative_to(repo)} is missing frontmatter name")
    if name_match.group(1).strip() != skill_name:
        fail(
            f"{skill_file.relative_to(repo)} frontmatter name "
            f"{name_match.group(1).strip()!r} does not match directory {skill_name!r}"
        )
    if not description_match or not description_match.group(1).strip():
        fail(f"{skill_file.relative_to(repo)} is missing a non-empty frontmatter description")

    openai_yaml = skill_dir / "agents" / "openai.yaml"
    openai_text = read_text(openai_yaml)
    for field in ("display_name", "short_description", "default_prompt"):
        if not re.search(rf"^\s*{field}:\s*['\"]?.+['\"]?\s*$", openai_text, flags=re.M):
            fail(f"{openai_yaml.relative_to(repo)} is missing interface.{field}")
    skills.append(skill_name)

expected_list = [f"skills/{name}/SKILL.md" for name in skills]
actual_list = subprocess.check_output(
    [str(repo / "scripts" / "list-skills.sh")],
    text=True,
).splitlines()
if actual_list != expected_list:
    fail(
        "scripts/list-skills.sh output does not match skills/*/SKILL.md\n"
        f"expected: {expected_list}\n"
        f"actual:   {actual_list}"
    )

readme = read_text(repo / "README.md")
for name in skills:
    expected_link = f"./skills/{name}/SKILL.md"
    if expected_link not in readme:
        fail(f"README.md does not link to {expected_link}")

print(f"plugin validation passed ({len(skills)} skills)")
PY
