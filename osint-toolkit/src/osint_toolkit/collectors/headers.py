from __future__ import annotations

import requests
from ..evidence import store_evidence
from ..models import Observation

USER_AGENT = "osint-toolkit/0.1 (+authorized passive collection)"
TIMEOUT = 8


def collect(url: str, evidence_root: str = "evidence") -> list[Observation]:
    """Perform one conservative HEAD request; never sends payloads or credentials."""
    try:
        response = requests.head(url, allow_redirects=True, timeout=TIMEOUT, headers={"User-Agent": USER_AGENT})
        # Headers themselves are serialized for evidence rather than hashing empty HEAD content.
        raw = (f"HTTP {response.status_code}\n" + "\n".join(f"{k}: {v}" for k, v in response.headers.items()) + "\n").encode()
        meta = store_evidence(raw, "headers", response.url, evidence_root)
        return [Observation(source="http", target=url, entity_type="http_header", value=f"{k}: {v}", confidence=0.85, evidence_url=response.url, hash=meta["hash"]) for k, v in response.headers.items()]
    except Exception as exc:
        return [Observation(source="http", target=url, entity_type="http_header", value=f"error: {type(exc).__name__}: {exc}", confidence=0.1, status="error")]
