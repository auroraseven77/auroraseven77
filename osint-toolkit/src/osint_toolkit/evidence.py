from __future__ import annotations

import hashlib
from pathlib import Path


def store_evidence(raw: bytes, kind: str, evidence_url: str | None = None, root: str | Path = "evidence") -> dict[str, str | None]:
    """Persist immutable-by-content evidence and return SHA-256 metadata."""
    digest = hashlib.sha256(raw).hexdigest()
    directory = Path(root)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{kind}_{digest[:12]}.bin"
    if not path.exists():
        path.write_bytes(raw)
    return {"hash": digest, "path": str(path), "evidence_url": evidence_url}
