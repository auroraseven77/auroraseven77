from __future__ import annotations

import hashlib
import re
from pathlib import Path

_KIND_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def _validate_kind(kind: str) -> str:
    """Reject path separators and traversal tokens before touching the filesystem."""
    if not isinstance(kind, str) or not _KIND_RE.fullmatch(kind) or kind in {".", ".."}:
        raise ValueError("kind must be a safe filename token (letters, digits, dot, underscore, hyphen)")
    return kind


def store_evidence(
    raw: bytes,
    kind: str,
    evidence_url: str | None = None,
    root: str | Path = "evidence",
) -> dict[str, str | None]:
    """Persist evidence and fail closed if a shortened-hash path contains different bytes."""
    safe_kind = _validate_kind(kind)
    digest = hashlib.sha256(raw).hexdigest()
    directory = Path(root)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{safe_kind}_{digest[:12]}.bin"
    if path.exists():
        existing_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if existing_digest != digest:
            raise RuntimeError("existing evidence path does not match expected full SHA-256")
    else:
        path.write_bytes(raw)
    return {"hash": digest, "path": str(path), "evidence_url": evidence_url}
