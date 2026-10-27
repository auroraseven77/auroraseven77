#!/usr/bin/env python3
"""Bounded GitHub-to-Termux test worker for the Aurora mirror.

Only fixed test suites are executable. Queue documents never contain shell commands.
This is an execution gate for owner-controlled branches, not a security sandbox.
"""

from __future__ import annotations

import argparse
import base64
import fcntl
import hashlib
import json
import os
import platform
import re
import signal
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = "0.1.0"
REPOSITORY = "auroraseven77/auroraseven77"
REMOTE_URLS = {
    "https://github.com/auroraseven77/auroraseven77.git",
    "https://github.com/auroraseven77/auroraseven77",
}
QUEUE_BRANCH = "automation/termux-task-queue"
QUEUE_PATH = ".aurora-termux-worker/queue.json"
RESULT_ROOT = "integrations/aurora-termux-worker/reports"
MAX_QUEUE_BYTES = 32 * 1024
MAX_TASKS_PER_POLL = 8
MIN_TIMEOUT_SECONDS = 30
MAX_TIMEOUT_SECONDS = 1800
MAX_LOG_BYTES = 256 * 1024
LOG_TAIL_BYTES = 4096
TASK_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
SHA_RE = re.compile(r"^[0-9a-fA-F]{40}$")
SECRET_PATTERNS = (
    re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"(?i)\b(token|password|secret|api[_-]?key)\s*[:=]\s*\S+"),
)

# Each suite is fixed in code. The queue cannot provide arguments or shell text.
SUITES: dict[str, tuple[str, ...]] = {
    "motor_optimizer": (
        "-m", "pytest", "-q",
        "b1_motor/tests/test_optimizer_contract.py",
        "b1_motor/test_motor.py",
        "b1_motor/test_contract.py",
    ),
    "mps_observables": (
        "-m", "pytest", "-q",
        "b1_motor/tests/test_observables_api.py",
        "b1_motor/tests/test_mps_two_qubit.py",
        "b1_motor/tests/test_vqe_b12.py",
    ),
    "motor_b12": (
        "-m", "pytest", "-q",
        "b1_motor/tests/test_ansatz_b12.py",
        "b1_motor/tests/test_ansatz_topology_b12.py",
        "b1_motor/tests/test_hamiltonian_b12.py",
        "b1_motor/tests/test_observables_api.py",
        "b1_motor/tests/test_vqe_b12.py",
    ),
    "tuu_invariants": (
        "-m", "pytest", "-q",
        "tests/test_invariant_engine.py",
        "tests/test_raw_first_lifecycle.py",
        "TUU/tests",
    ),
    "phase1": (
        "-m", "unittest", "discover",
        "-s", "aurora_phase1/tests", "-v",
    ),
    "compile_core": (
        "-m", "compileall", "-q",
        "b1_motor", "TUU", "aurora_phase1",
    ),
}


class WorkerError(RuntimeError):
    """Expected worker/configuration failure."""


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def validate_queue(raw: bytes) -> list[dict[str, Any]]:
    """Validate the bounded queue schema and return normalized task records."""
    if len(raw) > MAX_QUEUE_BYTES:
        raise WorkerError("queue exceeds maximum byte size")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WorkerError("queue is not valid UTF-8 JSON") from exc
    if not isinstance(payload, dict) or set(payload) != {"schema_version", "tasks"}:
        raise WorkerError("queue must contain only schema_version and tasks")
    if payload["schema_version"] != 1 or isinstance(payload["schema_version"], bool):
        raise WorkerError("unsupported queue schema_version")
    tasks = payload["tasks"]
    if not isinstance(tasks, list) or len(tasks) > MAX_TASKS_PER_POLL:
        raise WorkerError(f"tasks must be a list with at most {MAX_TASKS_PER_POLL} entries")

    normalized: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    required = {"task_id", "pr", "sha", "suite", "timeout_seconds"}
    for index, task in enumerate(tasks):
        if not isinstance(task, dict) or set(task) != required:
            raise WorkerError(f"task {index} has an invalid field set")
        task_id = task["task_id"]
        if not isinstance(task_id, str) or not TASK_ID_RE.fullmatch(task_id):
            raise WorkerError(f"task {index} has an invalid task_id")
        if task_id in seen_ids:
            raise WorkerError(f"duplicate task_id: {task_id}")
        seen_ids.add(task_id)

        pr = task["pr"]
        if isinstance(pr, bool) or not isinstance(pr, int) or not 1 <= pr <= 999999:
            raise WorkerError(f"task {task_id} has an invalid PR number")
        sha = task["sha"]
        if not isinstance(sha, str) or not SHA_RE.fullmatch(sha):
            raise WorkerError(f"task {task_id} must specify a full 40-character commit SHA")
        suite = task["suite"]
        if not isinstance(suite, str) or suite not in SUITES:
            raise WorkerError(f"task {task_id} uses a non-allowlisted suite")
        timeout = task["timeout_seconds"]
        if (
            isinstance(timeout, bool)
            or not isinstance(timeout, int)
            or not MIN_TIMEOUT_SECONDS <= timeout <= MAX_TIMEOUT_SECONDS
        ):
            raise WorkerError(
                f"task {task_id} timeout_seconds must be in "
                f"[{MIN_TIMEOUT_SECONDS}, {MAX_TIMEOUT_SECONDS}]"
            )
        normalized.append(
            {
                "task_id": task_id,
                "pr": pr,
                "sha": sha.lower(),
                "suite": suite,
                "timeout_seconds": timeout,
            }
        )
    return normalized


def suite_command(suite: str, python_executable: str | None = None) -> list[str]:
    """Build a command exclusively from the compiled-in allowlist."""
    if suite not in SUITES:
        raise WorkerError(f"non-allowlisted suite: {suite}")
    executable = python_executable or sys.executable
    if not os.path.isabs(executable):
        raise WorkerError("Python executable must be an absolute path")
    return [executable, *SUITES[suite]]


def sanitize_log(raw: bytes) -> str:
    """Return a bounded UTF-8 tail with common credential formats redacted."""
    text = raw[-LOG_TAIL_BYTES:].decode("utf-8", errors="replace")
    for pattern in SECRET_PATTERNS:
        text = pattern.sub("[REDACTED]", text)
    return text


def _git(repo: Path, *args: str, timeout: int = 60, env: dict[str, str] | None = None) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo), *args],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        env=env,
        check=False,
    )
    if completed.returncode:
        detail = sanitize_log(completed.stderr)
        raise WorkerError(f"git command failed ({completed.returncode}): {detail[-1000:]}")
    return completed.stdout.decode("utf-8", errors="replace").strip()


def _check_repo(repo: Path) -> None:
    if not repo.is_dir():
        raise WorkerError(f"mirror repository does not exist: {repo}")
    top = _git(repo, "rev-parse", "--show-toplevel")
    if Path(top).resolve() != repo.resolve():
        raise WorkerError("configured mirror path is not the Git top level")
    remote = _git(repo, "remote", "get-url", "origin").strip()
    if remote not in REMOTE_URLS:
        raise WorkerError("origin URL does not match the allowlisted Aurora repository")


def _queue_bytes(repo: Path) -> bytes:
    _git(repo, "fetch", "--no-tags", "origin", f"refs/heads/{QUEUE_BRANCH}")
    result = subprocess.run(
        ["git", "-C", str(repo), "show", f"FETCH_HEAD:{QUEUE_PATH}"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    if result.returncode:
        raise WorkerError("could not read the queue manifest from its dedicated branch")
    if len(result.stdout) > MAX_QUEUE_BYTES:
        raise WorkerError("queue exceeds maximum byte size")
    return result.stdout


def _test_environment(temp_root: Path) -> dict[str, str]:
    """Do not pass token/config environment variables to tests."""
    home = temp_root / "home"
    tmp = temp_root / "tmp"
    home.mkdir(parents=True, exist_ok=True)
    tmp.mkdir(parents=True, exist_ok=True)
    return {
        "PATH": os.environ.get("PATH", "/data/data/com.termux/files/usr/bin:/system/bin"),
        "HOME": str(home),
        "TMPDIR": str(tmp),
        "TMP": str(tmp),
        "TEMP": str(tmp),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "TERM": "dumb",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONUNBUFFERED": "1",
    }


def _resource_limits(timeout_seconds: int):
    """Best-effort POSIX limits for CPU and individual output files."""
    def apply() -> None:
        try:
            import resource
            resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
            file_limit = MAX_LOG_BYTES
            resource.setrlimit(resource.RLIMIT_FSIZE, (file_limit, file_limit))
            cpu_soft = max(1, timeout_seconds)
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_soft, cpu_soft + 2))
        except (ImportError, AttributeError, OSError, ValueError):
            # The parent timeout remains authoritative where rlimits are unavailable.
            pass
    return apply


def _verify_pr_commit(repo: Path, task: dict[str, Any]) -> bool:
    ref = f"refs/pull/{task['pr']}/head"
    _git(repo, "fetch", "--no-tags", "origin", ref, timeout=90)
    fetched_sha = _git(repo, "rev-parse", "FETCH_HEAD^{commit}")
    return fetched_sha.lower() == task["sha"]


def _run_suite(repo: Path, task: dict[str, Any]) -> dict[str, Any]:
    started = utc_now()
    start_monotonic = time.monotonic()
    report: dict[str, Any] = {
        "schema_version": 1,
        "worker_version": VERSION,
        "repository": REPOSITORY,
        "task_id": task["task_id"],
        "pr": task["pr"],
        "source_sha": task["sha"],
        "suite": task["suite"],
        "timeout_seconds": task["timeout_seconds"],
        "started_at": started,
        "finished_at": None,
        "elapsed_seconds": None,
        "outcome": "runner_error",
        "exit_code": None,
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "stdout_tail": "",
        "stderr_tail": "",
        "result_branch": None,
    }

    if not _verify_pr_commit(repo, task):
        report["outcome"] = "stale_commit"
        report["stderr_tail"] = (
            "Queue SHA no longer matches the current PR head; no source code was run."
        )
    else:
        with tempfile.TemporaryDirectory(prefix="aurora-task-") as temp_name:
            temp_root = Path(temp_name)
            checkout = temp_root / "checkout"
            stdout_path = temp_root / "stdout.log"
            stderr_path = temp_root / "stderr.log"
            _git(repo, "worktree", "add", "--detach", str(checkout), task["sha"], timeout=90)
            try:
                command = suite_command(task["suite"])
                env = _test_environment(temp_root)
                try:
                    with stdout_path.open("wb") as stdout_file, stderr_path.open("wb") as stderr_file:
                        process = subprocess.Popen(
                            command,
                            cwd=checkout,
                            env=env,
                            stdin=subprocess.DEVNULL,
                            stdout=stdout_file,
                            stderr=stderr_file,
                            start_new_session=True,
                            preexec_fn=_resource_limits(task["timeout_seconds"]),
                        )
                        timed_out = False
                        try:
                            return_code = process.wait(timeout=task["timeout_seconds"])
                        except subprocess.TimeoutExpired:
                            timed_out = True
                            # Kill the whole process group so children cannot outlive
                            # a timed-out test suite on the phone.
                            try:
                                os.killpg(process.pid, signal.SIGTERM)
                            except ProcessLookupError:
                                pass
                            try:
                                process.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                try:
                                    os.killpg(process.pid, signal.SIGKILL)
                                except ProcessLookupError:
                                    pass
                                process.wait()
                    if timed_out:
                        report["outcome"] = "timeout"
                        report["exit_code"] = 124
                    else:
                        report["exit_code"] = return_code
                        report["outcome"] = "passed" if return_code == 0 else "failed"
                except OSError as exc:
                    report["outcome"] = "runner_error"
                    report["exit_code"] = 126
                    report["stderr_tail"] = f"Could not start test command: {type(exc).__name__}"
                report["stdout_tail"] = sanitize_log(stdout_path.read_bytes()) if stdout_path.exists() else ""
                report["stderr_tail"] = sanitize_log(stderr_path.read_bytes()) if stderr_path.exists() else ""
            finally:
                _git(repo, "worktree", "remove", "--force", str(checkout), timeout=60)

    report["finished_at"] = utc_now()
    report["elapsed_seconds"] = round(time.monotonic() - start_monotonic, 3)
    return report


def _read_token(token_path: Path) -> str:
    try:
        info = token_path.stat()
    except FileNotFoundError as exc:
        raise WorkerError(
            f"missing write token file: {token_path}; worker must not run without result return path"
        ) from exc
    if not stat.S_ISREG(info.st_mode) or stat.S_IMODE(info.st_mode) & 0o077:
        raise WorkerError("token file must be a regular file with mode 0600 or stricter")
    token = token_path.read_text(encoding="utf-8").strip()
    if not token or "\n" in token or "\r" in token:
        raise WorkerError("token file must contain exactly one non-empty line")
    return token


def _push_environment(token: str) -> dict[str, str]:
    """Provide write credentials only to the one git push subprocess."""
    env = os.environ.copy()
    value = base64.b64encode(f"x-access-token:{token}".encode("utf-8")).decode("ascii")
    env["GIT_CONFIG_COUNT"] = "1"
    env["GIT_CONFIG_KEY_0"] = "http.https://github.com/.extraheader"
    env["GIT_CONFIG_VALUE_0"] = f"AUTHORIZATION: basic {value}"
    return env


def _report_payload(report: dict[str, Any]) -> bytes:
    return (json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode("utf-8")


def _publish_report(repo: Path, token_path: Path, report: dict[str, Any]) -> str:
    """Publish one append-only result branch; never push to main or the source PR."""
    task_id = report["task_id"]
    source_sha = report["source_sha"]
    report_rel = f"{RESULT_ROOT}/{task_id}--{source_sha[:12]}.json"
    result_branch = f"automation/termux-results/{task_id}-{source_sha[:12]}"
    report["result_branch"] = result_branch
    payload = _report_payload(report)

    # Idempotent retry: if this exact report branch already exists, require byte identity.
    existing = _git(repo, "ls-remote", "--heads", "origin", f"refs/heads/{result_branch}")
    if existing:
        _git(repo, "fetch", "--no-tags", "origin", f"refs/heads/{result_branch}")
        remote_payload = _git(repo, "show", f"FETCH_HEAD:{report_rel}").encode("utf-8") + b"\n"
        if remote_payload != payload:
            raise WorkerError("result branch exists with different bytes; refusing to overwrite it")
        return result_branch

    _git(repo, "fetch", "--no-tags", "origin", "refs/heads/main", timeout=90)
    main_sha = _git(repo, "rev-parse", "FETCH_HEAD^{commit}")
    token = _read_token(token_path)  # Read after tests have completed.
    with tempfile.TemporaryDirectory(prefix="aurora-report-") as temp_name:
        report_worktree = Path(temp_name) / "report"
        _git(repo, "worktree", "add", "--detach", str(report_worktree), main_sha, timeout=90)
        try:
            destination = report_worktree / report_rel
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(payload)
            _git(report_worktree, "add", "--", report_rel)
            commit = _git(
                report_worktree,
                "-c", "user.name=Aurora Termux Worker",
                "-c", "user.email=aurora-termux-worker@users.noreply.github.com",
                "commit", "-m", f"termux-worker: report {task_id} {source_sha[:12]}",
            )
            commit_sha = _git(report_worktree, "rev-parse", "HEAD")
            push_env = _push_environment(token)
            _git(
                report_worktree,
                "push", "origin", f"{commit_sha}:refs/heads/{result_branch}",
                timeout=120,
                env=push_env,
            )
        finally:
            _git(repo, "worktree", "remove", "--force", str(report_worktree), timeout=60)
    return result_branch


def _load_state(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        completed = payload.get("completed", {})
        if payload.get("schema_version") != 1 or not isinstance(completed, dict):
            raise ValueError
        return {
            str(task_id): str(sha).lower()
            for task_id, sha in completed.items()
            if isinstance(task_id, str) and isinstance(sha, str) and SHA_RE.fullmatch(sha)
        }
    except (OSError, json.JSONDecodeError, ValueError, AttributeError):
        raise WorkerError("worker state is invalid; refusing to rerun tasks blindly")


def _save_state(path: Path, completed: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps({"schema_version": 1, "completed": completed}, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    os.chmod(temporary, 0o600)
    os.replace(temporary, path)


def run_worker(repo: Path, state_dir: Path, token_path: Path) -> int:
    repo = repo.expanduser().resolve()
    state_dir = state_dir.expanduser().resolve()
    state_dir.mkdir(parents=True, exist_ok=True)
    lock_path = state_dir / "worker.lock"
    state_path = state_dir / "completed.json"

    with lock_path.open("a", encoding="utf-8") as lock_handle:
        try:
            fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print("AURORA_WORKER_LOCKED no operation started")
            return 0

        _check_repo(repo)
        tasks = validate_queue(_queue_bytes(repo))
        if not tasks:
            print("AURORA_WORKER_QUEUE_EMPTY")
            return 0

        completed = _load_state(state_path)
        pending = [task for task in tasks if completed.get(task["task_id"]) != task["sha"]]
        if not pending:
            print(f"AURORA_WORKER_NO_NEW_TASKS count={len(tasks)}")
            return 0

        # Validate credentials before executing code; token bytes are not passed to tests.
        if not token_path.exists():
            raise WorkerError(f"missing write token file: {token_path}")
        token_mode = stat.S_IMODE(token_path.stat().st_mode)
        if token_mode & 0o077:
            raise WorkerError("token file must have mode 0600 or stricter")

        for task in pending:
            report = _run_suite(repo, task)
            result_branch = _publish_report(repo, token_path, report)
            completed[task["task_id"]] = task["sha"]
            _save_state(state_path, completed)
            print(
                f"AURORA_WORKER_RESULT task={task['task_id']} "
                f"outcome={report['outcome']} pr={task['pr']} "
                f"sha={task['sha']} branch={result_branch}"
            )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo",
        default=str(Path.home() / "auroraseven77-sync-mirror"),
        help="path to the isolated Aurora mirror Git checkout",
    )
    parser.add_argument(
        "--state-dir",
        default=str(Path.home() / ".local/state/aurora-termux-worker"),
        help="private worker state directory",
    )
    parser.add_argument(
        "--token-file",
        default=str(Path.home() / ".config/aurora-sync-mirror/github_token"),
        help="0600 fine-grained GitHub token used only to publish result branches",
    )
    args = parser.parse_args(argv)
    try:
        return run_worker(Path(args.repo), Path(args.state_dir), Path(args.token_file))
    except (WorkerError, OSError, subprocess.SubprocessError) as exc:
        # Never print environment, token contents, or arbitrary command arguments.
        print(f"AURORA_WORKER_ERROR {type(exc).__name__}: {str(exc)[:1000]}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
