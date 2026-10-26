#!/usr/bin/env bash
# Read-only inventory of selected local MCP source files; never prints file contents.
set -u
printf '\n=== AURORA MCP — READ-ONLY SOURCE INVENTORY ===\n'
if ! command -v python3 >/dev/null 2>&1; then
  printf 'inventory_state=NOT_TESTED (python3 unavailable)\n'
  exit 2
fi

python3 - <<'PY'
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

MAX_FILES_PER_ROOT = 64
MAX_FILE_BYTES = 4 * 1024 * 1024
CHUNK_BYTES = 64 * 1024
SOURCE_SUFFIXES = {".js", ".cjs", ".mjs", ".py"}
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


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(CHUNK_BYTES), b""):
            digest.update(chunk)
    return digest.hexdigest()


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
            if isinstance(value, str) and value and len(value) <= 160:
                selected[key] = value
        scripts = data.get("scripts")
        if isinstance(scripts, dict):
            selected["script_names"] = sorted(
                key for key in scripts if isinstance(key, str) and len(key) <= 80
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
                    entry["sha256"] = digest_file(path)
                    entry["state"] = "HASHED_SOURCE_ONLY"
                    if path.name == "package.json":
                        item["package_metadata"] = safe_package_metadata(path)
        except OSError as exc:
            entry["state"] = "UNAVAILABLE"
            entry["error_type"] = type(exc).__name__
        item["files"].append(entry)
    roots.append(item)

print(json.dumps({
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
    "side_effects": "filesystem reads only; no network, no writes, no process start, no package scripts, no logs, env files, package-lock files, backups, or JSONL ledgers read",
    "disclosure": "prints file names, sizes, SHA-256 digests and allowlisted package metadata; never prints source contents or package script command values",
}, indent=2, sort_keys=True))
PY
