from dataclasses import FrozenInstanceError

import pytest

from aurora_phase1.cognitive_poc.error_attribution import (
    AttributionAssessment,
    AttributionCriteria,
    AttributionProvenance,
    AttributionStatus,
    CandidateCause,
    CauseStatus,
)


def make_cause(cause_id="C1", status=CauseStatus.PLAUSIBLE):
    return CandidateCause(cause_id=cause_id, status=status)


def make_criteria():
    return AttributionCriteria(criteria_id="ATTR-01", description="Explicit evidence compatibility")


def make_provenance(error_timestamp=10, attribution_timestamp=11):
    return AttributionProvenance(
        prediction_hash="abc123",
        prediction_error_timestamp_logical=error_timestamp,
        candidate_causes=(make_cause(),),
        evidence={"source": "test"},
        criteria=make_criteria(),
        attribution_timestamp_logical=attribution_timestamp,
        evidence_source="test",
        evaluator_id="EVAL-01",
    )


def test_valid_attribution_assessment():
    assessment = AttributionAssessment(
        prediction_hash="abc123",
        prediction_error_timestamp_logical=10,
        candidate_causes=(make_cause("C1", CauseStatus.SUPPORTED),),
        attribution_status=AttributionStatus.RESOLVED,
        timestamp_logical=11,
    )
    assert assessment.attribution_status is AttributionStatus.RESOLVED


def test_canonical_attribution_has_exact_five_fields():
    assessment = AttributionAssessment("abc123", 10, (make_cause(),), AttributionStatus.ATTRIBUTION_UNRESOLVED, 11)
    assert set(assessment.canonical_object) == {
        "prediction_hash", "prediction_error_timestamp_logical", "candidate_causes", "attribution_status", "timestamp_logical"
    }


def test_multiple_compatible_causes_are_explicit():
    assessment = AttributionAssessment(
        "abc123", 10,
        (make_cause("C1", CauseStatus.PLAUSIBLE), make_cause("C2", CauseStatus.SUPPORTED)),
        AttributionStatus.MULTIPLE_COMPATIBLE, 11
    )
    assert assessment.attribution_status is AttributionStatus.MULTIPLE_COMPATIBLE
    assert len(assessment.candidate_causes) == 2


def test_unresolved_attribution_is_explicit():
    assessment = AttributionAssessment("abc123", 10, (make_cause(status=CauseStatus.INSUFFICIENT_EVIDENCE),), AttributionStatus.ATTRIBUTION_UNRESOLVED, 11)
    assert assessment.attribution_status is AttributionStatus.ATTRIBUTION_UNRESOLVED


def test_candidate_cause_is_immutable():
    cause = make_cause()
    with pytest.raises(FrozenInstanceError):
        cause.status = CauseStatus.SUPPORTED


def test_attribution_assessment_is_immutable():
    assessment = AttributionAssessment("abc123", 10, (make_cause(),), AttributionStatus.ATTRIBUTION_UNRESOLVED, 11)
    with pytest.raises(FrozenInstanceError):
        assessment.timestamp_logical = 12


def test_invalid_assessment_timestamp_is_rejected():
    with pytest.raises(ValueError, match="timestamp_logical"):
        AttributionAssessment("abc123", 10, (make_cause(),), AttributionStatus.ATTRIBUTION_UNRESOLVED, 10)


def test_invalid_candidate_container_is_rejected():
    with pytest.raises(ValueError, match="candidate_causes"):
        AttributionAssessment("abc123", 10, [make_cause()], AttributionStatus.ATTRIBUTION_UNRESOLVED, 11)


def test_invalid_provenance_timestamp_is_rejected():
    with pytest.raises(ValueError, match="attribution_timestamp_logical"):
        make_provenance(error_timestamp=10, attribution_timestamp=10)


def test_provenance_requires_criteria():
    with pytest.raises(ValueError, match="criteria"):
        AttributionProvenance("abc123", 10, (make_cause(),), {}, None, 11, "test", "EVAL-01")

from aurora_phase1.cognitive_poc.error_attribution import attribute_error

from aurora_phase1.cognitive_poc.prediction_error import ComparisonOutcome, PredictionError


def test_attribute_error_builds_assessment_from_prediction_error():
    prediction_error = PredictionError(
        prediction_hash="abc123",
        observed_value=42,
        outcome=ComparisonOutcome.MISMATCH,
        error=2,
        timestamp_logical=10,
    )
    criteria = make_criteria()
    causes = (make_cause("C1", CauseStatus.SUPPORTED),)
    def evaluator(*, prediction_error, cause, evidence, criteria):
        return cause.status

    assessment = attribute_error(
        prediction_error=prediction_error,
        candidate_causes=causes,
        criteria=criteria,
        evidence={"observation": "test"},
                evidence_source="test",
        evaluator_id="EVAL-01",
        timestamp_logical=11,
        evaluator=evaluator,
    )
    assert isinstance(assessment, AttributionAssessment)
    assert assessment.prediction_hash == "abc123"
    assert assessment.prediction_error_timestamp_logical == 10
    assert assessment.candidate_causes == causes
    assert assessment.attribution_status is AttributionStatus.RESOLVED
    assert assessment.timestamp_logical == 11

def test_attribute_error_requires_explicit_evidence_evaluation():
    prediction_error = PredictionError("abc123", 42, ComparisonOutcome.MISMATCH, 2, 10)
    criteria = make_criteria()
    causes = (make_cause("C1", CauseStatus.PLAUSIBLE),)
    with pytest.raises(ValueError, match="evaluator"):
        attribute_error(
            prediction_error=prediction_error,
            candidate_causes=causes,
            criteria=criteria,
            evidence={"observation": "test"},
                    evidence_source="test",
        evaluator_id="EVAL-01",
            timestamp_logical=11,
            evaluator=None,
        )

def test_attribute_error_accepts_deterministic_evaluator():
    prediction_error = PredictionError("abc123", 42, ComparisonOutcome.MISMATCH, 2, 10)
    criteria = make_criteria()
    causes = (CandidateCause("C1", CauseStatus.PLAUSIBLE),)
    def evaluator(*, prediction_error, cause, evidence, criteria):
        assert prediction_error.prediction_hash == "abc123"
        assert cause.cause_id == "C1"
        assert evidence == {"observation": "test"}
        assert criteria.criteria_id == "ATTR-01"
        return CauseStatus.SUPPORTED
    assessment = attribute_error(
        prediction_error=prediction_error,
        candidate_causes=causes,
        criteria=criteria,
        evidence={"observation": "test"},
                evidence_source="test",
        evaluator_id="EVAL-01",
        timestamp_logical=11,
        evaluator=evaluator,
    )
    assert assessment.candidate_causes == (CandidateCause("C1", CauseStatus.SUPPORTED),)
    assert assessment.attribution_status is AttributionStatus.RESOLVED
