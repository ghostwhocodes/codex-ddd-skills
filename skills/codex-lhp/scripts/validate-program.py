#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

VALID_STATES = {
    "planned",
    "ready",
    "active",
    "implementation-complete",
    "ai-review",
    "remediation",
    "human-review",
    "accepted",
    "completed",
    "blocked",
}

REQUIRED_FILES = [
    "Program.md",
    "SpecBreakdown.md",
    "Milestones.md",
    "DependencyGraph.md",
    "ReviewGates.md",
    "State.md",
    "events.jsonl",
]


def extract_json(path: Path, heading: str) -> Any:
    text = path.read_text(encoding="utf-8")
    pattern = rf"## {re.escape(heading)}\s*```json\s*(.*?)\s*```"
    match = re.search(pattern, text, flags=re.DOTALL)
    if not match:
        raise ValueError(f"{path.name}: missing JSON block under `{heading}`")
    return json.loads(match.group(1))


def require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    return value


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a CodexLHP program directory.")
    parser.add_argument("--repo", required=True, help="Repository root.")
    parser.add_argument("--program", required=True, help="Program id under ai/programs/<id>.")
    parser.add_argument("--json", action="store_true", help="Emit JSON result.")
    args = parser.parse_args()

    repo_root = Path(args.repo).resolve()
    program_dir = repo_root / "ai" / "programs" / args.program
    errors: list[str] = []

    if not program_dir.is_dir():
        errors.append(f"Program directory does not exist: {program_dir}")
    else:
        for name in REQUIRED_FILES:
            if not (program_dir / name).exists():
                errors.append(f"Missing required file: {name}")

    milestones_payload: dict[str, Any] = {}
    dependency_payload: dict[str, Any] = {}
    gates_payload: dict[str, Any] = {}
    state_payload: dict[str, Any] = {}

    if not errors:
        try:
            milestones_payload = require_dict(
                extract_json(program_dir / "Milestones.md", "Machine Milestones"),
                "Machine Milestones",
            )
            dependency_payload = require_dict(
                extract_json(program_dir / "DependencyGraph.md", "Machine Dependencies"),
                "Machine Dependencies",
            )
            gates_payload = require_dict(
                extract_json(program_dir / "ReviewGates.md", "Machine Review Gates"),
                "Machine Review Gates",
            )
            state_payload = require_dict(
                extract_json(program_dir / "State.md", "Machine State"),
                "Machine State",
            )
        except Exception as exc:  # noqa: BLE001 - validation should report all parse failures plainly.
            errors.append(str(exc))

    milestone_ids: set[str] = set()
    if not errors:
        milestones = milestones_payload.get("milestones")
        if not isinstance(milestones, list):
            errors.append("Milestones.md: `milestones` must be a list")
        else:
            for index, milestone in enumerate(milestones):
                if not isinstance(milestone, dict):
                    errors.append(f"Milestones.md: milestone {index} must be an object")
                    continue
                milestone_id = milestone.get("milestone_id")
                status = milestone.get("status")
                if not isinstance(milestone_id, str) or not milestone_id:
                    errors.append(f"Milestones.md: milestone {index} missing milestone_id")
                    continue
                if milestone_id in milestone_ids:
                    errors.append(f"Milestones.md: duplicate milestone_id `{milestone_id}`")
                milestone_ids.add(milestone_id)
                if status not in VALID_STATES:
                    errors.append(f"Milestones.md: `{milestone_id}` has invalid status `{status}`")

    if milestone_ids:
        dependencies = dependency_payload.get("dependencies")
        if not isinstance(dependencies, dict):
            errors.append("DependencyGraph.md: `dependencies` must be an object")
        else:
            unknown_dependency_keys = set(dependencies) - milestone_ids
            if unknown_dependency_keys:
                errors.append(
                    "DependencyGraph.md: unknown dependency milestone ids: "
                    + ", ".join(sorted(unknown_dependency_keys))
                )
            for milestone_id, prerequisites in dependencies.items():
                if not isinstance(prerequisites, list):
                    errors.append(f"DependencyGraph.md: `{milestone_id}` prerequisites must be a list")
                    continue
                invalid_prerequisites = [
                    index for index, prerequisite in enumerate(prerequisites) if not isinstance(prerequisite, str)
                ]
                if invalid_prerequisites:
                    errors.append(
                        f"DependencyGraph.md: `{milestone_id}` prerequisites must be milestone id strings "
                        "at indexes: "
                        + ", ".join(str(index) for index in invalid_prerequisites)
                    )
                    continue
                unknown = set(prerequisites) - milestone_ids
                if unknown:
                    errors.append(
                        f"DependencyGraph.md: `{milestone_id}` depends on unknown ids: "
                        + ", ".join(sorted(unknown))
                    )

        state_milestones = state_payload.get("milestones")
        if not isinstance(state_milestones, dict):
            errors.append("State.md: `milestones` must be an object")
        else:
            missing_state = milestone_ids - set(state_milestones)
            unknown_state = set(state_milestones) - milestone_ids
            if missing_state:
                errors.append("State.md: missing milestone state for: " + ", ".join(sorted(missing_state)))
            if unknown_state:
                errors.append("State.md: unknown milestone state ids: " + ", ".join(sorted(unknown_state)))
            for milestone_id, status in state_milestones.items():
                if status not in VALID_STATES:
                    errors.append(f"State.md: `{milestone_id}` has invalid state `{status}`")

        gate_status = gates_payload.get("milestone_gate_status")
        if not isinstance(gate_status, dict):
            errors.append("ReviewGates.md: `milestone_gate_status` must be an object")
        else:
            unknown_gate_ids = set(gate_status) - milestone_ids
            if unknown_gate_ids:
                errors.append("ReviewGates.md: unknown milestone ids: " + ", ".join(sorted(unknown_gate_ids)))

    result = {
        "ok": not errors,
        "program_dir": str(program_dir),
        "errors": errors,
    }
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    elif errors:
        for error in errors:
            print(error, file=sys.stderr)
    else:
        print(f"Program is valid: {program_dir}")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
