#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import re
import shlex
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from task_contract import CLOSEOUT_PATTERN, ContractError, require_initialized_task_dir

MARKERS = {
    "overall_state": (
        "<!-- WRAPPER_OVERALL_STATE:BEGIN -->",
        "<!-- WRAPPER_OVERALL_STATE:END -->",
    ),
    "merge_review": (
        "<!-- WRAPPER_MERGE_REVIEW_STATE:BEGIN -->",
        "<!-- WRAPPER_MERGE_REVIEW_STATE:END -->",
    ),
    "closeout_verification": (
        "<!-- WRAPPER_CLOSEOUT_VERIFICATION:BEGIN -->",
        "<!-- WRAPPER_CLOSEOUT_VERIFICATION:END -->",
    ),
    "next_action": (
        "<!-- WRAPPER_NEXT_ACTION:BEGIN -->",
        "<!-- WRAPPER_NEXT_ACTION:END -->",
    ),
    "closeout_review_summary": (
        "<!-- WRAPPER_CLOSEOUT_REVIEW_SUMMARY:BEGIN -->",
        "<!-- WRAPPER_CLOSEOUT_REVIEW_SUMMARY:END -->",
    ),
    "closeout_handoff": (
        "<!-- WRAPPER_CLOSEOUT_HANDOFF:BEGIN -->",
        "<!-- WRAPPER_CLOSEOUT_HANDOFF:END -->",
    ),
}

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Refresh wrapper-owned review state across task-local closeout and "
            "documentation surfaces."
        )
    )
    parser.add_argument("--task-dir", required=True, help="Absolute or relative task directory path.")
    parser.add_argument(
        "--status",
        required=True,
        choices=("success", "findings"),
        help="Wrapper review outcome to record.",
    )
    parser.add_argument(
        "--timestamp",
        help="ISO-8601 UTC timestamp to record. Defaults to the current UTC time.",
    )
    parser.add_argument(
        "--review-output",
        help="Wrapper review JSON output path. Required for `--status findings`.",
    )
    return parser


def _timestamp(value: str | None) -> str:
    if value:
        return _canonical_utc_timestamp(value)
    return _render_utc_timestamp(datetime.now(timezone.utc).replace(microsecond=0))


def _parse_timestamp(value: str) -> datetime:
    normalized = value.strip()
    if not normalized:
        raise SystemExit("Timestamp must not be empty.")
    try:
        parsed = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SystemExit(
            f"Timestamp must be a valid ISO-8601 timestamp, got {value!r}."
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _render_utc_timestamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _canonical_utc_timestamp(value: str) -> str:
    return _render_utc_timestamp(_parse_timestamp(value))


def _load_machine_closeout(closeout_path: Path) -> tuple[str, dict[str, Any], tuple[int, int]]:
    closeout_text = closeout_path.read_text(encoding="utf-8")
    match = CLOSEOUT_PATTERN.search(closeout_text)
    if match is None:
        raise SystemExit("Closeout.md is missing `## Machine Closeout` JSON block.")
    closeout = json.loads(match.group(1))
    if not isinstance(closeout, dict):
        raise SystemExit("Closeout.md machine closeout must decode to a JSON object.")
    return closeout_text, closeout, match.span(1)


def _replace_marked_block(text: str, marker_name: str, body: str) -> str:
    start_marker, end_marker = MARKERS[marker_name]
    pattern = re.compile(
        rf"{re.escape(start_marker)}\n.*?\n{re.escape(end_marker)}",
        re.DOTALL,
    )
    replacement = f"{start_marker}\n{body.rstrip()}\n{end_marker}"
    updated_text, count = pattern.subn(replacement, text, count=1)
    if count != 1:
        raise SystemExit(
            f"Missing wrapper-managed block `{start_marker}` / `{end_marker}`."
        )
    return updated_text


def _replace_required_marked_block(text: str, marker_name: str, body: str) -> str:
    return _replace_marked_block(text, marker_name, body)


def _task_slug(task_dir: Path) -> str:
    return task_dir.name


def _review_resume_text(payload: dict[str, Any], timestamp: str) -> str:
    findings = payload.get("material_findings")
    if not isinstance(findings, list):
        findings = []

    lines = [
        "# Review Resume",
        "",
        f"Generated: {timestamp}",
        "",
        "Status: material findings from the wrapper-owned read-only review.",
        "",
        "## Coding Agent Guidance",
        "",
        "- Step back before patching the reported locations.",
        "- Identify broader patterns, missing invariants, or test-harness gaps that allowed these findings to appear.",
        "- Prefer upstream fixes, contract/test-harness improvements, or invariant-preserving changes over narrow line-local patches unless the evidence proves a local patch is the correct fix.",
        "",
    ]
    if findings:
        lines.append("## Material Findings")
        lines.append("")
        for finding in findings:
            if not isinstance(finding, dict):
                lines.append(f"- {finding}")
                continue
            severity = finding.get("severity") or "P?"
            title = finding.get("title") or "Untitled finding"
            file_path = finding.get("file") or "unknown file"
            line = finding.get("line")
            location = file_path if line is None else f"{file_path}:{line}"
            body = finding.get("body") or ""
            recommendation = finding.get("recommendation") or ""
            detail = f"- [{severity}] {title} - {location}"
            if body:
                detail += f": {body}"
            if recommendation:
                detail += f" Recommendation: {recommendation}"
            lines.append(detail)
    else:
        lines.extend(["## Material Findings", "", "- Review reported findings without structured details."])

    summary = payload.get("summary")
    if isinstance(summary, str) and summary.strip():
        lines.extend(["", "## Summary", "", summary.strip()])

    residual_risks = payload.get("residual_risks")
    if isinstance(residual_risks, list) and residual_risks:
        lines.extend(["", "## Residual Risks", ""])
        for risk in residual_risks:
            lines.append(f"- {risk}")

    lines.extend(
        [
            "",
            "## Next",
            "",
            "Keep closeout review evidence pending, fix these findings, rerun validation, and review again.",
        ]
    )
    return "\n".join(lines) + "\n"


def _parse_review_output(path: Path) -> tuple[dict[str, Any], str]:
    raw = path.read_text(encoding="utf-8").strip()
    if raw.startswith("```"):
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", raw, flags=re.DOTALL)
        if match is not None:
            raw = match.group(1).strip()
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise SystemExit("Wrapper review output must decode to a JSON object.")
    return payload, raw


def _wrapper_review_closeout_id(timestamp: str, raw_review_output: str) -> str:
    return "wrapper-review-" + hashlib.sha256(
        (timestamp + "\n" + raw_review_output).encode("utf-8")
    ).hexdigest()[:16]


def _update_machine_closeout(
    closeout: dict[str, Any],
    *,
    status: str,
    timestamp: str,
) -> None:
    reviews = closeout.get("reviews")
    if not isinstance(reviews, list) or not reviews:
        raise SystemExit("Closeout.md machine closeout is missing review entries.")

    updated = False
    for review in reviews:
        if not isinstance(review, dict):
            continue
        if review.get("review_id") != "merge_readiness":
            continue
        if status == "success":
            review["status"] = "passed"
            review["summary"] = f"Authoritative clean wrapper review passed on {timestamp}."
        else:
            review["status"] = "pending"
            review["summary"] = (
                f"Wrapper review found material findings on {timestamp}; see ReviewResume.md."
            )
        updated = True

    if not updated:
        raise SystemExit(
            "Closeout.md machine closeout is missing `merge_readiness` review entry."
        )


def _runtime_command(script_name: str) -> str:
    command_prefix_shell = os.environ.get("CODEXLHT_RUNTIME_COMMAND_PREFIX_SHELL")
    if command_prefix_shell is not None:
        return f"{command_prefix_shell}/{script_name}"
    command_prefix = os.environ.get("CODEXLHT_RUNTIME_COMMAND_PREFIX")
    if command_prefix is None:
        runtime_root_rel = os.environ.get("CODEXLHT_RUNTIME_ROOT_REL", "codex")
        command_prefix = f"./{runtime_root_rel}" if runtime_root_rel else str(Path(__file__).resolve().parent)
    return f"{shlex.quote(command_prefix)}/{script_name}"


def _render_blocks(task_slug: str, timestamp: str, status: str) -> dict[str, str]:
    check_contract = _runtime_command("check-contract.py")
    sync_closeout = _runtime_command("sync-task-closeout.py")

    if status == "success":
        return {
            "overall_state": (
                "- Overall state: The authoritative wrapper-owned clean review passed "
                f"on {timestamp}. Machine `merge_readiness` is restored to `passed`, "
                "and the active wrapper should now sync `Closeout.md` plus rerun "
                f"`python3 {check_contract} --task {task_slug} --pretty` "
                "sequentially for this repaired tree."
            ),
            "merge_review": (
                "- Merge-readiness is locally and wrapper-clean as of "
                f"{timestamp}. No new material product, lifecycle, or contract "
                "findings remain on the current repaired tree."
            ),
            "closeout_verification": (
                "- Wrapper-owned closeout sync is now the remaining gate. The "
                f"authoritative clean review passed on {timestamp}, `ReviewResume.md` "
                "is being cleared from the repair loop, machine `merge_readiness` "
                "is `passed`, and the active wrapper can now sync `Closeout.md` "
                f"and rerun `python3 {check_contract} --task {task_slug} "
                "--pretty` sequentially."
            ),
            "next_action": (
                "- Let the active wrapper finish "
                f"`python3 {sync_closeout} --task {task_slug}` and then "
                f"rerun `python3 {check_contract} --task {task_slug} "
                "--pretty` sequentially for this clean reviewed tree."
            ),
            "closeout_review_summary": (
                "- Wrapper-owned review state: the authoritative clean wrapper "
                f"review passed on {timestamp}. No blocking findings remain on the "
                "current repaired tree, and the refreshed machine "
                "`merge_readiness` entry is ready for closeout sync."
            ),
            "closeout_handoff": (
                "- Wrapper-owned handoff state: ready for wrapper-owned closeout "
                f"sync toward `local_complete` based on the clean authoritative "
                f"review from {timestamp}."
            ),
        }

    return {
        "overall_state": (
            "- Overall state: Wrapper-owned review is still pending after material "
            f"findings were recorded on {timestamp}. `ReviewResume.md` is active, "
            "machine `merge_readiness` stays `pending`, and closeout sync / "
            "contract verification must wait for a clean rerun."
        ),
        "merge_review": (
            "- Merge-readiness remains wrapper-pending after material findings "
            f"recorded on {timestamp}. Treat `ReviewResume.md` as the repair "
            "context for the next pass and step back to the broader invariant "
            "before patching."
        ),
        "closeout_verification": (
            "- Pending at the wrapper-owned boundary. The latest authoritative "
            f"wrapper review recorded findings on {timestamp}, `ReviewResume.md` "
            "is active, machine `merge_readiness` is `pending`, and no fresh "
            "closeout sync should run until the next clean wrapper rerun."
        ),
        "next_action": (
            "- Fix the active `ReviewResume.md` findings, rerun the relevant "
            "validation, and then exit this repair slice so the authoritative "
            "wrapper can rerun its clean read-only review and closeout sync."
        ),
        "closeout_review_summary": (
            "- Wrapper-owned review state: pending clean authoritative wrapper "
            f"review. Material findings were recorded on {timestamp}; see "
            "`ReviewResume.md` and keep machine `merge_readiness` pending until "
            "the next clean rerun."
        ),
        "closeout_handoff": (
            "- Wrapper-owned handoff state: blocked on a clean authoritative "
            "wrapper review and subsequent closeout sync. Do not treat any "
            "earlier `local_complete` snapshot as current while "
            "`ReviewResume.md` remains active."
        ),
    }


def _write_review_blocking_events(
    task_dir: Path,
    *,
    timestamp: str,
    raw_review_output: str,
    closeout: dict[str, Any],
) -> None:
    closeout_id = _wrapper_review_closeout_id(timestamp, raw_review_output)
    reviews = closeout.get("reviews")
    if not isinstance(reviews, list):
        raise SystemExit("Closeout.md machine closeout is missing review entries.")

    events_path = task_dir / "events.jsonl"
    with events_path.open("a+", encoding="utf-8") as events_file:
        fcntl.flock(events_file.fileno(), fcntl.LOCK_EX)
        events_file.seek(0)
        existing_lines = events_file.readlines()
        existing_events: list[dict[str, Any]] = []
        for index, line in enumerate(existing_lines, start=1):
            raw_line = line.strip()
            if not raw_line:
                continue
            try:
                decoded = json.loads(raw_line)
            except json.JSONDecodeError as exc:
                raise SystemExit(
                    f"events.jsonl contains invalid JSON on line {index}: {exc}."
                ) from exc
            if not isinstance(decoded, dict):
                raise SystemExit(
                    f"events.jsonl line {index} must decode to a JSON object."
                )
            existing_events.append(decoded)
        events_file.seek(0, 2)
        for review in reviews:
            if not isinstance(review, dict):
                continue
            review_id = review.get("review_id")
            if not isinstance(review_id, str) or not review_id:
                continue
            if any(
                existing_event.get("event") == "review_blocking"
                and existing_event.get("closeout_id") == closeout_id
                and existing_event.get("review_id") == review_id
                for existing_event in existing_events
            ):
                continue
            event = {
                "schema_version": 1,
                "ts": timestamp,
                "event": "review_blocking",
                "review_id": review_id,
                "closeout_id": closeout_id,
                "note": "Wrapper review found material findings; see ReviewResume.md.",
            }
            events_file.write(json.dumps(event, sort_keys=True) + "\n")
        fcntl.flock(events_file.fileno(), fcntl.LOCK_UN)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    task_dir = Path(args.task_dir).resolve()
    try:
        require_initialized_task_dir(task_dir)
    except ContractError as exc:
        raise SystemExit(str(exc)) from exc
    timestamp = _timestamp(args.timestamp)
    task_slug = _task_slug(task_dir)
    blocks = _render_blocks(task_slug, timestamp, args.status)

    closeout_path = task_dir / "Closeout.md"
    documentation_path = task_dir / "Documentation.md"
    review_resume_path = task_dir / "ReviewResume.md"
    review_resume_text: str | None = None
    raw_review_output: str | None = None

    closeout_text, closeout, closeout_json_span = _load_machine_closeout(closeout_path)
    _update_machine_closeout(closeout, status=args.status, timestamp=timestamp)
    closeout_text = (
        closeout_text[: closeout_json_span[0]]
        + json.dumps(closeout, indent=2)
        + closeout_text[closeout_json_span[1] :]
    )
    closeout_text = _replace_required_marked_block(
        closeout_text, "closeout_review_summary", blocks["closeout_review_summary"]
    )
    closeout_text = _replace_required_marked_block(
        closeout_text, "closeout_handoff", blocks["closeout_handoff"]
    )

    documentation_text = documentation_path.read_text(encoding="utf-8")
    documentation_text = _replace_required_marked_block(
        documentation_text, "overall_state", blocks["overall_state"]
    )
    documentation_text = _replace_required_marked_block(
        documentation_text, "merge_review", blocks["merge_review"]
    )
    documentation_text = _replace_required_marked_block(
        documentation_text,
        "closeout_verification",
        blocks["closeout_verification"],
    )
    documentation_text = _replace_required_marked_block(
        documentation_text, "next_action", blocks["next_action"]
    )

    if args.status == "findings":
        if not args.review_output:
            raise SystemExit("`--review-output` is required when `--status findings`.")
        payload, raw_review_output = _parse_review_output(Path(args.review_output))
        review_resume_text = _review_resume_text(payload, timestamp)

    closeout_path.write_text(closeout_text, encoding="utf-8")
    documentation_path.write_text(documentation_text, encoding="utf-8")

    if args.status == "findings":
        review_resume_path.write_text(review_resume_text, encoding="utf-8")
        _write_review_blocking_events(
            task_dir,
            timestamp=timestamp,
            raw_review_output=raw_review_output,
            closeout=closeout,
        )
    elif review_resume_path.exists():
        review_resume_path.unlink()
    return 0


if __name__ == "__main__":
    sys.exit(main())
