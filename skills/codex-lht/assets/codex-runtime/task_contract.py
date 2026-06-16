#!/usr/bin/env python3
from __future__ import annotations

import fcntl
import fnmatch
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ContractError(RuntimeError):
    pass


MACHINE_CONTRACT_PATTERN = re.compile(
    r"^## Machine Contract\s+```json\n(.*?)\n```",
    re.MULTILINE | re.DOTALL,
)

MACHINE_POLICY_PATTERN = re.compile(
    r"^## Machine Policy\s+```json\n(.*?)\n```",
    re.MULTILINE | re.DOTALL,
)

CLOSEOUT_PATTERN = re.compile(
    r"^## Machine Closeout\s+```json\n(.*?)\n```",
    re.MULTILINE | re.DOTALL,
)

REQUIREMENT_SECTION_PATTERN = re.compile(
    r"^## Requirement IDs\s+(.*?)(?=^## |\Z)",
    re.MULTILINE | re.DOTALL,
)

HANDOFF_SECTION_PATTERN = re.compile(
    r"^## Allowed Handoff Target\s+(.*?)(?=^## |\Z)",
    re.MULTILINE | re.DOTALL,
)

REQUIREMENT_LINE_PATTERN = re.compile(r"^\s*-\s+`([^`]+)`:", re.MULTILINE)
HANDOFF_LINE_PATTERN = re.compile(r"^\s*-\s+`([^`]+)`\s*$", re.MULTILINE)

VALIDATION_EVENTS = {"validation_passed", "validation_failed"}
REVIEW_EVENTS = {"review_passed", "review_blocking"}
REQUIREMENT_EVENTS = {"requirement_satisfied", "requirement_unsatisfied"}
HANDOFF_EVENTS = {"handoff_requested"}
ACTIVE_CLOSEOUT_EVENTS = REQUIREMENT_EVENTS | REVIEW_EVENTS | HANDOFF_EVENTS
WRAPPER_REVIEW_STEP_STATUSES = {"success", "findings", "failed"}
CONTRACT_EVENTS = {
    "contract_satisfied",
    "contract_failed",
    "task_incomplete",
    "handoff_ready",
}
INTERNAL_RUNNER_LOCK_REL_PATH = Path("codex-lht/locks/internal-long-horizon.lock")
TASK_SLUG_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
REQUIRED_TASK_FILE_NAMES = (
    "Prompt.md",
    "Contract.md",
    "Plan.md",
    "Implement.md",
    "Documentation.md",
    "Closeout.md",
    "events.jsonl",
)


def validate_task_slug(task_slug: str) -> str:
    if not TASK_SLUG_PATTERN.fullmatch(task_slug):
        raise ContractError(
            f"Invalid task slug `{task_slug}`. Task slug must be a single path "
            "segment using only ASCII letters, digits, '.', '_' and '-', and must "
            "start with a letter or digit."
        )
    return task_slug


def task_root_for_repo(repo_root: Path) -> Path:
    task_root_rel_raw = os.environ.get("CODEXLHT_TASK_ROOT_REL", "ai/tasks")
    task_root_rel = Path(task_root_rel_raw)
    if task_root_rel.is_absolute():
        raise ContractError(
            f"Task root must be repository-relative: {task_root_rel_raw}."
        )
    if ".." in task_root_rel.parts:
        raise ContractError(
            f"Task root must not contain parent traversal: {task_root_rel_raw}."
        )

    repo_root_real = repo_root.resolve()
    task_root = (repo_root_real / task_root_rel).resolve()
    try:
        task_root.relative_to(repo_root_real)
    except ValueError as exc:
        raise ContractError(
            f"Task root must stay inside repository: {task_root_rel_raw}."
        ) from exc
    return task_root


def task_dir_for_slug(repo_root: Path, task_slug: str) -> Path:
    task_slug = validate_task_slug(task_slug)
    task_root = task_root_for_repo(repo_root)
    task_dir = (task_root / task_slug).resolve()
    try:
        task_dir.relative_to(task_root)
    except ValueError as exc:
        raise ContractError(
            f"Task directory must stay inside task root: {task_dir}."
        ) from exc
    return task_dir


def require_initialized_task_dir(task_dir: Path) -> None:
    if not task_dir.is_dir():
        raise ContractError(f"Task directory does not exist: {task_dir}.")
    for file_name in REQUIRED_TASK_FILE_NAMES:
        task_file = task_dir / file_name
        if not task_file.is_file():
            raise ContractError(f"Missing task file: {task_file}.")


def repo_root_for_task_dir(task_dir: Path) -> Path:
    task_root_rel = Path(os.environ.get("CODEXLHT_TASK_ROOT_REL", "ai/tasks"))
    return task_dir.parents[len(task_root_rel.parts)]


def repo_root_for_runtime_path(runtime_file: Path) -> Path:
    runtime_root = runtime_file.resolve().parent
    for candidate in (runtime_root, *runtime_root.parents):
        if (candidate / ".git").exists():
            return candidate
    return runtime_root.parent


def runtime_root_rel_for_repo(repo_root: Path) -> Path:
    env_rel = os.environ.get("CODEXLHT_RUNTIME_ROOT_REL")
    if env_rel:
        return Path(env_rel)
    runtime_root = Path(__file__).resolve().parent
    try:
        return runtime_root.relative_to(repo_root)
    except ValueError:
        return Path("codex")


def internal_runner_lock_path(repo_root: Path) -> Path:
    env_path = os.environ.get("CODEXLHT_RUNNER_LOCK_PATH")
    if env_path:
        return Path(env_path).expanduser().resolve()
    git_dir = _git_dir(repo_root)
    if git_dir is not None:
        return git_dir / INTERNAL_RUNNER_LOCK_REL_PATH
    return repo_root / "target" / INTERNAL_RUNNER_LOCK_REL_PATH


def internal_runner_lock_paths(repo_root: Path) -> list[Path]:
    return [internal_runner_lock_path(repo_root)]


def _git_dir(repo_root: Path) -> Path | None:
    git_dir = repo_root / ".git"
    if not git_dir.exists():
        return None
    if git_dir.is_dir():
        return git_dir.resolve()
    try:
        content = git_dir.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    prefix = "gitdir:"
    if not content.startswith(prefix):
        return None
    path = Path(content[len(prefix) :].strip())
    if not path.is_absolute():
        path = repo_root / path
    return path.resolve()


def policy_dir_for_id(repo_root: Path, policy_id: str) -> Path:
    return repo_root / "ai" / "policies" / policy_id


def _extract_required_section(
    text: str, pattern: re.Pattern[str], section_name: str
) -> str:
    match = pattern.search(text)
    if match is None:
        raise ContractError(f"Missing `{section_name}` section in Contract.md.")
    return match.group(1)


def _extract_machine_contract(text: str) -> dict[str, Any]:
    match = MACHINE_CONTRACT_PATTERN.search(text)
    if match is None:
        raise ContractError("Missing `## Machine Contract` JSON block in Contract.md.")
    try:
        machine_contract = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise ContractError(f"Machine contract JSON is invalid: {exc}.") from exc
    if not isinstance(machine_contract, dict):
        raise ContractError("Machine contract must decode to a JSON object.")
    return machine_contract


def _extract_machine_policy(text: str) -> dict[str, Any]:
    match = MACHINE_POLICY_PATTERN.search(text)
    if match is None:
        raise ContractError("Missing `## Machine Policy` JSON block in Policy.md.")
    try:
        machine_policy = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise ContractError(f"Machine policy JSON is invalid: {exc}.") from exc
    if not isinstance(machine_policy, dict):
        raise ContractError("Machine policy must decode to a JSON object.")
    return machine_policy


def _require_string_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ContractError(f"`{field_name}` must be a list of strings.")
    if len(set(value)) != len(value):
        raise ContractError(f"`{field_name}` contains duplicate values.")
    return value


def _require_optional_string_list(value: Any, field_name: str) -> list[str]:
    if value is None:
        return []
    return _require_string_list(value, field_name)


def _require_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ContractError(f"`{field_name}` must be a non-empty string.")
    return value.strip()


def _require_structural_guards(value: Any, field_name: str) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ContractError(f"`{field_name}` must be a list of objects.")
    guards: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, guard in enumerate(value):
        guard_name = f"{field_name}[{index}]"
        if not isinstance(guard, dict):
            raise ContractError(f"`{guard_name}` must be an object.")
        guard_id = _require_string(guard.get("guard_id"), f"{guard_name}.guard_id")
        if guard_id in seen:
            raise ContractError(f"`{field_name}` contains duplicate guard `{guard_id}`.")
        seen.add(guard_id)
        include_globs = _require_string_list(
            guard.get("include_globs"), f"{guard_name}.include_globs"
        )
        if not include_globs:
            raise ContractError(f"`{guard_name}.include_globs` must not be empty.")
        exclude_globs = _require_optional_string_list(
            guard.get("exclude_globs"), f"{guard_name}.exclude_globs"
        )
        forbidden_regexes = _require_string_list(
            guard.get("forbidden_regexes"), f"{guard_name}.forbidden_regexes"
        )
        if not forbidden_regexes:
            raise ContractError(f"`{guard_name}.forbidden_regexes` must not be empty.")
        for pattern in forbidden_regexes:
            try:
                re.compile(pattern)
            except re.error as exc:
                raise ContractError(
                    f"`{guard_name}.forbidden_regexes` contains invalid regex `{pattern}`: {exc}."
                ) from exc
        guards.append(
            {
                "guard_id": guard_id,
                "include_globs": include_globs,
                "exclude_globs": exclude_globs,
                "forbidden_regexes": forbidden_regexes,
            }
        )
    return guards


def _merge_id_lists(
    task_ids: list[str],
    policy_chunks: list[tuple[str, list[str]]],
    *,
    field_name: str,
) -> list[str]:
    merged = list(task_ids)
    seen = set(task_ids)
    for policy_id, ids in policy_chunks:
        for item in ids:
            if item in seen:
                raise ContractError(
                    f"`{field_name}` value `{item}` is declared multiple times across the task contract and active policies."
                )
            merged.append(item)
            seen.add(item)
    return merged


def load_policy(policy_dir: Path) -> dict[str, Any]:
    policy_path = policy_dir / "Policy.md"
    if not policy_path.is_file():
        raise ContractError(f"Missing policy file: {policy_path}.")

    machine_policy = _extract_machine_policy(policy_path.read_text(encoding="utf-8"))
    schema_version = machine_policy.get("schema_version")
    if schema_version != 1:
        raise ContractError(
            f"Unsupported machine policy schema_version `{schema_version}` in {policy_path}."
        )

    policy_id = _require_string(machine_policy.get("policy_id"), "policy_id")
    if policy_id != policy_dir.name:
        raise ContractError(
            f"Machine policy id `{policy_id}` does not match policy directory `{policy_dir.name}`."
        )

    requirement_ids = _require_string_list(
        machine_policy.get("requirement_ids"), "requirement_ids"
    )
    validation_ids = _require_string_list(
        machine_policy.get("validation_ids"), "validation_ids"
    )
    review_ids = _require_string_list(machine_policy.get("review_ids"), "review_ids")
    structural_guards = _require_structural_guards(
        machine_policy.get("structural_guards"), "structural_guards"
    )

    return {
        "schema_version": schema_version,
        "policy_id": policy_id,
        "requirement_ids": requirement_ids,
        "validation_ids": validation_ids,
        "review_ids": review_ids,
        "structural_guards": structural_guards,
        "policy_dir": str(policy_dir),
    }


def load_contract(task_dir: Path) -> dict[str, Any]:
    contract_path = task_dir / "Contract.md"
    if not contract_path.is_file():
        raise ContractError(f"Missing contract file: {contract_path}.")

    text = contract_path.read_text(encoding="utf-8")
    machine_contract = _extract_machine_contract(text)

    schema_version = machine_contract.get("schema_version")
    if schema_version != 1:
        raise ContractError(
            f"Unsupported machine contract schema_version `{schema_version}`."
        )

    requirement_ids = _require_string_list(
        machine_contract.get("requirement_ids"), "requirement_ids"
    )
    validation_ids = _require_string_list(
        machine_contract.get("validation_ids"), "validation_ids"
    )
    review_ids = _require_string_list(machine_contract.get("review_ids"), "review_ids")
    allowed_handoff_targets = _require_string_list(
        machine_contract.get("allowed_handoff_targets"), "allowed_handoff_targets"
    )
    policy_ids = _require_optional_string_list(
        machine_contract.get("policy_ids"), "policy_ids"
    )

    prose_requirement_ids = REQUIREMENT_LINE_PATTERN.findall(
        _extract_required_section(text, REQUIREMENT_SECTION_PATTERN, "Requirement IDs")
    )
    if prose_requirement_ids != requirement_ids:
        raise ContractError(
            "Machine contract requirement_ids do not match the `## Requirement IDs` section."
        )

    prose_handoff_targets = HANDOFF_LINE_PATTERN.findall(
        _extract_required_section(
            text, HANDOFF_SECTION_PATTERN, "Allowed Handoff Target"
        )
    )
    if prose_handoff_targets != allowed_handoff_targets:
        raise ContractError(
            "Machine contract allowed_handoff_targets do not match the `## Allowed Handoff Target` section."
        )

    repo_root = repo_root_for_task_dir(task_dir)
    active_policies: list[dict[str, Any]] = []
    seen_policy_ids: set[str] = set()
    for policy_id in policy_ids:
        if policy_id in seen_policy_ids:
            raise ContractError(f"`policy_ids` contains duplicate value `{policy_id}`.")
        active_policies.append(load_policy(policy_dir_for_id(repo_root, policy_id)))
        seen_policy_ids.add(policy_id)

    merged_requirement_ids = _merge_id_lists(
        requirement_ids,
        [
            (policy["policy_id"], policy["requirement_ids"])
            for policy in active_policies
        ],
        field_name="requirement_ids",
    )
    merged_validation_ids = _merge_id_lists(
        validation_ids,
        [
            (policy["policy_id"], policy["validation_ids"])
            for policy in active_policies
        ],
        field_name="validation_ids",
    )
    merged_review_ids = _merge_id_lists(
        review_ids,
        [(policy["policy_id"], policy["review_ids"]) for policy in active_policies],
        field_name="review_ids",
    )
    structural_guards: list[dict[str, Any]] = []
    seen_structural_guards: set[str] = set()
    for policy in active_policies:
        for guard in policy["structural_guards"]:
            guard_key = f"{policy['policy_id']}:{guard['guard_id']}"
            if guard_key in seen_structural_guards:
                raise ContractError(f"Duplicate structural guard `{guard_key}`.")
            structural_guards.append({"policy_id": policy["policy_id"], **guard})
            seen_structural_guards.add(guard_key)

    return {
        "schema_version": schema_version,
        "policy_ids": policy_ids,
        "policies": active_policies,
        "task_requirement_ids": requirement_ids,
        "task_validation_ids": validation_ids,
        "task_review_ids": review_ids,
        "requirement_ids": merged_requirement_ids,
        "validation_ids": merged_validation_ids,
        "review_ids": merged_review_ids,
        "structural_guards": structural_guards,
        "allowed_handoff_targets": allowed_handoff_targets,
    }


def load_events(task_dir: Path) -> list[dict[str, Any]]:
    events_path = task_dir / "events.jsonl"
    if not events_path.is_file():
        raise ContractError(f"Missing event log: {events_path}.")

    return parse_events_text(events_path.read_text(encoding="utf-8"))


def parse_events_text(text: str) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        if not raw_line.strip():
            raise ContractError(
                f"Malformed event log line {line_number}: blank lines are not allowed."
            )
        try:
            event = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            raise ContractError(
                f"Malformed event log line {line_number}: {exc}."
            ) from exc
        if not isinstance(event, dict):
            raise ContractError(
                f"Malformed event log line {line_number}: event must be a JSON object."
            )
        if event.get("schema_version") != 1:
            raise ContractError(
                f"Malformed event log line {line_number}: unsupported schema_version."
            )
        if not isinstance(event.get("event"), str):
            raise ContractError(
                f"Malformed event log line {line_number}: missing string `event`."
            )
        if not isinstance(event.get("ts"), str):
            raise ContractError(
                f"Malformed event log line {line_number}: missing string `ts`."
            )
        events.append(event)
    return events


def event_payload(event: dict[str, Any]) -> dict[str, Any]:
    return {
        key: value
        for key, value in event.items()
        if key not in {"schema_version", "ts"}
    }


def canonicalize_event_payload(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def normalize_event(payload: dict[str, Any], *, ts: str | None = None) -> dict[str, Any]:
    timestamp = ts or datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    return {
        "schema_version": 1,
        "ts": timestamp,
        **payload,
    }


def _record_latest(
    latest: dict[str, dict[str, Any]], event: dict[str, Any], key_name: str
) -> None:
    key = event.get(key_name)
    if not isinstance(key, str) or not key:
        raise ContractError(
            f"Event `{event.get('event')}` is missing required string `{key_name}`."
        )
    latest[key] = event


def _require_closeout_id(event: dict[str, Any]) -> str:
    closeout_id = event.get("closeout_id")
    if not isinstance(closeout_id, str) or not closeout_id:
        raise ContractError(
            f"Event `{event.get('event')}` is missing required string `closeout_id`."
        )
    return closeout_id


def _validate_validation_event(event: dict[str, Any]) -> None:
    command = event.get("command")
    if not isinstance(command, str) or not command.strip():
        raise ContractError(
            f"Event `{event.get('event')}` for validation `{event.get('validation_id')}` is missing required non-empty string `command`."
        )

    exit_code = event.get("exit_code")
    if not isinstance(exit_code, int):
        raise ContractError(
            f"Event `{event.get('event')}` for validation `{event.get('validation_id')}` is missing required integer `exit_code`."
        )


def _latest_wrapper_review_event(
    events: list[dict[str, Any]],
) -> tuple[int, dict[str, Any]] | None:
    latest_event: tuple[int, dict[str, Any]] | None = None
    for index, event in enumerate(events):
        if event.get("event") != "runner_step_completed":
            continue
        if event.get("step_id") != "wrapper_review":
            continue
        status = event.get("status")
        if not isinstance(status, str) or status not in WRAPPER_REVIEW_STEP_STATUSES:
            raise ContractError(
                "Wrapper review step event must include status `success`, `findings`, or `failed`."
            )
        latest_event = (index, event)
    return latest_event


def latest_wrapper_review_status(events: list[dict[str, Any]]) -> str | None:
    latest_event = _latest_wrapper_review_event(events)
    if latest_event is None:
        return None
    return latest_event[1]["status"]


def _latest_run_slice_completed_event(
    events: list[dict[str, Any]],
) -> tuple[int, dict[str, Any]] | None:
    latest_event: tuple[int, dict[str, Any]] | None = None
    for index, event in enumerate(events):
        if event.get("event") != "run_slice_completed":
            continue
        exit_code = event.get("exit_code")
        if not isinstance(exit_code, int):
            raise ContractError(
                "Run slice event must include integer `exit_code`."
            )
        latest_event = (index, event)
    return latest_event


def _latest_closeout_event(
    events: list[dict[str, Any]],
) -> tuple[int, dict[str, Any]] | None:
    latest_event: tuple[int, dict[str, Any]] | None = None
    for index, event in enumerate(events):
        if event.get("event") not in ACTIVE_CLOSEOUT_EVENTS:
            continue
        latest_event = (index, event)
    return latest_event


def _validation_after_latest_completed_slice_blocker(
    events: list[dict[str, Any]],
) -> str | None:
    latest_slice = _latest_run_slice_completed_event(events)
    if latest_slice is None:
        return None

    slice_index, _slice_event = latest_slice
    for index, event in enumerate(events):
        if index <= slice_index or event.get("event") not in VALIDATION_EVENTS:
            continue
        validation_id = event.get("validation_id")
        run_id = event.get("run_id")
        validation_label = (
            f"Validation `{validation_id}`"
            if isinstance(validation_id, str) and validation_id
            else "Validation activity"
        )
        run_label = (
            f" for run `{run_id}`"
            if isinstance(run_id, str) and run_id
            else ""
        )
        return (
            f"{validation_label}{run_label} was recorded after the latest completed run slice; "
            "finish the current slice and rerun the authoritative wrapper review before syncing "
            "closeout or claiming contract readiness."
        )
    return None


def _stale_closeout_sync_blocker(events: list[dict[str, Any]]) -> str | None:
    latest_slice = _latest_run_slice_completed_event(events)
    latest_closeout = _latest_closeout_event(events)
    if latest_slice is None or latest_closeout is None:
        return None

    slice_index, _slice_event = latest_slice
    closeout_index, closeout_event = latest_closeout
    if closeout_index > slice_index:
        return None

    closeout_id = closeout_event.get("closeout_id")
    if not isinstance(closeout_id, str) or not closeout_id:
        raise ContractError(
            f"Event `{closeout_event.get('event')}` is missing required string `closeout_id`."
        )
    return (
        f"Latest closeout sync `{closeout_id}` predates the latest completed run slice; "
        "rerun wrapper-owned closeout sync for the current slice before claiming contract readiness."
    )


def _active_internal_runner_blocker(repo_root: Path) -> str | None:
    if os.environ.get("CODEX_LHT_ALLOW_ACTIVE_WRAPPER") == "1":
        return None

    wrapper_script = (
        repo_root / runtime_root_rel_for_repo(repo_root) / "run-long-horizon.sh"
    ).resolve()

    def inspect_lock_path(lock_path: Path) -> str | None:
        if not lock_path.exists():
            return None
        try:
            handle = lock_path.open("rb")
        except FileNotFoundError:
            return None
        except OSError as exc:
            return (
                f"Unable to inspect the internal wrapper lock at `{lock_path}` read-only: {exc}."
            )
        with handle:
            try:
                # Inspect-only contract checks must not create or mutate the
                # lock file, so probe an existing lock with a shared
                # non-blocking lock.
                fcntl.flock(handle.fileno(), fcntl.LOCK_SH | fcntl.LOCK_NB)
            except BlockingIOError:
                return (
                    "The authoritative internal wrapper run is still active for this checkout; "
                    "wait for it to finish before syncing closeout or claiming contract readiness."
                )
            except OSError as exc:
                return (
                    f"Unable to inspect the internal wrapper lock at `{lock_path}` read-only: {exc}."
                )
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        return None

    def resolve_arg_path(arg: str, proc_cwd: Path) -> Path | None:
        if not arg or arg.startswith("-"):
            return None
        candidate = Path(arg)
        if not candidate.is_absolute():
            candidate = proc_cwd / candidate
        try:
            return candidate.resolve()
        except OSError:
            return None

    def looks_like_wrapper_process(args: list[str], proc_cwd: Path) -> bool:
        script_index: int | None = None
        for index, arg in enumerate(args):
            resolved = resolve_arg_path(arg, proc_cwd)
            if resolved == wrapper_script:
                script_index = index
                break
        if script_index is None:
            return False
        for index, arg in enumerate(args[script_index + 1 :], start=script_index + 1):
            if arg == "--task":
                return index + 1 < len(args) and bool(args[index + 1])
            if arg.startswith("--task="):
                return len(arg.split("=", 1)[1]) > 0
        return False

    for lock_path in internal_runner_lock_paths(repo_root):
        blocker = inspect_lock_path(lock_path)
        if blocker is not None:
            return blocker

    if os.name != "posix" or not Path("/proc").is_dir():
        return None

    current_pid = os.getpid()
    for proc_dir in Path("/proc").iterdir():
        if not proc_dir.name.isdigit():
            continue
        try:
            pid = int(proc_dir.name)
        except ValueError:
            continue
        if pid == current_pid:
            continue
        try:
            cwd = Path(os.path.realpath(proc_dir / "cwd"))
        except OSError:
            continue
        if cwd != repo_root and repo_root not in cwd.parents:
            continue
        try:
            raw_cmdline = (proc_dir / "cmdline").read_bytes()
        except OSError:
            continue
        if not raw_cmdline:
            continue
        args = [
            arg.decode("utf-8", errors="replace")
            for arg in raw_cmdline.split(b"\0")
            if arg
        ]
        if looks_like_wrapper_process(args, cwd):
            return (
                "The authoritative internal wrapper run is still active for this checkout; "
                "wait for it to finish before syncing closeout or claiming contract readiness."
            )
    return None


def _authoritative_wrapper_review_success_blocker(
    events: list[dict[str, Any]],
) -> str | None:
    latest_review = _latest_wrapper_review_event(events)
    if latest_review is None:
        return None
    review_index, review_event = latest_review
    if review_event["status"] != "success":
        return None

    run_id = review_event.get("run_id")
    started_at = review_event.get("started_at")
    ended_at = review_event.get("ended_at")
    duration_seconds = review_event.get("duration_seconds")
    if (
        not isinstance(run_id, str)
        or not run_id
        or not isinstance(started_at, str)
        or not started_at
        or not isinstance(ended_at, str)
        or not ended_at
        or not isinstance(duration_seconds, (int, float))
        or duration_seconds < 0
    ):
        return (
            "Latest wrapper review step recorded `success` without the wrapper-owned run metadata "
            "(`run_id`, `started_at`, `ended_at`, `duration_seconds`) needed to prove it came "
            "from the authoritative wrapper review step."
        )

    latest_slice = _latest_run_slice_completed_event(events)
    if latest_slice is None:
        return (
            "Latest wrapper review step recorded `success` without any completed run slice to review; "
            "do not use ad hoc/manual review events to satisfy closeout."
        )

    slice_index, slice_event = latest_slice
    slice_run_id = slice_event.get("run_id")
    if not isinstance(slice_run_id, str) or not slice_run_id:
        return "Latest completed run slice is missing required string `run_id`."
    if review_index <= slice_index:
        return (
            "Latest wrapper review `success` predates the latest completed run slice; "
            "rerun the authoritative wrapper review for the current slice before syncing closeout."
        )
    if slice_event["exit_code"] != 0:
        return (
            f"Latest completed run slice for `{slice_run_id}` exited `{slice_event['exit_code']}`; "
            "do not claim readiness from an older wrapper review success."
        )
    if run_id != slice_run_id:
        return (
            f"Latest wrapper review `success` recorded run_id `{run_id}`, but the latest completed "
            f"run slice belongs to `{slice_run_id}`; rerun the authoritative wrapper review for the current slice."
        )
    return None


def wrapper_review_blockers(task_dir: Path, events: list[dict[str, Any]]) -> list[str]:
    blockers: list[str] = []
    repo_root = repo_root_for_task_dir(task_dir)
    active_runner_blocker = _active_internal_runner_blocker(repo_root)
    if active_runner_blocker is not None:
        blockers.append(active_runner_blocker)

    validation_postdate_blocker = _validation_after_latest_completed_slice_blocker(events)
    if validation_postdate_blocker is not None:
        blockers.append(validation_postdate_blocker)

    latest_status = latest_wrapper_review_status(events)
    if latest_status in {"findings", "failed"}:
        blockers.append(
            "Latest wrapper review step recorded status "
            f"`{latest_status}`; rerun the wrapper review loop until it records `success`."
        )
    elif latest_status == "success":
        authoritative_success_blocker = _authoritative_wrapper_review_success_blocker(
            events
        )
        if authoritative_success_blocker is not None:
            blockers.append(authoritative_success_blocker)

    if (task_dir / "ReviewResume.md").exists():
        blockers.append(
            "Active `ReviewResume.md` repair context is still present; "
            "do not sync closeout or claim handoff readiness until a clean wrapper review removes it."
        )

    return blockers


def _matches_any(path: str, patterns: list[str]) -> bool:
    return any(fnmatch.fnmatch(path, pattern) for pattern in patterns)


def _iter_structural_guard_files(
    repo_root: Path, include_globs: list[str], exclude_globs: list[str]
) -> list[Path]:
    files: list[Path] = []
    for path in repo_root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(repo_root).as_posix()
        if not _matches_any(rel, include_globs):
            continue
        if _matches_any(rel, exclude_globs):
            continue
        files.append(path)
    return files


def evaluate_structural_guards(
    repo_root: Path, guards: list[dict[str, Any]]
) -> list[str]:
    errors: list[str] = []
    for guard in guards:
        compiled = [
            (pattern, re.compile(pattern)) for pattern in guard["forbidden_regexes"]
        ]
        for path in _iter_structural_guard_files(
            repo_root, guard["include_globs"], guard["exclude_globs"]
        ):
            rel = path.relative_to(repo_root).as_posix()
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except UnicodeDecodeError:
                continue
            for line_number, line in enumerate(lines, start=1):
                for pattern, regex in compiled:
                    if regex.search(line):
                        errors.append(
                            f"Structural guard `{guard['policy_id']}:{guard['guard_id']}` matched `{pattern}` at {rel}:{line_number}."
                        )
    return errors


def evaluate_contract(task_dir: Path) -> dict[str, Any]:
    contract = load_contract(task_dir)
    events = load_events(task_dir)
    repo_root = repo_root_for_task_dir(task_dir)

    latest_validations: dict[str, dict[str, Any]] = {}
    latest_closeout_id: str | None = None
    closeout_events_by_id: dict[str, list[dict[str, Any]]] = {}

    for event in events:
        event_type = event["event"]
        if event_type in VALIDATION_EVENTS:
            _validate_validation_event(event)
            _record_latest(latest_validations, event, "validation_id")
        elif event_type in REQUIREMENT_EVENTS:
            closeout_id = _require_closeout_id(event)
            closeout_events_by_id.setdefault(closeout_id, []).append(event)
            latest_closeout_id = closeout_id
        elif event_type in REVIEW_EVENTS:
            closeout_id = _require_closeout_id(event)
            closeout_events_by_id.setdefault(closeout_id, []).append(event)
            latest_closeout_id = closeout_id
        elif event_type in HANDOFF_EVENTS:
            closeout_id = _require_closeout_id(event)
            handoff_target = event.get("handoff_target")
            if not isinstance(handoff_target, str) or not handoff_target:
                raise ContractError(
                    "Event `handoff_requested` is missing required string `handoff_target`."
                )
            closeout_events_by_id.setdefault(closeout_id, []).append(event)
            latest_closeout_id = closeout_id

    errors: list[str] = []

    for validation_id in contract["validation_ids"]:
        latest_event = latest_validations.get(validation_id)
        if latest_event is None:
            errors.append(f"Missing validation event for `{validation_id}`.")
            continue
        if latest_event["event"] != "validation_passed":
            errors.append(
                f"Validation `{validation_id}` last recorded `{latest_event['event']}`."
            )
            continue
        if latest_event["exit_code"] != 0:
            errors.append(
                f"Validation `{validation_id}` recorded `validation_passed` with nonzero exit_code `{latest_event['exit_code']}`."
            )

    stale_closeout_sync_blocker = _stale_closeout_sync_blocker(events)
    if stale_closeout_sync_blocker is not None:
        errors.append(stale_closeout_sync_blocker)
        active_closeout_events: list[dict[str, Any]] = []
    else:
        active_closeout_events = (
            closeout_events_by_id.get(latest_closeout_id, [])
            if latest_closeout_id is not None
            else []
        )
    active_requirements: dict[str, dict[str, Any]] = {}
    active_reviews: dict[str, dict[str, Any]] = {}
    active_handoff: dict[str, Any] | None = None

    for event in active_closeout_events:
        event_type = event["event"]
        if event_type in REQUIREMENT_EVENTS:
            requirement_id = event.get("requirement_id")
            if not isinstance(requirement_id, str) or not requirement_id:
                raise ContractError(
                    f"Event `{event_type}` is missing required string `requirement_id`."
                )
            previous = active_requirements.get(requirement_id)
            if previous is not None and previous["event"] != event_type:
                raise ContractError(
                    f"Closeout `{latest_closeout_id}` contains contradictory requirement evidence for `{requirement_id}`."
                )
            active_requirements[requirement_id] = event
        elif event_type in REVIEW_EVENTS:
            review_id = event.get("review_id")
            if not isinstance(review_id, str) or not review_id:
                raise ContractError(
                    f"Event `{event_type}` is missing required string `review_id`."
                )
            previous = active_reviews.get(review_id)
            if previous is not None and previous["event"] != event_type:
                raise ContractError(
                    f"Closeout `{latest_closeout_id}` contains contradictory review evidence for `{review_id}`."
                )
            active_reviews[review_id] = event
        elif event_type in HANDOFF_EVENTS:
            if (
                active_handoff is not None
                and active_handoff["handoff_target"] != event["handoff_target"]
            ):
                raise ContractError(
                    f"Closeout `{latest_closeout_id}` contains contradictory handoff targets."
                )
            active_handoff = event

    for requirement_id in contract["requirement_ids"]:
        latest_event = active_requirements.get(requirement_id)
        if latest_event is None:
            errors.append(f"Missing requirement event for `{requirement_id}`.")
            continue
        if latest_event["event"] != "requirement_satisfied":
            errors.append(
                f"Requirement `{requirement_id}` last recorded `{latest_event['event']}`."
            )

    for review_id in contract["review_ids"]:
        latest_event = active_reviews.get(review_id)
        if latest_event is None:
            errors.append(f"Missing review event for `{review_id}`.")
            continue
        if latest_event["event"] != "review_passed":
            errors.append(
                f"Review `{review_id}` last recorded `{latest_event['event']}`."
            )

    if active_handoff is None:
        errors.append("Missing handoff request event.")
        handoff_target = None
    else:
        handoff_target = active_handoff["handoff_target"]
        if handoff_target not in contract["allowed_handoff_targets"]:
            errors.append(
                f"Handoff target `{handoff_target}` is not allowed by Contract.md."
            )

    errors.extend(wrapper_review_blockers(task_dir, events))
    errors.extend(evaluate_structural_guards(repo_root, contract["structural_guards"]))

    return {
        "ok": not errors,
        "task_dir": str(task_dir),
        "handoff_target": handoff_target,
        "contract": contract,
        "errors": errors,
    }


def append_event(task_dir: Path, payload: dict[str, Any]) -> Path:
    return append_events(task_dir, [payload])


def append_events(task_dir: Path, payloads: list[dict[str, Any]]) -> Path:
    events_path = task_dir / "events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    serialized_events = [
        json.dumps(normalize_event(payload, ts=timestamp), sort_keys=True)
        for payload in payloads
    ]

    with events_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.seek(0)
        parse_events_text(handle.read())
        handle.seek(0, 2)
        for serialized in serialized_events:
            handle.write(serialized)
            handle.write("\n")
        handle.flush()
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)

    return events_path
