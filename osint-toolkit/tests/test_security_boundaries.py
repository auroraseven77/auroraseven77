from pathlib import Path

import pytest
from pydantic import ValidationError

from osint_toolkit.correlator import build_report
from osint_toolkit.models import Observation
from osint_toolkit.pipeline import run
from osint_toolkit.policy import AuthorizationError, authorize, normalize_target


def test_normalization_rejects_unsupported_scheme_and_hostless_url():
    with pytest.raises(AuthorizationError):
        normalize_target("ftp://example.com")
    with pytest.raises(AuthorizationError):
        normalize_target("https:///missing-host")


def test_scope_rejects_suffix_confusion_and_sibling_domain():
    with pytest.raises(AuthorizationError):
        authorize("example.com.attacker.invalid", ["example.com"])
    with pytest.raises(AuthorizationError):
        authorize("https://other.example.net", ["example.com"])


def test_empty_allow_list_fails_closed():
    with pytest.raises(AuthorizationError, match="no authorized targets"):
        authorize("example.com", [])


def test_observation_rejects_out_of_range_confidence_and_bad_digest():
    base = {
        "source": "synthetic",
        "target": "example.com",
        "entity_type": "dns",
        "value": "A 192.0.2.1",
        "confidence": 0.9,
    }
    with pytest.raises(ValidationError):
        Observation(**{**base, "confidence": 1.01})
    with pytest.raises(ValidationError):
        Observation(**{**base, "hash": "not-a-sha256"})


def test_denied_pipeline_has_no_output_or_evidence_side_effects(tmp_path: Path):
    output = tmp_path / "nested" / "observations.jsonl"
    evidence = tmp_path / "evidence"
    with pytest.raises(AuthorizationError):
        run(
            "https://outside.example.net",
            ["example.com"],
            out_path=str(output),
            evidence_root=str(evidence),
        )
    assert not output.parent.exists()
    assert not evidence.exists()


def test_report_is_advisory_and_escalates_error_observation():
    item = Observation(
        source="synthetic",
        target="example.com",
        entity_type="dns",
        value="timeout",
        confidence=0.5,
        status="error",
        hash="a" * 64,
    )
    report = build_report([item], risk_threshold=0.7)
    assert report["observation_count"] == 1
    assert report["ai_authority"] == "advisory_only"
    assert report["human_review_required"] is True
    assert report["groups"][0]["evidence_refs"] == ["a" * 64]
