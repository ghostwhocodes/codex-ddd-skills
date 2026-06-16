#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from task_contract import (
    ContractError,
    evaluate_contract,
    repo_root_for_runtime_path,
    task_dir_for_slug,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Deterministically verify whether an internal CodexLHT task satisfies "
            "its machine-readable Contract.md boundary."
        )
    )
    parser.add_argument(
        "--task",
        required=True,
        help="Task slug under ai/tasks/<slug>.",
    )
    parser.add_argument(
        "--repo-root",
        default=str(repo_root_for_runtime_path(Path(__file__))),
        help="Repository root. Defaults to the Git repository containing this runtime.",
    )
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Pretty-print the JSON result.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        repo_root = Path(args.repo_root).resolve()
        task_dir = task_dir_for_slug(repo_root, args.task)
        result = evaluate_contract(task_dir)
    except ContractError as exc:
        result = {
            "ok": False,
            "errors": [str(exc)],
        }
        if "task_dir" in locals():
            result["task_dir"] = str(task_dir)

    if args.pretty:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(json.dumps(result, sort_keys=True))

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
