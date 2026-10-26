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


def _verify_existing_path(path: Path, expected_digest: str) -> None:
    if path.is_symlink():
        raise RuntimeError("evidence destination must not be a symbolic link")
    if not path.exists() or not path.is_file():
        raise RuntimeError("existing evidence destination is not a regular file")
    actual_digest = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual_digest != expected_digest:
        raise RuntimeError("existing evidence path does not match expected full SHA-256")


def store_evidence(
    raw: bytes,
    kind: str,
    evidence_url: str | None = None,
    root: str | Path = "evidence",
) -> dict[str, str | None]:
    """Persist evidence safely and verify existing content before reuse.

    The filename keeps a 12-character digest prefix for compatibility, but the
    full SHA-256 is verified on reuse. Exclusive creation avoids overwriting a
    destination that appears after the initial existence check.
    """
    if not isinstance(raw, bytes):
        raise TypeError("raw must be bytes")
    safe_kind = _validate_kind(kind)
    digest = hashlib.sha256(raw).hexdigest()
    directory = Path(root)
    if directory.is_symlink():
        raise RuntimeError("evidence root must not be a symbolic link")
    directory.mkdir(parents=True, exist_ok=True)
    if directory.is_symlink() or not directory.is_dir():
        raise RuntimeError("evidence root must be a regular directory")
    path = directory / f"{safe_kind}_{digest[:12]}.bin"
    if path.is_symlink():
        raise RuntimeError("evidence destination must not be a symbolic link")
    if path.exists():
        _verify_existing_path(path, digest)
    else:
        try:
            with path.open("xb") as stream:
                stream.write(raw)
        except FileExistsError:
            _verify_existing_path(path, digest)
    return {"hash": digest, "path": str(path), "evidence_url": evidence_url}
