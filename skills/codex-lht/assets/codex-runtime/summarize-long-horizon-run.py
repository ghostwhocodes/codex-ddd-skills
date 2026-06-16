#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from task_contract import (
    ContractError,
    load_events,
    repo_root_for_runtime_path,
    task_dir_for_slug,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Summarize timing and execution stats for an internal CodexLHT run."
    )
    parser.add_argument("--task", required=True, help="Task slug under ai/tasks/<slug>.")
    parser.add_argument(
        "--repo-root",
        default=str(repo_root_for_runtime_path(Path(__file__))),
        help="Repository root. Defaults to the Git repository containing this runtime.",
    )
    parser.add_argument("--run-id", help="Optional run identifier to filter events.")
    parser.add_argument("--run-started-at", help="Optional wrapper start timestamp.")
    parser.add_argument("--run-ended-at", help="Optional wrapper end timestamp.")
    parser.add_argument(
        "--run-duration-seconds",
        type=float,
        help="Optional wrapper wall-clock duration in seconds.",
    )
    parser.add_argument("--rollout-path", help="Optional rollout JSONL file to inspect.")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a machine-readable JSON summary instead of human text.",
    )
    return parser


def parse_timestamp(raw: str | None) -> datetime | None:
    if not raw:
        return None
    normalized = raw.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def parse_float(value: Any) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


def parse_int(value: Any) -> int | None:
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            return None
    return None


def sum_durations(events: list[dict[str, Any]]) -> float:
    total = 0.0
    for event in events:
        duration = parse_float(event.get("duration_seconds"))
        if duration is not None and duration >= 0:
            total += duration
    return total


def format_duration(seconds: float) -> str:
    rounded = max(0, int(round(seconds)))
    hours, remainder = divmod(rounded, 3600)
    minutes, secs = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def inspect_rollout(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "path": None,
            "exists": False,
            "entry_count": 0,
            "task_complete_markers": 0,
            "started_at": None,
            "ended_at": None,
            "last_primary_rate_limit_used_percent": None,
        }

    summary: dict[str, Any] = {
        "path": str(path),
        "exists": path.is_file(),
        "entry_count": 0,
        "task_complete_markers": 0,
        "started_at": None,
        "ended_at": None,
        "last_primary_rate_limit_used_percent": None,
    }
    if not path.is_file():
        return summary

    with path.open(encoding="utf-8") as handle:
        for raw_line in handle:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                payload = json.loads(raw_line)
            except json.JSONDecodeError:
                continue

            summary["entry_count"] += 1
            timestamp = payload.get("timestamp")
            if isinstance(timestamp, str):
                if summary["started_at"] is None:
                    summary["started_at"] = timestamp
                summary["ended_at"] = timestamp

            entry_type = payload.get("type")
            nested_type = payload.get("payload", {}).get("type")
            if entry_type == "task_complete" or nested_type == "task_complete":
                summary["task_complete_markers"] += 1

            if nested_type == "token_count":
                primary = (
                    payload.get("payload", {})
                    .get("rate_limits", {})
                    .get("primary", {})
                    .get("used_percent")
                )
                if isinstance(primary, (int, float)):
                    summary["last_primary_rate_limit_used_percent"] = float(primary)

    return summary


def filter_run_events(
    events: list[dict[str, Any]],
    *,
    run_id: str | None,
    run_started_at: datetime | None,
    run_ended_at: datetime | None,
) -> list[dict[str, Any]]:
    if run_id:
        matching = [event for event in events if event.get("run_id") == run_id]
        if matching:
            return matching

    if run_started_at is None:
        return events

    filtered: list[dict[str, Any]] = []
    for event in events:
        event_ts = parse_timestamp(event.get("ts"))
        if event_ts is None:
            continue
        if event_ts < run_started_at:
            continue
        if run_ended_at is not None and event_ts > run_ended_at:
            continue
        filtered.append(event)
    return filtered


def build_summary(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = Path(args.repo_root).resolve()
    task_dir = task_dir_for_slug(repo_root, args.task)
    if not task_dir.is_dir():
        raise ContractError(f"Task directory does not exist: {task_dir}")

    events = load_events(task_dir)
    run_started_at = parse_timestamp(args.run_started_at)
    run_ended_at = parse_timestamp(args.run_ended_at)
    filtered_events = filter_run_events(
        events,
        run_id=args.run_id,
        run_started_at=run_started_at,
        run_ended_at=run_ended_at,
    )

    validation_events = [
        event for event in filtered_events if event["event"].startswith("validation_")
    ]
    slice_events = [
        event for event in filtered_events if event["event"] == "run_slice_completed"
    ]
    runner_step_events = [
        event for event in filtered_events if event["event"] == "runner_step_completed"
    ]

    slice_events.sort(
        key=lambda event: (
            parse_int(event.get("slice_index"))
            if parse_int(event.get("slice_index")) is not None
            else math.inf,
            event.get("started_at", ""),
        )
    )

    validation_by_id: dict[str, dict[str, Any]] = {}
    for event in validation_events:
        validation_id = str(event.get("validation_id", "unknown"))
        bucket = validation_by_id.setdefault(
            validation_id,
            {
                "validation_id": validation_id,
                "count": 0,
                "passed_count": 0,
                "failed_count": 0,
                "total_seconds": 0.0,
                "last_exit_code": None,
                "last_command": None,
            },
        )
        bucket["count"] += 1
        bucket["total_seconds"] += max(
            0.0, parse_float(event.get("duration_seconds")) or 0.0
        )
        if event["event"] == "validation_passed":
            bucket["passed_count"] += 1
        else:
            bucket["failed_count"] += 1
        bucket["last_exit_code"] = event.get("exit_code")
        bucket["last_command"] = event.get("command")

    runner_steps_by_id: dict[str, dict[str, Any]] = {}
    for event in runner_step_events:
        step_id = str(event.get("step_id", "unknown"))
        bucket = runner_steps_by_id.setdefault(
            step_id,
            {
                "step_id": step_id,
                "count": 0,
                "failed_count": 0,
                "total_seconds": 0.0,
            },
        )
        bucket["count"] += 1
        bucket["total_seconds"] += max(
            0.0, parse_float(event.get("duration_seconds")) or 0.0
        )
        if event.get("status") != "success":
            bucket["failed_count"] += 1

    slice_kind_counts = Counter(str(event.get("slice_kind", "unknown")) for event in slice_events)
    codex_total_seconds = sum_durations(slice_events)
    validation_total_seconds = sum_durations(validation_events)
    runner_step_total_seconds = sum_durations(runner_step_events)
    execution_seconds = max(0.0, codex_total_seconds - validation_total_seconds)

    wall_clock_seconds = args.run_duration_seconds
    if wall_clock_seconds is None and run_started_at is not None and run_ended_at is not None:
        wall_clock_seconds = max(0.0, (run_ended_at - run_started_at).total_seconds())
    if wall_clock_seconds is None:
        timestamps: list[datetime] = []
        for event in filtered_events:
            for key in ("started_at", "ended_at", "ts"):
                parsed = parse_timestamp(event.get(key))
                if parsed is not None:
                    timestamps.append(parsed)
        if timestamps:
            wall_clock_seconds = max(0.0, (max(timestamps) - min(timestamps)).total_seconds())
        else:
            wall_clock_seconds = 0.0

    wrapper_overhead_seconds = max(
        0.0, wall_clock_seconds - codex_total_seconds - runner_step_total_seconds
    )

    run_event_counts = Counter(
        event["event"]
        for event in filtered_events
        if event["event"]
        in {
            "task_incomplete",
            "contract_failed",
            "contract_satisfied",
            "handoff_ready",
        }
    )

    rollout_summary = inspect_rollout(Path(args.rollout_path) if args.rollout_path else None)

    self_improvement_reasons: list[str] = []
    failed_validation_count = sum(
        1 for event in validation_events if event["event"] == "validation_failed"
    )
    resume_slice_count = slice_kind_counts.get("resume", 0)
    if failed_validation_count > 0:
        self_improvement_reasons.append("validation retries or failures occurred")
    if resume_slice_count > 0:
        self_improvement_reasons.append("resume slices were required to finish or progress")
    if len(slice_events) >= 3:
        self_improvement_reasons.append("the run needed at least three execution slices")
    if run_event_counts["task_incomplete"] > 0 or run_event_counts["contract_failed"] > 0:
        self_improvement_reasons.append("closeout or contract churn was recorded")
    if codex_total_seconds >= 900 and execution_seconds >= max(300.0, validation_total_seconds * 2):
        self_improvement_reasons.append(
            "codex spent a large amount of time outside recorded validation commands"
        )
    if wall_clock_seconds >= 1800 and not validation_events:
        self_improvement_reasons.append(
            "the run was long but did not record contract-scoped validation commands"
        )

    slices_summary = []
    for event in slice_events:
        slices_summary.append(
            {
                "slice_index": event.get("slice_index"),
                "slice_kind": event.get("slice_kind"),
                "exit_code": event.get("exit_code"),
                "started_at": event.get("started_at"),
                "ended_at": event.get("ended_at"),
                "duration_seconds": parse_float(event.get("duration_seconds")) or 0.0,
            }
        )

    return {
        "task": args.task,
        "run_id": args.run_id,
        "event_count": len(filtered_events),
        "wall_clock_seconds": wall_clock_seconds,
        "codex": {
            "slice_count": len(slice_events),
            "slice_kind_counts": dict(slice_kind_counts),
            "nonzero_exit_slices": sum(
                1 for event in slice_events if int(event.get("exit_code", 0)) != 0
            ),
            "total_seconds": codex_total_seconds,
            "execution_seconds": execution_seconds,
            "validation_seconds": validation_total_seconds,
        },
        "validation": {
            "total_count": len(validation_events),
            "passed_count": sum(
                1 for event in validation_events if event["event"] == "validation_passed"
            ),
            "failed_count": failed_validation_count,
            "total_seconds": validation_total_seconds,
            "by_validation_id": sorted(
                validation_by_id.values(), key=lambda item: item["validation_id"]
            ),
        },
        "runner_steps": {
            "total_count": len(runner_step_events),
            "failed_count": sum(
                1 for event in runner_step_events if event.get("status") != "success"
            ),
            "total_seconds": runner_step_total_seconds,
            "by_step_id": sorted(runner_steps_by_id.values(), key=lambda item: item["step_id"]),
        },
        "wrapper": {
            "overhead_seconds": wrapper_overhead_seconds,
        },
        "run_events": {
            "task_incomplete_count": run_event_counts["task_incomplete"],
            "contract_failed_count": run_event_counts["contract_failed"],
            "contract_satisfied_count": run_event_counts["contract_satisfied"],
            "handoff_ready_count": run_event_counts["handoff_ready"],
        },
        "rollout": rollout_summary,
        "self_improvement_analysis": {
            "worthwhile": bool(self_improvement_reasons),
            "reasons": self_improvement_reasons,
        },
        "slices": slices_summary,
    }


def print_human_summary(summary: dict[str, Any]) -> None:
    codex = summary["codex"]
    validation = summary["validation"]
    runner_steps = summary["runner_steps"]
    rollout = summary["rollout"]
    self_improvement = summary["self_improvement_analysis"]

    print(f"Run summary for {summary['task']} ({summary.get('run_id') or 'unscoped'})")
    print(
        "Wall clock: "
        f"{format_duration(summary['wall_clock_seconds'])} "
        f"({summary['wall_clock_seconds']:.1f}s)"
    )
    print(
        "Codex runtime: "
        f"{format_duration(codex['total_seconds'])} across {codex['slice_count']} slice(s); "
        f"validation {format_duration(codex['validation_seconds'])}, "
        f"execution {format_duration(codex['execution_seconds'])}"
    )
    print(
        "Validation commands: "
        f"{validation['total_count']} total, {validation['passed_count']} passed, "
        f"{validation['failed_count']} failed"
    )
    print(
        "Finalize steps: "
        f"{runner_steps['total_count']} total, "
        f"{runner_steps['failed_count']} failed, "
        f"{format_duration(runner_steps['total_seconds'])}"
    )
    print(
        "Wrapper overhead: "
        f"{format_duration(summary['wrapper']['overhead_seconds'])}"
    )

    if summary["slices"]:
        print("Execution slices:")
        for slice_summary in summary["slices"]:
            print(
                f"{slice_summary['slice_index']}. "
                f"{slice_summary['slice_kind']} "
                f"exit={slice_summary['exit_code']} "
                f"duration={format_duration(slice_summary['duration_seconds'])}"
            )

    if validation["by_validation_id"]:
        print("Validation breakdown:")
        for bucket in validation["by_validation_id"]:
            print(
                f"- {bucket['validation_id']}: "
                f"{bucket['count']} run(s), "
                f"{bucket['failed_count']} failed, "
                f"{format_duration(bucket['total_seconds'])}"
            )

    if runner_steps["by_step_id"]:
        print("Finalize breakdown:")
        for bucket in runner_steps["by_step_id"]:
            print(
                f"- {bucket['step_id']}: "
                f"{bucket['count']} run(s), "
                f"{bucket['failed_count']} failed, "
                f"{format_duration(bucket['total_seconds'])}"
            )

    if rollout["path"]:
        rollout_line = (
            f"Rollout: {rollout['path']} "
            f"(entries={rollout['entry_count']}, task_complete_markers={rollout['task_complete_markers']})"
        )
        if rollout["last_primary_rate_limit_used_percent"] is not None:
            rollout_line += (
                f", last_primary_rate_limit_used_percent="
                f"{rollout['last_primary_rate_limit_used_percent']:.1f}"
            )
        print(rollout_line)

    if self_improvement["worthwhile"]:
        print(
            "Self-improvement analysis: worthwhile; reasons: "
            + "; ".join(self_improvement["reasons"])
        )
    else:
        print("Self-improvement analysis: not flagged")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        summary = build_summary(args)
    except ContractError as exc:
        payload = {"ok": False, "errors": [str(exc)]}
        print(json.dumps(payload, sort_keys=True))
        return 1

    if args.json:
        print(json.dumps({"ok": True, "summary": summary}, sort_keys=True))
    else:
        print_human_summary(summary)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
