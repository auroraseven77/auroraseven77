from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse
from .collectors import dns, headers, robots, tls
from .models import Observation
from .policy import authorize


def run(target: str, allowed_targets: list[str] | tuple[str, ...], out_path: str = "observations.jsonl", evidence_root: str = "evidence") -> list[Observation]:
    """Run only passive collectors after explicit scope authorization."""
    authorize(target, allowed_targets)
    observations: list[Observation] = []
    if "://" in target:
        parsed = urlparse(target)
        if parsed.scheme not in {"http", "https"} or not parsed.hostname:
            raise ValueError("target must be a valid HTTP(S) URL")
        observations += headers.collect(target, evidence_root)
        observations += robots.collect(target, evidence_root)
        if parsed.scheme == "https":
            observations += tls.collect(target, evidence_root)
    else:
        observations += dns.collect(target)

    output = Path(out_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("a", encoding="utf-8") as stream:
        for observation in observations:
            stream.write(observation.model_dump_json() + "\n")
    return observations
