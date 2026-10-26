#!/usr/bin/env bash
# Read-only inventory of selected local MCP source files; never prints file contents.
set -u
printf '\n=== AURORA MCP — READ-ONLY SOURCE INVENTORY ===\n'
if ! command -v python3 >/dev/null 2>&1; then
  printf 'inventory_state=NOT_TESTED (python3 unavailable)\n'
  exit 2
fi

python3 - "$@" <<'PY'
import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

parser = argparse.ArgumentParser(description="Bounded read-only Aurora MCP source inventory")
parser.add_argument("--summary", action="store_true", help="emit compact root summaries and manual-review candidates")
args = parser.parse_args()

MAX_FILES_PER_ROOT = 64
MAX_FILE_BYTES = 4 * 1024 * 1024
CHUNK_BYTES = 64 * 1024
SOURCE_SUFFIXES = {".js", ".cjs", ".mjs", ".py"}
SAFE_METADATA_VALUE = re.compile(r"^[A-Za-z0-9@._/+~-]{1,160}$")
SAFE_SCRIPT_NAME = re.compile(r"^[A-Za-z0-9:_-]{1,80}$")
SKIP_NAME_PARTS = ("token", "secret", "credential", "password", "private", "auth")


def skipped_name(name: str) -> bool:
    lower = name.lower()
    return (
        name.startswith(".")
        or lower in {".env", "package-lock.json"}
        or lower.startswith(".env.")
        or lower.endswith((".bak", ".log", ".jsonl", ".pem", ".key"))
        or any(part in lower for part in SKIP_NAME_PARTS)
    )


STATIC_MARKERS = {
    "process_execution": re.compile(r"\b(?:subprocess|popen|child_process|execsync|execfile|exec|spawn|fork|os\.system)\b"),
    "network_client": re.compile(r"\b(?:fetch|axios|requests\.|urllib|http\.client|socket\.)"),
    "network_listener": re.compile(r"\b(?:createserver|\.listen\s*\(|httpserver|socketserver)\b"),
    "filesystem_mutation": re.compile(r"\b(?:writefile(?:sync)?|write_bytes|write_text|unlink(?:sync)?|rmtree|mkdir|rename|replace)\b"),
    "environment_or_credential_access": re.compile(r"\b(?:process\.env|os\.environ|getenv|dotenv|credential|password|api[_-]?key|bearer)\b"),
    "dynamic_code": re.compile(r"\b(?:eval|new\s+function|compile\s*\()\b"),
    "mcp_tool_or_protocol": re.compile(r"\b(?:tools/list|tools/call|registertool|listtoolsrequestschema|calltoolrequestschema|modelcontextprotocol|mcpserver)\b"),
    "authorization_or_approval": re.compile(r"\b(?:authorize|authorization|authenticate|approval|allowlist|deny|default.?deny)\b"),
}


MAX_LINE_NUMBERS_PER_MARKER = 8
MANUAL_REVIEW_MARKERS = {
    "process_execution",
    "network_listener",
    "filesystem_mutation",
    "environment_or_credential_access",
    "dynamic_code",
}


def digest_and_markers(path: Path) -> tuple[str, dict, dict, dict]:
    """Hash raw bytes and collect bounded marker line numbers without exposing code."""
    digest = hashlib.sha256()
    counts = {name: 0 for name in STATIC_MARKERS}
    line_numbers = {name: [] for name in STATIC_MARKERS}
    with path.open("rb") as stream:
        for line_number, raw_line in enumerate(stream, start=1):
            digest.update(raw_line)
            line = raw_line.decode("utf-8", errors="replace").lower()
            for name, pattern in STATIC_MARKERS.items():
                if pattern.search(line):
                    counts[name] += 1
                    if len(line_numbers[name]) < MAX_LINE_NUMBERS_PER_MARKER:
                        line_numbers[name].append(line_number)
    active = {name: count for name, count in counts.items() if count}
    locations = {name: line_numbers[name] for name in active}
    truncated = {
        name: counts[name] > len(line_numbers[name])
        for name in active
        if counts[name] > len(line_numbers[name])
    }
    return digest.hexdigest(), active, locations, truncated


def safe_package_metadata(path: Path) -> dict:
    # Parse only the package manifest and emit an allowlist, never scripts/values.
    try:
        if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_FILE_BYTES:
            return {"state": "NOT_READ_UNSAFE_OR_TOO_LARGE"}
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return {"state": "INVALID_MANIFEST"}
        selected = {}
        for key in ("name", "version", "type", "main"):
            value = data.get(key)
            if isinstance(value, str) and SAFE_METADATA_VALUE.fullmatch(value):
                selected[key] = value
        scripts = data.get("scripts")
        if isinstance(scripts, dict):
            selected["script_names"] = sorted(
                key for key in scripts if isinstance(key, str) and SAFE_SCRIPT_NAME.fullmatch(key)
            )[:32]
        selected["state"] = "METADATA_ALLOWLISTED"
        return selected
    except Exception as exc:
        return {"state": "UNAVAILABLE", "error_type": type(exc).__name__}


home = Path.home()
roots = []
for label in ("mcp-aurora", "mcp-aurora-server"):
    root = home / label
    item = {"root": "~/" + label, "files": [], "truncated": False}
    if root.is_symlink():
        item["state"] = "SYMLINK_ROOT_SKIPPED"
        roots.append(item)
        continue
    if not root.exists():
        item["state"] = "ABSENT"
        roots.append(item)
        continue
    if not root.is_dir():
        item["state"] = "NOT_DIRECTORY"
        roots.append(item)
        continue

    item["state"] = "PRESENT"
    item["git_metadata"] = "PRESENT" if (root / ".git").exists() else "NOT_FOUND"
    try:
        children = sorted(root.iterdir(), key=lambda path: path.name)
    except OSError as exc:
        item["state"] = "PRESENT_BUT_UNREADABLE"
        item["error_type"] = type(exc).__name__
        roots.append(item)
        continue

    candidates = []
    for path in children:
        if skipped_name(path.name):
            continue
        if path.name == "package.json" or path.suffix.lower() in SOURCE_SUFFIXES:
            candidates.append(path)
    if len(candidates) > MAX_FILES_PER_ROOT:
        item["truncated"] = True
        candidates = candidates[:MAX_FILES_PER_ROOT]

    for path in candidates:
        entry = {"name": path.name}
        try:
            if path.is_symlink():
                entry["state"] = "SYMLINK_SKIPPED"
            elif not path.is_file():
                entry["state"] = "NOT_REGULAR_FILE"
            else:
                size = path.stat().st_size
                entry["size_bytes"] = size
                if size > MAX_FILE_BYTES:
                    entry["state"] = "TOO_LARGE_NOT_HASHED"
                else:
                    if path.name == "package.json":
                        entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
                        entry["state"] = "HASHED_MANIFEST_ONLY"
                        item["package_metadata"] = safe_package_metadata(path)
                    else:
                        entry["sha256"], markers, locations, truncated = digest_and_markers(path)
                        entry["state"] = "HASHED_SOURCE_ONLY"
                        entry["static_marker_lines"] = markers
                        entry["static_marker_line_numbers"] = locations
                        entry["static_marker_lines_truncated"] = truncated
                        review_reasons = sorted(MANUAL_REVIEW_MARKERS.intersection(markers))
                        entry["manual_review_suggested"] = bool(review_reasons)
                        if review_reasons:
                            entry["manual_review_marker_categories"] = review_reasons
        except OSError as exc:
            entry["state"] = "UNAVAILABLE"
            entry["error_type"] = type(exc).__name__
        item["files"].append(entry)
    roots.append(item)

report = {
    "schema_version": "1.0",
    "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    "state": "COMPLETED_READ_ONLY",
    "roots": roots,
    "limits": {
        "max_files_per_root": MAX_FILES_PER_ROOT,
        "max_file_bytes": MAX_FILE_BYTES,
        "hash_chunk_bytes": CHUNK_BYTES,
        "scope": "top-level regular .js/.cjs/.mjs/.py files plus package.json only",
    },
    "side_effects": "read-only local filesystem inspection; reads bounded source files for hashing and heuristic markers and reads package.json within the size cap for SHA-256 and allowlisted metadata/script names; never emits or executes package script command values; no network requests, file writes, or project/service process starts/stops; excludes logs, env files, package-lock files, backups, and JSONL ledgers",
    "static_triage": "heuristic counts and bounded line numbers for fixed execution/network/listener/filesystem/environment/dynamic-code/MCP/authorization patterns; counts and line locations are not proof of behavior or vulnerability",
    "manual_review": "manual_review_suggested is a triage flag for selected marker categories, not a vulnerability verdict or an execution decision",
    "max_line_numbers_per_marker": MAX_LINE_NUMBERS_PER_MARKER,
    "disclosure": "prints file names, sizes, SHA-256 digests, bounded marker line numbers/counts and allowlisted package metadata; never prints source contents or package script command values",
}
if args.summary:
    summarized_roots = []
    for root_item in roots:
        entries = root_item.get("files", [])
        source_entries = [entry for entry in entries if entry.get("state") == "HASHED_SOURCE_ONLY"]
        manifest_entries = [entry for entry in entries if entry.get("state") == "HASHED_MANIFEST_ONLY"]
        candidates = []
        for entry in source_entries:
            if not entry.get("manual_review_suggested"):
                continue
            candidates.append({
                "name": entry.get("name"),
                "sha256": entry.get("sha256"),
                "manual_review_marker_categories": entry.get("manual_review_marker_categories", []),
                "static_marker_lines": entry.get("static_marker_lines", {}),
                "static_marker_line_numbers": entry.get("static_marker_line_numbers", {}),
                "static_marker_lines_truncated": entry.get("static_marker_lines_truncated", {}),
            })
        marker_file_counts = {
            category: sum(category in entry.get("static_marker_lines", {}) for entry in source_entries)
            for category in STATIC_MARKERS
        }
        summarized_roots.append({
            "root": root_item.get("root"),
            "state": root_item.get("state"),
            "git_metadata": root_item.get("git_metadata", "NOT_TESTED"),
            "source_files_hashed": len(source_entries),
            "manifests_hashed": len(manifest_entries),
            "files_not_hashed_or_skipped": sum(
                entry.get("state") not in {"HASHED_SOURCE_ONLY", "HASHED_MANIFEST_ONLY"}
                for entry in entries
            ),
            "truncated": root_item.get("truncated", False),
            "marker_file_counts": {
                key: value for key, value in marker_file_counts.items() if value
            },
            "manual_review_candidate_count": len(candidates),
            "manual_review_candidates": candidates,
        })
    report["roots"] = summarized_roots
    report["view"] = "SUMMARY"
    report["summary_policy"] = "includes only review candidates with bounded line numbers and hashes; omits per-file entries without selected review markers; no source text is emitted"
else:
    report["view"] = "DETAIL"
print(json.dumps(report, indent=2, sort_keys=True))

PY
