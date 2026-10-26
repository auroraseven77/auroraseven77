"""Immutable error-attribution primitives for Cognitive Core Block 4."""

from dataclasses import dataclass
from enum import Enum
from typing import Any


class CauseStatus(Enum):
    SUPPORTED = "SUPPORTED"
    PLAUSIBLE = "PLAUSIBLE"
    INCONSISTENT = "INCONSISTENT"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class AttributionStatus(Enum):
    RESOLVED = "RESOLVED"
    MULTIPLE_COMPATIBLE = "MULTIPLE_COMPATIBLE"
    ATTRIBUTION_UNRESOLVED = "ATTRIBUTION_UNRESOLVED"


@dataclass(frozen=True)
class AttributionCriteria:
    criteria_id: str
    description: str

    def __post_init__(self) -> None:
        if not isinstance(self.criteria_id, str) or not self.criteria_id:
            raise ValueError("criteria_id must be a non-empty string")
        if not isinstance(self.description, str) or not self.description:
            raise ValueError("description must be a non-empty string")


@dataclass(frozen=True)
class CandidateCause:
    cause_id: str
    status: CauseStatus

    def __post_init__(self) -> None:
        if not isinstance(self.cause_id, str) or not self.cause_id:
            raise ValueError("cause_id must be a non-empty string")
        if not isinstance(self.status, CauseStatus):
            raise ValueError("status must be a CauseStatus")


@dataclass(frozen=True)
class AttributionProvenance:
    prediction_hash: str
    prediction_error_timestamp_logical: int
    candidate_causes: tuple[CandidateCause, ...]
    evidence: Any
    criteria: AttributionCriteria
    attribution_timestamp_logical: int
    evidence_source: str
    evaluator_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.prediction_hash, str) or not self.prediction_hash:
            raise ValueError("prediction_hash must be a non-empty string")
        if not isinstance(self.prediction_error_timestamp_logical, int) or isinstance(self.prediction_error_timestamp_logical, bool):
            raise ValueError("prediction_error_timestamp_logical must be an integer")
        if not isinstance(self.candidate_causes, tuple):
            raise ValueError("candidate_causes must be a tuple")
        if not all(isinstance(cause, CandidateCause) for cause in self.candidate_causes):
            raise ValueError("candidate_causes must contain CandidateCause values")
        if not isinstance(self.evidence_source, str) or not self.evidence_source:
            raise ValueError("evidence_source must be a non-empty string")
        if not isinstance(self.criteria, AttributionCriteria):
            raise ValueError("criteria must be an AttributionCriteria")
        if not isinstance(self.attribution_timestamp_logical, int) or isinstance(self.attribution_timestamp_logical, bool):
            raise ValueError("attribution_timestamp_logical must be an integer")
        if self.attribution_timestamp_logical <= self.prediction_error_timestamp_logical:
            raise ValueError("attribution_timestamp_logical must be greater than prediction_error_timestamp_logical")


@dataclass(frozen=True)
class AttributionAssessment:
    prediction_hash: str
    prediction_error_timestamp_logical: int
    candidate_causes: tuple[CandidateCause, ...]
    attribution_status: AttributionStatus
    timestamp_logical: int

    def __post_init__(self) -> None:
        if not isinstance(self.prediction_hash, str) or not self.prediction_hash:
            raise ValueError("prediction_hash must be a non-empty string")
        if not isinstance(self.prediction_error_timestamp_logical, int) or isinstance(self.prediction_error_timestamp_logical, bool):
            raise ValueError("prediction_error_timestamp_logical must be an integer")
        if not isinstance(self.candidate_causes, tuple):
            raise ValueError("candidate_causes must be a tuple")
        if not all(isinstance(cause, CandidateCause) for cause in self.candidate_causes):
            raise ValueError("candidate_causes must contain CandidateCause values")
        if not isinstance(self.attribution_status, AttributionStatus):
            raise ValueError("attribution_status must be an AttributionStatus")
        if not isinstance(self.timestamp_logical, int) or isinstance(self.timestamp_logical, bool):
            raise ValueError("timestamp_logical must be an integer")
        if self.timestamp_logical <= self.prediction_error_timestamp_logical:
            raise ValueError("timestamp_logical must be greater than prediction_error_timestamp_logical")

    @property
    def canonical_object(self) -> dict[str, Any]:
        return {
            "prediction_hash": self.prediction_hash,
            "prediction_error_timestamp_logical": self.prediction_error_timestamp_logical,
            "candidate_causes": [
                {"cause_id": c.cause_id, "status": c.status.value}
                for c in self.candidate_causes
            ],
            "attribution_status": self.attribution_status.value,
            "timestamp_logical": self.timestamp_logical,
        }

def attribute_error(*, prediction_error, candidate_causes, criteria, evidence, evidence_source, timestamp_logical, evaluator_id, evaluator):
    from aurora_phase1.cognitive_poc.prediction_error import PredictionError

    if not callable(evaluator):
        raise ValueError("evaluator must be callable")
    if not isinstance(prediction_error, PredictionError):
        raise ValueError("prediction_error must be a resolved PredictionError")
    if not isinstance(candidate_causes, tuple):
        raise ValueError("candidate_causes must be a tuple")
    if not all(isinstance(cause, CandidateCause) for cause in candidate_causes):
        raise ValueError("candidate_causes must contain CandidateCause values")
    if not isinstance(criteria, AttributionCriteria):
        raise ValueError("criteria must be an AttributionCriteria")
    if not isinstance(evidence_source, str) or not evidence_source:
        raise ValueError("evidence_source must be a non-empty string")
    if not isinstance(evaluator_id, str) or not evaluator_id:
        raise ValueError("evaluator_id must be a non-empty string")
    if not isinstance(timestamp_logical, int) or isinstance(timestamp_logical, bool):
        raise ValueError("timestamp_logical must be an integer")
    if timestamp_logical <= prediction_error.timestamp_logical:
        raise ValueError("timestamp_logical must be greater than prediction_error.timestamp_logical")

    evaluated_causes = tuple(
        CandidateCause(
            cause_id=cause.cause_id,
            status=evaluator(
                prediction_error=prediction_error,
                cause=cause,
                evidence=evidence,
                criteria=criteria,
            ),
        )
        for cause in candidate_causes
    )
    if not all(isinstance(cause.status, CauseStatus) for cause in evaluated_causes):
        raise ValueError("evaluator must return a CauseStatus")
    compatible = tuple(
        cause
        for cause in evaluated_causes
        if cause.status in (CauseStatus.SUPPORTED, CauseStatus.PLAUSIBLE)
    )
    if len(compatible) == 1 and compatible[0].status is CauseStatus.SUPPORTED:
        status = AttributionStatus.RESOLVED
    elif len(compatible) >= 2:
        status = AttributionStatus.MULTIPLE_COMPATIBLE
    else:
        status = AttributionStatus.ATTRIBUTION_UNRESOLVED

    provenance = AttributionProvenance(
        prediction_hash=prediction_error.prediction_hash,
        prediction_error_timestamp_logical=prediction_error.timestamp_logical,
        candidate_causes=evaluated_causes,
        evidence=evidence,
        criteria=criteria,
        attribution_timestamp_logical=timestamp_logical,
        evidence_source=evidence_source,
        evaluator_id=evaluator_id,
    )
    return AttributionAssessment(
        prediction_hash=prediction_error.prediction_hash,
        prediction_error_timestamp_logical=prediction_error.timestamp_logical,
        candidate_causes=evaluated_causes,
        attribution_status=status,
        timestamp_logical=timestamp_logical,
    )
