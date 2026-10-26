"""Immutable prediction-error primitives for Cognitive Core Block 3."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ComparisonOutcome(Enum):
    """Resolved outcome of an explicit prediction/observation comparison."""

    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    NOT_COMPARABLE = "NOT_COMPARABLE"


class ResolutionStatus(Enum):
    """Epistemic resolution status for prediction-error evaluation."""

    UNKNOWN = "UNKNOWN"
    NOT_YET_DECIDABLE = "NOT_YET_DECIDABLE"


@dataclass(frozen=True)
class ComparisonRule:
    """Immutable identity and description of the comparison rule."""

    rule_id: str
    description: str

    def __post_init__(self) -> None:
        if not isinstance(self.rule_id, str) or not self.rule_id:
            raise ValueError("rule_id must be a non-empty string")
        if not isinstance(self.description, str) or not self.description:
            raise ValueError("description must be a non-empty string")


@dataclass(frozen=True)
class PredictionErrorProvenance:
    """Audit context kept outside the canonical prediction-error object."""

    prediction_hash: str
    comparison_rule: ComparisonRule
    prediction_timestamp_logical: int
    observation_source: str
    comparison_timestamp_logical: int

    def __post_init__(self) -> None:
        if not isinstance(self.prediction_hash, str) or not self.prediction_hash:
            raise ValueError("prediction_hash must be a non-empty string")
        if not isinstance(self.comparison_rule, ComparisonRule):
            raise ValueError("comparison_rule must be a ComparisonRule")
        if not isinstance(self.prediction_timestamp_logical, int) or isinstance(self.prediction_timestamp_logical, bool):
            raise ValueError("prediction_timestamp_logical must be an integer")
        if not isinstance(self.observation_source, str) or not self.observation_source:
            raise ValueError("observation_source must be a non-empty string")
        if not isinstance(self.comparison_timestamp_logical, int) or isinstance(self.comparison_timestamp_logical, bool):
            raise ValueError("comparison_timestamp_logical must be an integer")
        if self.comparison_timestamp_logical <= self.prediction_timestamp_logical:
            raise ValueError("comparison_timestamp_logical must be greater than prediction_timestamp_logical")


def compare_prediction(*, prediction: object, observed_value: object, prediction_hash: str, prediction_timestamp_logical: int, timestamp_logical: int, comparator, provenance: PredictionErrorProvenance) -> "PredictionError":
    if not callable(comparator):
        raise ValueError("comparator must be callable")
    if not isinstance(provenance, PredictionErrorProvenance):
        raise ValueError("provenance must be a PredictionErrorProvenance")
    if not isinstance(prediction_hash, str) or not prediction_hash:
        raise ValueError("prediction_hash must be a non-empty string")
    if not isinstance(prediction_timestamp_logical, int) or isinstance(prediction_timestamp_logical, bool):
        raise ValueError("prediction_timestamp_logical must be an integer")
    if not isinstance(timestamp_logical, int) or isinstance(timestamp_logical, bool):
        raise ValueError("timestamp_logical must be an integer")
    if timestamp_logical <= prediction_timestamp_logical:
        raise ValueError("timestamp_logical must be greater than prediction_timestamp_logical")
    if provenance.prediction_hash != prediction_hash:
        raise ValueError("provenance prediction_hash must match prediction_hash")
    if provenance.prediction_timestamp_logical != prediction_timestamp_logical:
        raise ValueError("provenance prediction timestamp must match prediction_timestamp_logical")
    if provenance.comparison_timestamp_logical != timestamp_logical:
        raise ValueError("provenance comparison timestamp must match timestamp_logical")
    result = comparator(prediction, observed_value)
    if not isinstance(result, tuple) or len(result) != 2:
        raise ValueError("comparator must return (outcome, error)")
    outcome, error = result
    if not isinstance(outcome, ComparisonOutcome):
        raise ValueError("comparator outcome must be a ComparisonOutcome")
    return PredictionError(prediction_hash=prediction_hash, observed_value=observed_value, outcome=outcome, error=error, timestamp_logical=timestamp_logical)


@dataclass(frozen=True)
class PredictionError:
    """Immutable resolved representation of prediction error."""

    prediction_hash: str
    observed_value: Any
    outcome: ComparisonOutcome
    error: Any
    timestamp_logical: int

    def __post_init__(self) -> None:
        if not isinstance(self.prediction_hash, str) or not self.prediction_hash:
            raise ValueError("prediction_hash must be a non-empty string")
        if not isinstance(self.outcome, ComparisonOutcome):
            raise ValueError("outcome must be a ComparisonOutcome")
        if not isinstance(self.timestamp_logical, int) or isinstance(
            self.timestamp_logical, bool
        ):
            raise ValueError("timestamp_logical must be an integer")


@dataclass(frozen=True)
class UnresolvedPredictionError:
    """Explicit unresolved state without fabricating a resolved error."""

    prediction_hash: str
    status: ResolutionStatus
    timestamp_logical: int
    reason: str

    def __post_init__(self) -> None:
        if not isinstance(self.prediction_hash, str) or not self.prediction_hash:
            raise ValueError("prediction_hash must be a non-empty string")
        if self.status not in (
            ResolutionStatus.UNKNOWN,
            ResolutionStatus.NOT_YET_DECIDABLE,
        ):
            raise ValueError(
                "unresolved prediction error requires UNKNOWN or "
                "NOT_YET_DECIDABLE"
            )
        if not isinstance(self.timestamp_logical, int) or isinstance(
            self.timestamp_logical, bool
        ):
            raise ValueError("timestamp_logical must be an integer")
        if not isinstance(self.reason, str) or not self.reason:
            raise ValueError("reason must be a non-empty string")
