from __future__ import annotations

import socket
import ssl
from datetime import datetime, timezone
from urllib.parse import urlparse
from ..evidence import store_evidence
from ..models import Observation

TIMEOUT = 8


def _subject(cert: dict, key: str) -> str:
    values = []
    for part in cert.get(key, ()):
        values.extend(v for k, v in part if k in {"commonName", "organizationName"})
    return ", ".join(values) or "<none>"


def collect(url: str, evidence_root: str = "evidence") -> list[Observation]:
    host = urlparse(url).hostname
    if not host:
        return [Observation(source="tls", target=url, entity_type="tls_cert", value="invalid host", confidence=0.1, status="error")]
    context = ssl.create_default_context()
    try:
        with socket.create_connection((host, 443), timeout=TIMEOUT) as sock:
            with context.wrap_socket(sock, server_hostname=host) as tls_sock:
                cert = tls_sock.getpeercert()
                der = tls_sock.getpeercert(binary_form=True) or b""
                meta = store_evidence(der, "tls", f"https://{host}", evidence_root)
                sans = [value for kind, value in cert.get("subjectAltName", ()) if kind == "DNS"]
                not_after = cert.get("notAfter")
                validity = "unknown"
                if not_after:
                    try:
                        expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
                        validity = "valid" if expiry > datetime.now(timezone.utc) else "expired"
                    except ValueError:
                        validity = "unparsed"
                return [
                    Observation(source="tls", target=host, entity_type="tls_cert", value=f"subject={_subject(cert, 'subject')}", confidence=0.9, evidence_url=f"https://{host}", hash=meta["hash"]),
                    Observation(source="tls", target=host, entity_type="tls_cert", value=f"issuer={_subject(cert, 'issuer')} notAfter={not_after} validity={validity}", confidence=0.9, evidence_url=f"https://{host}"),
                    Observation(source="tls", target=host, entity_type="tls_cert", value=f"SAN={','.join(sans) if sans else '<none>'}", confidence=0.9, evidence_url=f"https://{host}"),
                ]
    except Exception as exc:
        return [Observation(source="tls", target=host, entity_type="tls_cert", value=f"error: {type(exc).__name__}: {exc}", confidence=0.1, status="error")]
