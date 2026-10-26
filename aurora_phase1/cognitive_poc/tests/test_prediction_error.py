from dataclasses import FrozenInstanceError

import pytest

from aurora_phase1.cognitive_poc.prediction_error import (
    ComparisonOutcome,
    ComparisonRule,
    PredictionErrorProvenance,
    PredictionError,
    ResolutionStatus,
    UnresolvedPredictionError,
    compare_prediction,
)


def make_provenance(prediction_hash="abc123", prediction_timestamp_logical=1, comparison_timestamp_logical=2):
    return PredictionErrorProvenance(
        prediction_hash=prediction_hash,
        comparison_rule=ComparisonRule(rule_id="EQ-01", description="Exact equality"),
        prediction_timestamp_logical=prediction_timestamp_logical,
        observation_source="test",
        comparison_timestamp_logical=comparison_timestamp_logical,
    )


def equality_comparator(prediction, observed):
    if prediction == observed:
        return ComparisonOutcome.MATCH, None
    return ComparisonOutcome.MISMATCH, {"difference": True}


def not_comparable_comparator(prediction, observed):
    return ComparisonOutcome.NOT_COMPARABLE, None


def test_match_is_deterministic():
    result = compare_prediction(
        prediction=10,
        observed_value=10,
        prediction_hash="abc123",
        prediction_timestamp_logical=1,
        timestamp_logical=2,
        provenance=make_provenance(),
        comparator=equality_comparator,
    )
    assert result.outcome is ComparisonOutcome.MATCH
    assert result.error is None


def test_mismatch_represents_explicit_error():
    result = compare_prediction(
        prediction=10,
        observed_value=12,
        prediction_hash="abc123",
        prediction_timestamp_logical=1,
        timestamp_logical=3,
        provenance=make_provenance(comparison_timestamp_logical=3),
        comparator=equality_comparator,
    )
    assert result.outcome is ComparisonOutcome.MISMATCH
    assert result.error == {"difference": True}


def test_not_comparable_is_resolved_comparison_outcome():
    result = compare_prediction(
        prediction=10,
        observed_value="x",
        prediction_hash="abc123",
        prediction_timestamp_logical=1,
        timestamp_logical=4,
        provenance=make_provenance(comparison_timestamp_logical=4),
        comparator=not_comparable_comparator,
    )
    assert result.outcome is ComparisonOutcome.NOT_COMPARABLE
    assert result.error is None


def test_unknown_is_not_a_comparison_outcome():
    unresolved = UnresolvedPredictionError(
        prediction_hash="abc123",
        status=ResolutionStatus.UNKNOWN,
        timestamp_logical=5,
        reason="observation missing",
    )
    assert unresolved.status is ResolutionStatus.UNKNOWN
    assert unresolved.status.value not in {outcome.value for outcome in ComparisonOutcome}


def test_not_yet_decidable_is_explicit():
    unresolved = UnresolvedPredictionError(
        prediction_hash="abc123",
        status=ResolutionStatus.NOT_YET_DECIDABLE,
        timestamp_logical=6,
        reason="comparison rule unavailable",
    )
    assert unresolved.status is ResolutionStatus.NOT_YET_DECIDABLE


def test_prediction_error_is_immutable():
    result = PredictionError(
        prediction_hash="abc123",
        observed_value=10,
        outcome=ComparisonOutcome.MATCH,
        error=None,
        timestamp_logical=2,
    )
    with pytest.raises(FrozenInstanceError):
        result.observed_value = 11


def test_invalid_comparator_is_rejected():
    with pytest.raises(ValueError, match="comparator must be callable"):
        compare_prediction(
            prediction=1,
            observed_value=1,
            prediction_hash="abc123",
            prediction_timestamp_logical=0,
            timestamp_logical=1,
            provenance=make_provenance(prediction_timestamp_logical=0, comparison_timestamp_logical=1),
            comparator=None,
        )


def test_invalid_comparator_result_is_rejected():
    with pytest.raises(ValueError, match="comparator must return"):
        compare_prediction(
            prediction=1,
            observed_value=1,
            prediction_hash="abc123",
            prediction_timestamp_logical=0,
            timestamp_logical=1,
            provenance=make_provenance(prediction_timestamp_logical=0, comparison_timestamp_logical=1),
            comparator=lambda p, o: ComparisonOutcome.MATCH,
        )


def test_invalid_prediction_hash_is_rejected():
    with pytest.raises(ValueError, match="prediction_hash"):
        compare_prediction(
            prediction=1,
            observed_value=1,
            prediction_hash="",
            prediction_timestamp_logical=0,
            timestamp_logical=1,
            provenance=make_provenance(prediction_timestamp_logical=0, comparison_timestamp_logical=1),
            comparator=equality_comparator,
        )


def test_invalid_timestamp_is_rejected():
    with pytest.raises(ValueError, match="timestamp_logical"):
        compare_prediction(
            prediction=1,
            observed_value=1,
            prediction_hash="abc123",
            prediction_timestamp_logical=0,
            timestamp_logical=True,
            provenance=make_provenance(prediction_timestamp_logical=0, comparison_timestamp_logical=1),
            comparator=equality_comparator,
        )
