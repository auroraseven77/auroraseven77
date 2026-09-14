from __future__ import annotations

import urllib.robotparser
from urllib.parse import urljoin
import requests
from ..evidence import store_evidence
from ..models import Observation

USER_AGENT = "osint-toolkit/0.1 (+authorized passive collection)"
TIMEOUT = 8


def collect(base_url: str, evidence_root: str = "evidence") -> list[Observation]:
    robots_url = urljoin(base_url, "/robots.txt")
    try:
        response = requests.get(robots_url, timeout=TIMEOUT, headers={"User-Agent": USER_AGENT})
        meta = store_evidence(response.content, "robots", robots_url, evidence_root)
        if response.status_code >= 400:
            return [Observation(source="robots", target=base_url, entity_type="robots", value=f"robots.txt status={response.status_code}", confidence=0.6, evidence_url=robots_url, hash=meta["hash"], status="skipped")]
        parser = urllib.robotparser.RobotFileParser()
        parser.parse(response.text.splitlines())
        return [
            Observation(source="robots", target=base_url, entity_type="robots", value=f"robots.txt ok ({len(response.content)} bytes)", confidence=0.8, evidence_url=robots_url, hash=meta["hash"]),
            Observation(source="robots", target=base_url, entity_type="robots", value=f"crawl_delay={parser.crawl_delay(USER_AGENT)} sitemaps={parser.site_maps()}", confidence=0.7, evidence_url=robots_url),
        ]
    except Exception as exc:
        return [Observation(source="robots", target=base_url, entity_type="robots", value=f"error: {type(exc).__name__}: {exc}", confidence=0.1, status="error")]
