#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from task_contract import (
    ContractError,
    append_event,
    repo_root_for_runtime_path,
    require_initialized_task_dir,
    task_dir_for_slug,
)


EVENT_CHOICES = [
    "validation_passed",
    "validation_failed",
    "contract_satisfied",
    "contract_failed",
    "task_incomplete",
    "handoff_ready",
    "run_slice_completed",
    "runner_step_completed",
    "runner_decision",
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Append one deterministic internal helper event to "
            "ai/tasks/<slug>/events.jsonl."
        )
    )
    parser.add_argument("--task", required=True, help="Task slug under ai/tasks/<slug>.")
    parser.add_argument(
        "--repo-root",
        default=str(repo_root_for_runtime_path(Path(__file__))),
        help="Repository root. Defaults to the Git repository containing this runtime.",
    )
    parser.add_argument("--event", required=True, choices=EVENT_CHOICES)
    parser.add_argument("--validation-id")
    parser.add_argument("--handoff-target")
    parser.add_argument("--exit-code", type=int)
    parser.add_argument("--note")
    parser.add_argument("--command")
    parser.add_argument("--run-id")
    parser.add_argument("--started-at")
    parser.add_argument("--ended-at")
    parser.add_argument("--duration-seconds", type=float)
    parser.add_argument("--slice-kind")
    parser.add_argument("--slice-index", type=int)
    parser.add_argument("--step-id")
    parser.add_argument("--status")
    parser.add_argument("--decision-id")
    parser.add_argument("--decision")
    return parser


def _require_arg(parser: argparse.ArgumentParser, args: argparse.Namespace, field: str) -> str:
    value = getattr(args, field.replace("-", "_"))
    if not value:
        parser.error(f"`--{field}` is required for `{args.event}` events.")
    return value


def build_payload(
    parser: argparse.ArgumentParser, args: argparse.Namespace
) -> dict[str, object]:
    payload: dict[str, object] = {"event": args.event, "task": args.task}

    if args.run_id:
        payload["run_id"] = args.run_id
    if args.started_at:
        payload["started_at"] = args.started_at
    if args.ended_at:
        payload["ended_at"] = args.ended_at
    if args.duration_seconds is not None:
        payload["duration_seconds"] = args.duration_seconds

    if args.event.startswith("validation_"):
        payload["validation_id"] = _require_arg(parser, args, "validation-id")
        payload["command"] = _require_arg(parser, args, "command")
        if args.exit_code is None:
            parser.error(f"`--exit-code` is required for `{args.event}` events.")
        payload["exit_code"] = args.exit_code
    elif args.event in {"contract_satisfied", "handoff_ready"}:
        payload["handoff_target"] = _require_arg(parser, args, "handoff-target")
    elif args.event in {"contract_failed", "task_incomplete"}:
        if args.note:
            payload["note"] = args.note
    elif args.event == "run_slice_completed":
        payload["slice_kind"] = _require_arg(parser, args, "slice-kind")
        if args.slice_index is None:
            parser.error("`--slice-index` is required for `run_slice_completed` events.")
        if args.exit_code is None:
            parser.error("`--exit-code` is required for `run_slice_completed` events.")
        payload["slice_index"] = args.slice_index
        payload["exit_code"] = args.exit_code
    elif args.event == "runner_step_completed":
        payload["step_id"] = _require_arg(parser, args, "step-id")
        payload["status"] = _require_arg(parser, args, "status")
    elif args.event == "runner_decision":
        payload["decision_id"] = _require_arg(parser, args, "decision-id")
        payload["decision"] = _require_arg(parser, args, "decision")
        if args.slice_index is not None:
            payload["slice_index"] = args.slice_index

    if args.note and args.event not in {"contract_failed", "task_incomplete"}:
        payload["note"] = args.note

    return payload


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        repo_root = Path(args.repo_root).resolve()
        task_dir = task_dir_for_slug(repo_root, args.task)
    except ContractError as exc:
        parser.error(str(exc))

    try:
        require_initialized_task_dir(task_dir)
    except ContractError as exc:
        parser.error(str(exc))

    payload = build_payload(parser, args)

    try:
        events_path = append_event(task_dir, payload)
    except ContractError as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, sort_keys=True))
        return 1

    print(json.dumps({"ok": True, "events_path": str(events_path)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
