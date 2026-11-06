#!/usr/bin/env python3
"""Aurora-10 read-only observability pilot. Python standard library only."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import socket
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AGENTS = (
    "A01_ARGOS_HEALTH", "A02_SPEC_API", "A03_AUTH_REVIEW", "A04_SOCKET",
    "A05_PROCESS", "A06_LIFECYCLE", "A07_RESOURCE", "A08_INTEGRITY",
    "A09_NETWORK", "A10_HERMES",
)
DEFAULT_SOURCE = Path("/opt/terminal-server/openai/server.py")
DEFAULT_OUTPUT = Path("./aurora-10-observations")
MAX_DURATION_HOURS = 24
MAX_INTERVAL_SECONDS = 3600
MAX_SOURCE_BYTES = 2_000_000
HTTP_TIMEOUT_SECONDS = 2.0


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def read_text(path: Path, limit: int = MAX_SOURCE_BYTES) -> tuple[str | None, str | None]:
    try:
        if not path.is_file():
            return None, "not_a_regular_file_or_missing"
        size = path.stat().st_size
        if size > limit:
            return None, f"size_limit_exceeded:{size}"
        return path.read_text(encoding="utf-8", errors="replace"), None
    except Exception as exc:
        return None, f"{type(exc).__name__}:{exc}"


def parse_proc_tcp(path: Path) -> dict[str, Any]:
    text, error = read_text(path, 256_000)
    if error:
        return {"available": False, "reason": error, "listeners": []}
    listeners = []
    for line in text.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 4:
            continue
        local_hex, state = parts[1], parts[3]
        if state != "0A" or ":" not in local_hex:
            continue
        addr_hex, port_hex = local_hex.split(":", 1)
        try:
            port = int(port_hex, 16)
            raw = bytes.fromhex(addr_hex)
            address = socket.inet_ntop(socket.AF_INET, raw[::-1])
        except Exception:
            address, port = "unparsed", -1
        listeners.append({"address": address, "port": port, "state": "LISTEN"})
    return {"available": True, "listeners": listeners}


def source_text(source: Path) -> dict[str, Any]:
    content, error = read_text(source)
    if error:
        return {"available": False, "path": str(source), "reason": error}
    return {"available": True, "path": str(source), "content": content}


def agent_health(_: dict[str, Any]) -> dict[str, Any]:
    url = "http://127.0.0.1:1384/healthcheck"
    request = urllib.request.Request(url, method="GET", headers={"User-Agent": "Aurora-10-readonly/0.1"})
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            body = response.read(4096).decode("utf-8", "replace")
            return {"url": url, "method": "GET", "http_status": response.status, "body_excerpt": body}
    except urllib.error.HTTPError as exc:
        return {"url": url, "method": "GET", "http_status": exc.code, "error": "http_error"}
    except Exception as exc:
        return {"url": url, "method": "GET", "available": False, "reason": f"{type(exc).__name__}:{exc}"}


def agent_spec(ctx: dict[str, Any]) -> dict[str, Any]:
    src = source_text(ctx["source"])
    if not src["available"]:
        return {k: v for k, v in src.items() if k != "content"}
    code = src["content"]
    patterns = {
        "healthcheck_route": r"@app\.(?:get|api_route)\s*\(\s*['\"]/?healthcheck",
        "open_route": r"@app\.(?:post|api_route)\s*\(\s*['\"]/?open",
        "read_route": r"@app\.(?:post|api_route)\s*\(\s*['\"]/?read",
        "write_route": r"@app\.(?:post|api_route)\s*\(\s*['\"]/?write",
        "kill_route": r"@app\.(?:post|api_route)\s*\(\s*['\"]/?kill",
        "http_middleware": r"@app\.middleware\s*\(\s*['\"]http['\"]",
    }
    return {"path": str(ctx["source"]), "static_matches": {k: bool(re.search(v, code)) for k, v in patterns.items()},
            "note": "static_text_match_only_not_runtime_route_verification"}


def agent_auth(ctx: dict[str, Any]) -> dict[str, Any]:
    src = source_text(ctx["source"])
    if not src["available"]:
        return {k: v for k, v in src.items() if k != "content"}
    code = src["content"]
    return {
        "path": str(ctx["source"]),
        "middleware_present": bool(re.search(r"@app\.middleware\s*\(\s*['\"]http['\"]", code)),
        "token_env_reference_present": "BEARER_TOKEN" in code,
        "conditional_token_guard_pattern": bool(re.search(r"if\s+expected_bearer_token\s+and", code)),
        "reject_status_401_pattern": bool(re.search(r"status_code\s*=\s*401", code)),
        "warning": "does_not_read_environment_or_secret_values; static inspection is not effective-authentication proof",
    }


def agent_socket(_: dict[str, Any]) -> dict[str, Any]:
    return {"tcp": parse_proc_tcp(Path("/proc/net/tcp")), "tcp6": parse_proc_tcp(Path("/proc/net/tcp6"))}


def agent_process(_: dict[str, Any]) -> dict[str, Any]:
    matches = []
    try:
        entries = list(Path("/proc").iterdir())
    except Exception as exc:
        return {"available": False, "reason": f"{type(exc).__name__}:{exc}", "matches": []}
    for entry in entries:
        if not entry.name.isdigit():
            continue
        cmd, err = read_text(entry / "cmdline", 8192)
        if err or not cmd:
            continue
        display = cmd.replace("\x00", " ").strip()
        if "terminal-server" not in display.lower() and "server.py" not in display.lower():
            continue
        status, status_err = read_text(entry / "status", 32768)
        stat, stat_err = read_text(entry / "stat", 8192)
        selected = {}
        if status:
            for line in status.splitlines():
                if line.startswith(("Name:", "Uid:", "Gid:", "PPid:", "State:")):
                    selected[line.split(":", 1)[0]] = line.split(":", 1)[1].strip()
        matches.append({"pid": int(entry.name), "cmdline": display[:512], "status_fields": selected,
                        "status_read_error": status_err, "stat_available": stat is not None,
                        "stat_read_error": stat_err})
    return {"matches": matches, "note": "proc visibility is permission- and namespace-dependent; no signal is sent"}


def agent_lifecycle(ctx: dict[str, Any]) -> dict[str, Any]:
    src = source_text(ctx["source"])
    if not src["available"]:
        return {k: v for k, v in src.items() if k != "content"}
    code = src["content"]
    names = ("Popen", "wait(", "poll(", "terminate(", "kill(", "start_new_session", "openpty", "pipes.pop", "os.close")
    return {"path": str(ctx["source"]), "static_occurrences": {name: code.count(name) for name in names},
            "warning": "text counts do not prove runtime process lifecycle or reaping"}


def agent_resource(_: dict[str, Any]) -> dict[str, Any]:
    limits, limits_err = read_text(Path("/proc/self/limits"))
    meminfo, mem_err = read_text(Path("/proc/meminfo"))
    stat, stat_err = read_text(Path("/proc/stat"))
    selected_limits = [line for line in limits.splitlines()
                       if any(x in line for x in ("open files", "processes"))] if limits else []
    selected_mem = {}
    if meminfo:
        for line in meminfo.splitlines():
            if line.startswith(("MemTotal:", "MemAvailable:", "SwapTotal:", "SwapFree:")):
                selected_mem[line.split(":", 1)[0]] = line.split(":", 1)[1].strip()
    return {"limits": selected_limits, "limits_error": limits_err, "memory": selected_mem,
            "meminfo_error": mem_err, "proc_stat_available": stat is not None, "proc_stat_error": stat_err}


def agent_integrity(ctx: dict[str, Any]) -> dict[str, Any]:
    try:
        data = ctx["source"].read_bytes()
        if len(data) > MAX_SOURCE_BYTES:
            return {"path": str(ctx["source"]), "available": False, "reason": "size_limit_exceeded"}
        return {"path": str(ctx["source"]), "available": True, "size_bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest()}
    except Exception as exc:
        return {"path": str(ctx["source"]), "available": False, "reason": f"{type(exc).__name__}:{exc}"}


def agent_network(_: dict[str, Any]) -> dict[str, Any]:
    dev, dev_err = read_text(Path("/proc/net/dev"))
    route, route_err = read_text(Path("/proc/net/route"))
    return {"interfaces_text": dev, "interfaces_error": dev_err, "routes_text": route,
            "routes_error": route_err, "note": "local kernel tables only; no external scan or connection attempt"}


def agent_hermes(results: list[dict[str, Any]]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for item in results:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    return {"agents_in_cycle": len(results), "status_counts": counts,
            "agent_payload_hashes": {item["agent_id"]: item["payload_sha256"] for item in results}}


COLLECTORS = {
    AGENTS[0]: agent_health, AGENTS[1]: agent_spec, AGENTS[2]: agent_auth,
    AGENTS[3]: agent_socket, AGENTS[4]: agent_process, AGENTS[5]: agent_lifecycle,
    AGENTS[6]: agent_resource, AGENTS[7]: agent_integrity, AGENTS[8]: agent_network,
}


def append_jsonl(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True, ensure_ascii=False) + "\n")


def execute_agent(agent_id: str, collector, ctx: dict[str, Any], run_id: str) -> dict[str, Any]:
    started = utc_now()
    try:
        payload = collector(ctx)
        status = "observed" if payload.get("available", True) else "unavailable"
    except Exception as exc:
        payload = {"error": f"{type(exc).__name__}:{exc}"}
        status = "error"
    record = {"run_id": run_id, "timestamp_utc": started, "agent_id": agent_id,
              "status": status, "payload": payload, "payload_sha256": digest(payload)}
    append_jsonl(ctx["output"] / "observations" / agent_id / "events.jsonl", record)
    return record


def run_cycle(ctx: dict[str, Any], run_id: str) -> dict[str, Any]:
    records = []
    for agent_id in AGENTS[:-1]:
        records.append(execute_agent(agent_id, COLLECTORS[agent_id], ctx, run_id))
    hermes_payload = agent_hermes(records)
    hermes_record = {"run_id": run_id, "timestamp_utc": utc_now(), "agent_id": AGENTS[-1],
                     "status": "observed", "payload": hermes_payload, "payload_sha256": digest(hermes_payload)}
    append_jsonl(ctx["output"] / "observations" / AGENTS[-1] / "events.jsonl", hermes_record)
    records.append(hermes_record)
    consolidated = {"run_id": run_id, "timestamp_utc": utc_now(),
                    "agents": [{"agent_id": r["agent_id"], "status": r["status"],
                                "payload_sha256": r["payload_sha256"]} for r in records]}
    consolidated["record_sha256"] = digest(consolidated)
    append_jsonl(ctx["output"] / "observations" / "consolidated" / "events.jsonl", consolidated)
    return consolidated


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aurora-10 read-only observability pilot")
    parser.add_argument("--source", type=Path, default=DEFAULT_SOURCE, help="local source file to inspect")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT, help="local output directory")
    parser.add_argument("--duration-hours", type=float, default=24.0)
    parser.add_argument("--interval-seconds", type=int, default=300)
    parser.add_argument("--once", action="store_true", help="run one cycle and exit")
    args = parser.parse_args()
    if args.duration_hours <= 0 or args.duration_hours > MAX_DURATION_HOURS:
        parser.error(f"--duration-hours must be >0 and <= {MAX_DURATION_HOURS}")
    if args.interval_seconds < 60 or args.interval_seconds > MAX_INTERVAL_SECONDS:
        parser.error(f"--interval-seconds must be between 60 and {MAX_INTERVAL_SECONDS}")
    if args.output.resolve() == Path("/"):
        parser.error("output directory cannot be filesystem root")
    return args


def main() -> int:
    args = parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    run_id = str(uuid.uuid4())
    deadline = time.monotonic() if args.once else time.monotonic() + args.duration_hours * 3600
    ctx = {"source": args.source.resolve(), "output": output}
    cycle = 0
    try:
        while True:
            if (output / "STOP").exists():
                print("STOP file detected; stopping cooperatively.")
                break
            cycle += 1
            summary = run_cycle(ctx, run_id)
            print(json.dumps({"cycle": cycle, "summary": summary}, ensure_ascii=False))
            if args.once or time.monotonic() >= deadline:
                break
            next_run = min(time.monotonic() + args.interval_seconds, deadline)
            while time.monotonic() < next_run:
                if (output / "STOP").exists():
                    print("STOP file detected; stopping cooperatively.")
                    return 0
                time.sleep(min(2.0, max(0.1, next_run - time.monotonic())))
    except KeyboardInterrupt:
        print("Interrupted by operator; no target-service cleanup was needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
