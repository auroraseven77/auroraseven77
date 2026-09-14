from __future__ import annotations

import dns.resolver
from ..models import Observation

RECORD_TYPES = ("A", "AAAA", "MX", "TXT", "NS", "CNAME")


def collect(domain: str) -> list[Observation]:
    """Passive DNS resolution only; no AXFR, brute force, or discovery."""
    out: list[Observation] = []
    resolver = dns.resolver.Resolver()
    resolver.lifetime = 5.0
    for rtype in RECORD_TYPES:
        try:
            for answer in resolver.resolve(domain, rtype):
                out.append(Observation(source="dns", target=domain, entity_type="dns", value=f"{rtype} {answer.to_text()}", confidence=0.9))
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            out.append(Observation(source="dns", target=domain, entity_type="dns", value=f"{rtype} <no answer>", confidence=0.9, status="skipped"))
        except Exception as exc:
            out.append(Observation(source="dns", target=domain, entity_type="dns", value=f"{rtype} error: {type(exc).__name__}: {exc}", confidence=0.1, status="error"))
    return out
