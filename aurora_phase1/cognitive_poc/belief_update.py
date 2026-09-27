"""Immutable Belief Update primitives for Cognitive Core Block 7."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from aurora_phase1.cognitive_poc.belief_state import BeliefState
from aurora_phase1.cognitive_poc.cognitive_evidence import (
    CognitiveEvidence,
    CognitiveEvidenceOccurrence,
)
from aurora_phase1.core.crypto import hash_object


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType({k: _freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, tuple):
        return tuple(_freeze(v) for v in value)
    if isinstance(value, set):
        return frozenset(_freeze(v) for v in value)
    return value


def _plain(value: Any) -> Any:
    if isinstance(value, MappingProxyType):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, Mapping):
        return {k: _plain(v) for k, v in value.items()}
    if isinstance(value, tuple):
        return [_plain(v) for v in value]
    if isinstance(value, frozenset):
        return sorted(_plain(v) for v in value)
    return value


@dataclass(frozen=True)
class UpdateRule:
    """Stable, versioned and deterministically represented update rule."""

    rule_id: str
    version: str
    representation: str
    parameters: Mapping[str, Any]

    def __post_init__(self) -> None:
        for name, value in (
            ("rule_id", self.rule_id),
            ("version", self.version),
            ("representation", self.representation),
        ):
            if not isinstance(value, str) or not value:
                raise ValueError(f"{name} must be a non-empty string")

        if not isinstance(self.parameters, Mapping):
            raise TypeError("parameters must be a mapping")

        object.__setattr__(self, "parameters", _freeze(dict(self.parameters)))

    @property
    def canonical_object(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "version": self.version,
            "representation": self.representation,
            "parameters": _plain(self.parameters),
        }

    @property
    def rule_identity(self) -> str:
        return hash_object(self.canonical_object)


class BeliefUpdateOutcome(str, Enum):
    UPDATE = "UPDATE"
    NO_UPDATE = "NO_UPDATE"
    REJECT_UPDATE = "REJECT_UPDATE"
    REQUIRE_MORE_EVIDENCE = "REQUIRE_MORE_EVIDENCE"


@dataclass(frozen=True)
class BeliefUpdate:
    """Immutable historical relation from prior belief to successor belief."""

    prior_identity: str
    evidence_id: str
    update_rule: UpdateRule
    successor_identity: str | None
    occurrence_id: str | None = None
    outcome: BeliefUpdateOutcome = BeliefUpdateOutcome.UPDATE

    def __post_init__(self) -> None:
        for name, value in (
            ("prior_identity", self.prior_identity),
            ("evidence_id", self.evidence_id),
        ):
            if not isinstance(value, str) or not value:
                raise ValueError(f"{name} must be a non-empty string")

        if self.successor_identity is not None:
            if not isinstance(self.successor_identity, str) or not self.successor_identity:
                raise ValueError("successor_identity must be a non-empty string or None")

        if self.occurrence_id is not None:
            if not isinstance(self.occurrence_id, str) or not self.occurrence_id:
                raise ValueError("occurrence_id must be a non-empty string")

        if not isinstance(self.update_rule, UpdateRule):
            raise TypeError("update_rule must be UpdateRule")

        if not isinstance(self.outcome, BeliefUpdateOutcome):
            raise TypeError("outcome must be BeliefUpdateOutcome")

        if self.outcome is BeliefUpdateOutcome.UPDATE:
            if self.successor_identity is None:
                raise ValueError("UPDATE requires successor_identity")
            if self.prior_identity == self.successor_identity:
                raise ValueError(
                    "effective update must produce a new belief identity"
                )
        elif self.successor_identity is not None:
            raise ValueError("non-UPDATE outcome must not have successor_identity")

    @property
    def canonical_object(self) -> dict[str, Any]:
        return {
            "prior_identity": self.prior_identity,
            "evidence_id": self.evidence_id,
            "occurrence_id": self.occurrence_id,
            "update_rule": self.update_rule.canonical_object,
            "successor_identity": self.successor_identity,
            "outcome": self.outcome.value,
        }

    @property
    def update_identity(self) -> str:
        return hash_object(self.canonical_object)


def validate_belief_update(
    belief_update: BeliefUpdate,
    *,
    prior_state: BeliefState,
    successor_state: BeliefState | None,
    evidence: CognitiveEvidence,
    occurrence: CognitiveEvidenceOccurrence | None = None,
) -> None:
    """Deterministically validate the B7 identity and lineage boundary."""

    if not isinstance(belief_update, BeliefUpdate):
        raise TypeError("belief_update must be BeliefUpdate")

    if belief_update.prior_identity != prior_state.belief_identity:
        raise ValueError("prior_identity does not match prior_state")

    if belief_update.evidence_id != evidence.evidence_id:
        raise ValueError("evidence_id does not match evidence")

    if belief_update.occurrence_id is not None:
        if occurrence is None:
            raise ValueError(
                "occurrence is required when occurrence_id is present"
            )
        if belief_update.occurrence_id != occurrence.occurrence_id:
            raise ValueError("occurrence_id does not match occurrence")
        if occurrence.evidence_id != belief_update.evidence_id:
            raise ValueError(
                "occurrence.evidence_id does not match evidence_id"
            )

    if belief_update.outcome is BeliefUpdateOutcome.UPDATE:
        if successor_state is None:
            raise ValueError("successor_state is required for UPDATE")
        if successor_state.belief_identity != belief_update.successor_identity:
            raise ValueError("successor_identity does not match successor_state")
        if successor_state.belief_identity == prior_state.belief_identity:
            raise ValueError("successor must have a new belief identity")
        if successor_state.timestamp_logical <= prior_state.timestamp_logical:
            raise ValueError("successor timestamp must strictly increase")
    elif successor_state is not None:
        raise ValueError("non-UPDATE outcome must not have successor_state")
