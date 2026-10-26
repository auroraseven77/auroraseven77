from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any, Mapping

from aurora_phase1.core.crypto import hash_object


class SemanticType(str, Enum):
    EPISTEMIC_ASSERTION = "EPISTEMIC_ASSERTION"
    PROPOSITION = "PROPOSITION"
    OBSERVATION = "OBSERVATION"
    MEASUREMENT = "MEASUREMENT"
    EXTERNAL_EVENT = "EXTERNAL_EVENT"
    EXTERNAL_STATE = "EXTERNAL_STATE"
    RELATION = "RELATION"
    DERIVED_OBJECT = "DERIVED_OBJECT"
    COMPOSITE_OBJECT = "COMPOSITE_OBJECT"


class OccurrenceType(str, Enum):
    OBSERVATION = "OBSERVATION"
    PRODUCTION = "PRODUCTION"
    AVAILABILITY = "AVAILABILITY"
    COMPOSITE = "COMPOSITE"


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
    if isinstance(value, Enum):
        return value.value
    return value


def _require_nonempty_text(name: str, value: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{name} must be a non-empty string")
    return value


@dataclass(frozen=True)
class CognitiveEvidence:
    semantic_type: SemanticType
    type_version: str
    constitutive_projection: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.semantic_type, SemanticType):
            raise TypeError("semantic_type must be SemanticType")
        _require_nonempty_text("type_version", self.type_version)
        if not isinstance(self.constitutive_projection, Mapping):
            raise TypeError("constitutive_projection must be a mapping")
        object.__setattr__(
            self,
            "constitutive_projection",
            _freeze(dict(self.constitutive_projection)),
        )

    @property
    def canonical_object(self) -> dict[str, Any]:
        return {
            "semantic_type": self.semantic_type.value,
            "type_version": self.type_version,
            "constitutive_projection": _plain(self.constitutive_projection),
        }

    @property
    def evidence_id(self) -> str:
        return hash_object(self.canonical_object)


@dataclass(frozen=True)
class CognitiveEvidenceOccurrence:
    evidence_id: str
    occurrence_type: OccurrenceType
    type_version: str
    normalized_occurrence_semantics: Mapping[str, Any]

    def __post_init__(self) -> None:
        _require_nonempty_text("evidence_id", self.evidence_id)
        if not isinstance(self.occurrence_type, OccurrenceType):
            raise TypeError("occurrence_type must be OccurrenceType")
        _require_nonempty_text("type_version", self.type_version)
        if not isinstance(self.normalized_occurrence_semantics, Mapping):
            raise TypeError("normalized_occurrence_semantics must be a mapping")
        object.__setattr__(
            self,
            "normalized_occurrence_semantics",
            _freeze(dict(self.normalized_occurrence_semantics)),
        )

    @property
    def canonical_object(self) -> dict[str, Any]:
        return {
            "evidence_id": self.evidence_id,
            "occurrence_type": self.occurrence_type.value,
            "type_version": self.type_version,
            "normalized_occurrence_semantics": _plain(
                self.normalized_occurrence_semantics
            ),
        }

    @property
    def occurrence_id(self) -> str:
        return hash_object(self.canonical_object)


__all__ = [
    "CognitiveEvidence",
    "CognitiveEvidenceOccurrence",
    "SemanticType",
    "OccurrenceType",
]
