#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from task_contract import (
    CLOSEOUT_PATTERN,
    ContractError,
    HANDOFF_EVENTS,
    REQUIREMENT_EVENTS,
    REVIEW_EVENTS,
    append_events,
    canonicalize_event_payload,
    event_payload,
    load_contract,
    normalize_event,
    parse_events_text,
    repo_root_for_runtime_path,
    require_initialized_task_dir,
    task_dir_for_slug,
    wrapper_review_blockers,
)

REQUIREMENT_STATUSES = {"pending", "satisfied", "unsatisfied"}
REVIEW_STATUSES = {"pending", "passed", "blocking"}
CLOSEOUT_EVENT_TYPES = REQUIREMENT_EVENTS | REVIEW_EVENTS | HANDOFF_EVENTS


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Parse ai/tasks/<slug>/Closeout.md and append wrapper-owned "
            "requirement, review, and handoff events."
        )
    )
    parser.add_argument("--task", required=True, help="Task slug under ai/tasks/<slug>.")
    parser.add_argument(
        "--repo-root",
        default=str(repo_root_for_runtime_path(Path(__file__))),
        help="Repository root. Defaults to the Git repository containing this runtime.",
    )
    return parser


def _extract_machine_closeout(text: str) -> dict[str, Any]:
    match = CLOSEOUT_PATTERN.search(text)
    if match is None:
        raise ContractError("Missing `## Machine Closeout` JSON block in Closeout.md.")
    try:
        payload = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise ContractError(f"Machine closeout JSON is invalid: {exc}.") from exc
    if not isinstance(payload, dict):
        raise ContractError("Machine closeout must decode to a JSON object.")
    return payload


def _require_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"`{field_name}` must be a non-empty string.")
    return value.strip()


def _normalize_status_items(
    items: Any,
    id_field: str,
    allowed_statuses: set[str],
    field_name: str,
) -> list[dict[str, str]]:
    if not isinstance(items, list):
        raise ContractError(f"`{field_name}` must be a list.")

    normalized: list[dict[str, str]] = []
    seen_ids: set[str] = set()
    for entry in items:
        if not isinstance(entry, dict):
            raise ContractError(f"Each `{field_name}` entry must be an object.")
        item_id = _require_string(entry.get(id_field), id_field)
        if item_id in seen_ids:
            raise ContractError(f"`{field_name}` contains duplicate `{item_id}` entries.")
        status = _require_string(entry.get("status"), "status")
        if status not in allowed_statuses:
            raise ContractError(
                f"`{field_name}` entry `{item_id}` has unsupported status `{status}`."
            )
        summary = entry.get("summary", "")
        if summary is None:
            summary = ""
        if not isinstance(summary, str):
            raise ContractError(
                f"`{field_name}` entry `{item_id}` has non-string `summary`."
            )
        normalized.append(
            {
                id_field: item_id,
                "status": status,
                "summary": summary.strip(),
            }
        )
        seen_ids.add(item_id)
    return normalized


def load_closeout(task_dir: Path, contract: dict[str, Any]) -> dict[str, Any]:
    closeout_path = task_dir / "Closeout.md"
    if not closeout_path.is_file():
        raise ContractError(f"Missing closeout file: {closeout_path}.")

    payload = _extract_machine_closeout(closeout_path.read_text(encoding="utf-8"))
    schema_version = payload.get("schema_version")
    if schema_version != 1:
        raise ContractError(
            f"Unsupported machine closeout schema_version `{schema_version}`."
        )

    requirements = _normalize_status_items(
        payload.get("requirements"),
        "requirement_id",
        REQUIREMENT_STATUSES,
        "requirements",
    )
    reviews = _normalize_status_items(
        payload.get("reviews"),
        "review_id",
        REVIEW_STATUSES,
        "reviews",
    )
    handoff_target = _require_string(payload.get("handoff_target"), "handoff_target")
    summary = payload.get("summary", "")
    if summary is None:
        summary = ""
    if not isinstance(summary, str):
        raise ContractError("`summary` must be a string when provided.")

    requirement_ids = {entry["requirement_id"] for entry in requirements}
    missing_requirements = [
        requirement_id
        for requirement_id in contract["requirement_ids"]
        if requirement_id not in requirement_ids
    ]
    if missing_requirements:
        raise ContractError(
            "Closeout.md is missing requirement entries for: "
            + ", ".join(f"`{item}`" for item in missing_requirements)
            + "."
        )

    unexpected_requirements = sorted(
        requirement_ids.difference(contract["requirement_ids"])
    )
    if unexpected_requirements:
        raise ContractError(
            "Closeout.md has unexpected requirement entries: "
            + ", ".join(f"`{item}`" for item in unexpected_requirements)
            + "."
        )

    review_ids = {entry["review_id"] for entry in reviews}
    missing_reviews = [
        review_id for review_id in contract["review_ids"] if review_id not in review_ids
    ]
    if missing_reviews:
        raise ContractError(
            "Closeout.md is missing review entries for: "
            + ", ".join(f"`{item}`" for item in missing_reviews)
            + "."
        )

    unexpected_reviews = sorted(review_ids.difference(contract["review_ids"]))
    if unexpected_reviews:
        raise ContractError(
            "Closeout.md has unexpected review entries: "
            + ", ".join(f"`{item}`" for item in unexpected_reviews)
            + "."
        )

    pending_requirements = [
        entry["requirement_id"] for entry in requirements if entry["status"] == "pending"
    ]
    if pending_requirements:
        raise ContractError(
            "Closeout.md still has pending requirements: "
            + ", ".join(f"`{item}`" for item in pending_requirements)
            + "."
        )

    pending_reviews = [
        entry["review_id"] for entry in reviews if entry["status"] == "pending"
    ]
    if pending_reviews:
        raise ContractError(
            "Closeout.md still has pending reviews: "
            + ", ".join(f"`{item}`" for item in pending_reviews)
            + "."
        )

    return {
        "schema_version": schema_version,
        "requirements": requirements,
        "reviews": reviews,
        "handoff_target": handoff_target,
        "summary": summary.strip(),
    }


def _closeout_id(payload: dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def _expected_closeout_events(closeout: dict[str, Any], closeout_id: str) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []

    for requirement in closeout["requirements"]:
        event_name = (
            "requirement_satisfied"
            if requirement["status"] == "satisfied"
            else "requirement_unsatisfied"
        )
        payload: dict[str, object] = {
            "event": event_name,
            "requirement_id": requirement["requirement_id"],
            "closeout_id": closeout_id,
        }
        if requirement["summary"]:
            payload["note"] = requirement["summary"]
        events.append(payload)

    for review in closeout["reviews"]:
        payload = {
            "event": "review_passed" if review["status"] == "passed" else "review_blocking",
            "review_id": review["review_id"],
            "closeout_id": closeout_id,
        }
        if review["summary"]:
            payload["note"] = review["summary"]
        events.append(payload)

    handoff_payload: dict[str, object] = {
        "event": "handoff_requested",
        "handoff_target": closeout["handoff_target"],
        "closeout_id": closeout_id,
    }
    if closeout["summary"]:
        handoff_payload["note"] = closeout["summary"]
    events.append(handoff_payload)

    return events


def _append_missing_closeout_events(
    task_dir: Path,
    closeout_id: str,
    expected_events: list[dict[str, object]],
) -> None:
    events_path = task_dir / "events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)

    expected_by_key: dict[str, dict[str, object]] = {}
    expected_keys: list[str] = []
    for payload in expected_events:
        key = canonicalize_event_payload(payload)
        if key in expected_by_key:
            raise ContractError(
                f"Closeout `{closeout_id}` produced duplicate expected events."
            )
        expected_by_key[key] = payload
        expected_keys.append(key)

    with events_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.seek(0)
        existing_events = parse_events_text(handle.read())
        blockers = wrapper_review_blockers(task_dir, existing_events)
        if blockers:
            raise ContractError(
                "Wrapper review state still blocks closeout sync: "
                + " ".join(blockers)
            )

        recorded_keys: set[str] = set()
        latest_closeout_id: str | None = None
        for event in existing_events:
            event_closeout_id = event.get("closeout_id")
            if (
                event["event"] in CLOSEOUT_EVENT_TYPES
                and isinstance(event_closeout_id, str)
                and event_closeout_id
            ):
                latest_closeout_id = event_closeout_id
            if event_closeout_id != closeout_id:
                continue
            key = canonicalize_event_payload(event_payload(event))
            if key not in expected_by_key:
                raise ContractError(
                    f"Closeout `{closeout_id}` already has unexpected recorded events."
                )
            recorded_keys.add(key)

        missing_payloads = [
            expected_by_key[key] for key in expected_keys if key not in recorded_keys
        ]
        payloads_to_append = missing_payloads
        if not payloads_to_append and latest_closeout_id != closeout_id:
            payloads_to_append = expected_events
        if not payloads_to_append:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            return

        handle.seek(0, 2)
        timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        for payload in payloads_to_append:
            serialized = json.dumps(normalize_event(payload, ts=timestamp), sort_keys=True)
            handle.write(serialized)
            handle.write("\n")
        handle.flush()
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def sync_closeout(task_dir: Path) -> dict[str, Any]:
    contract = load_contract(task_dir)
    closeout = load_closeout(task_dir, contract)
    closeout_id = _closeout_id(closeout)
    expected_events = _expected_closeout_events(closeout, closeout_id)
    _append_missing_closeout_events(task_dir, closeout_id, expected_events)

    return {
        "ok": True,
        "closeout_id": closeout_id,
        "handoff_target": closeout["handoff_target"],
        "task_dir": str(task_dir),
    }


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    try:
        repo_root = Path(args.repo_root).resolve()
        task_dir = task_dir_for_slug(repo_root, args.task)
        require_initialized_task_dir(task_dir)
        result = sync_closeout(task_dir)
    except ContractError as exc:
        print(json.dumps({"ok": False, "errors": [str(exc)]}, sort_keys=True))
        return 1

    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
