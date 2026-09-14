from osint_toolkit.correlator import build_report
from osint_toolkit.models import Observation


def test_report_groups_and_requires_human_review_on_low_confidence():
    observations = [
        Observation(source="a", target="example.com", entity_type="dns", value="A 1.2.3.4", confidence=0.9),
        Observation(source="b", target="example.com", entity_type="dns", value="A 5.6.7.8", confidence=0.2),
    ]
    report = build_report(observations, risk_threshold=0.3)
    assert report["observation_count"] == 2
    assert len(report["groups"]) == 1
    assert report["groups"][0]["human_review_required"] is True
    assert report["ai_authority"] == "advisory_only"
