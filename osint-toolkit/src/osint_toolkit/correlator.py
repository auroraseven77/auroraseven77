from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from statistics import fmean
from .models import Observation


def load_observations(path: str | Path) -> list[Observation]:
    result: list[Observation] = []
    with Path(path).open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                result.append(Observation.model_validate_json(line))
    return result


def build_report(observations: list[Observation], risk_threshold: float = 0.7) -> dict:
    groups: dict[tuple[str, str], list[Observation]] = defaultdict(list)
    for item in observations:
        groups[(item.target, item.entity_type)].append(item)

    grouped = []
    for (target, entity_type), items in sorted(groups.items()):
        confidence = round(fmean(item.confidence for item in items), 4)
        errors = sum(item.status == "error" for item in items)
        risk = round(min(1.0, errors / max(1, len(items)) + (1.0 - confidence) * 0.5), 4)
        grouped.append({
            "target": target,
            "entity_type": entity_type,
            "observation_count": len(items),
            "confidence_composite": confidence,
            "risk": risk,
            "evidence_refs": [item.hash for item in items if item.hash],
            "human_review_required": risk >= risk_threshold,
        })

    return {
        "schema_version": "0.1",
        "observation_count": len(observations),
        "risk_threshold": risk_threshold,
        "groups": grouped,
        "human_review_required": any(group["human_review_required"] for group in grouped),
        "ai_authority": "advisory_only",
    }


def write_report(observations_path: str | Path, report_path: str | Path = "report.json", risk_threshold: float = 0.7) -> dict:
    report = build_report(load_observations(observations_path), risk_threshold)
    Path(report_path).write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return report
