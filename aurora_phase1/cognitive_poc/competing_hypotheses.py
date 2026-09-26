"""Immutable competing-hypotheses primitives for Cognitive Core Block 5."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType
from typing import Any


def _freeze_json_value(value: Any) -> Any:
    """Recursively freeze JSON-like values without importing authorization code."""
    if isinstance(value, dict):
        return MappingProxyType(
            {str(key): _freeze_json_value(item) for key, item in value.items()}
        )
    if isinstance(value, list):
        return tuple(_freeze_json_value(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze_json_value(item) for item in value)
    if isinstance(value, float):
        if not isfinite(value):
            raise ValueError("proposition must contain only finite JSON numbers")
        return value
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    raise ValueError(
        f"proposition must be JSON-like, got {type(value).__name__}"
    )


def _thaw_json_value(value: Any) -> Any:
    """Return a JSON-serializable copy of a frozen JSON-like value."""
    if isinstance(value, MappingProxyType):
        return {key: _thaw_json_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json_value(item) for item in value]
    return value


@dataclass(frozen=True)
class Hypothesis:
    """Immutable explanatory hypothesis."""

    hypothesis_id: str
    proposition: Any

    def __post_init__(self) -> None:
        if not isinstance(self.hypothesis_id, str) or not self.hypothesis_id:
            raise ValueError("hypothesis_id must be a non-empty string")
        object.__setattr__(
            self,
            "proposition",
            _freeze_json_value(self.proposition),
        )


@dataclass(frozen=True)
class HypothesisSetProvenance:
    """Provenance kept separate from canonical hypothesis-set state."""

    question_context: Any
    evidence: Any
    source: str
    criteria: Any
    evaluator_id: str
    timestamp_logical: int
    prediction_commitment_refs: tuple[str, ...] = ()
    prediction_error_refs: tuple[tuple[str, int], ...] = ()
    attribution_assessment_refs: tuple[tuple[str, int], ...] = ()
    external_model_involvement: Any = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "question_context", _freeze_json_value(self.question_context))
        object.__setattr__(self, "evidence", _freeze_json_value(self.evidence))
        object.__setattr__(self, "criteria", _freeze_json_value(self.criteria))
        if self.external_model_involvement is not None:
            object.__setattr__(
                self,
                "external_model_involvement",
                _freeze_json_value(self.external_model_involvement),
            )

        if not isinstance(self.source, str) or not self.source:
            raise ValueError("source must be a non-empty string")
        if not isinstance(self.evaluator_id, str) or not self.evaluator_id:
            raise ValueError("evaluator_id must be a non-empty string")
        if not isinstance(self.timestamp_logical, int) or isinstance(
            self.timestamp_logical, bool
        ):
            raise ValueError("timestamp_logical must be an integer")

        if not isinstance(self.prediction_commitment_refs, tuple):
            raise ValueError("prediction_commitment_refs must be a tuple")
        if any(
            not isinstance(ref, str) or not ref
            for ref in self.prediction_commitment_refs
        ):
            raise ValueError("prediction_commitment_refs must contain non-empty strings")
        if self.prediction_commitment_refs != tuple(sorted(self.prediction_commitment_refs)):
            raise ValueError("prediction_commitment_refs must be deterministically ordered")

        for name, refs in (
            ("prediction_error_refs", self.prediction_error_refs),
            ("attribution_assessment_refs", self.attribution_assessment_refs),
        ):
            if not isinstance(refs, tuple):
                raise ValueError(f"{name} must be a tuple")
            for ref in refs:
                if (
                    not isinstance(ref, tuple)
                    or len(ref) != 2
                    or not isinstance(ref[0], str)
                    or not ref[0]
                    or not isinstance(ref[1], int)
                    or isinstance(ref[1], bool)
                ):
                    raise ValueError(f"{name} must contain (non-empty hash, integer timestamp) pairs")
            if refs != tuple(sorted(refs)):
                raise ValueError(f"{name} must be deterministically ordered")


@dataclass(frozen=True)
class HypothesisSetTransition:
    """Immutable transition between competing-hypothesis states."""

    previous_state: "CompetingHypothesisSet"
    new_state: "CompetingHypothesisSet"
    provenance: Any

    def __post_init__(self) -> None:
        if self.provenance is None:
            raise ValueError("provenance is required for hypothesis-set transitions")
        if isinstance(self.provenance, (dict, list, tuple)):
            object.__setattr__(self, "provenance", _freeze_json_value(self.provenance))


@dataclass(frozen=True)
class CompetingHypothesisSet:
    """Immutable deterministic representation of competing hypotheses."""

    hypotheses: tuple[Hypothesis, ...]
    timestamp_logical: int

    def __post_init__(self) -> None:
        if not isinstance(self.hypotheses, tuple):
            raise ValueError("hypotheses must be a tuple")
        if len(self.hypotheses) < 2:
            raise ValueError("competing hypothesis set requires at least two hypotheses")
        if not all(isinstance(hypothesis, Hypothesis) for hypothesis in self.hypotheses):
            raise ValueError("hypotheses must contain only Hypothesis instances")
        ids = [hypothesis.hypothesis_id for hypothesis in self.hypotheses]
        if len(ids) != len(set(ids)):
            raise ValueError("hypothesis_id values must be unique within a set")
        object.__setattr__(
            self,
            "hypotheses",
            tuple(sorted(self.hypotheses, key=lambda h: h.hypothesis_id)),
        )
        if not isinstance(self.timestamp_logical, int) or isinstance(
            self.timestamp_logical, bool
        ):
            raise ValueError("timestamp_logical must be an integer")

    @property
    def canonical_object(self) -> dict[str, Any]:
        """Return exactly the canonical Block 5 representation."""
        return {
            "hypotheses": [
                {
                    "hypothesis_id": hypothesis.hypothesis_id,
                    "proposition": _thaw_json_value(hypothesis.proposition),
                }
                for hypothesis in self.hypotheses
            ],
            "timestamp_logical": self.timestamp_logical,
        }

    def add_hypothesis(
        self,
        hypothesis: Hypothesis,
        *,
        timestamp_logical: int,
        provenance: Any,
    ) -> HypothesisSetTransition:
        """Return a new set containing an additional hypothesis."""
        if not isinstance(hypothesis, Hypothesis):
            raise ValueError("hypothesis must be a Hypothesis instance")
        if hypothesis.hypothesis_id in {
            item.hypothesis_id for item in self.hypotheses
        }:
            raise ValueError("hypothesis_id already exists in set")
        new_state = CompetingHypothesisSet(
            hypotheses=tuple(sorted((*self.hypotheses, hypothesis), key=lambda h: h.hypothesis_id)),
            timestamp_logical=timestamp_logical,
        )
        self._validate_transition_timestamp(new_state, provenance)
        return HypothesisSetTransition(self, new_state, provenance)

    def remove_hypothesis(
        self,
        hypothesis_id: str,
        *,
        timestamp_logical: int,
        provenance: Any,
    ) -> HypothesisSetTransition:
        """Return a new set with one hypothesis removed."""
        if not isinstance(hypothesis_id, str) or not hypothesis_id:
            raise ValueError("hypothesis_id must be a non-empty string")
        remaining = tuple(
            hypothesis
            for hypothesis in self.hypotheses
            if hypothesis.hypothesis_id != hypothesis_id
        )
        if len(remaining) == len(self.hypotheses):
            raise ValueError("hypothesis_id not found in set")
        new_state = CompetingHypothesisSet(
            hypotheses=remaining,
            timestamp_logical=timestamp_logical,
        )
        self._validate_transition_timestamp(new_state, provenance)
        return HypothesisSetTransition(self, new_state, provenance)

    def replace_hypothesis(
        self,
        hypothesis_id: str,
        replacement: Hypothesis,
        *,
        timestamp_logical: int,
        provenance: Any,
    ) -> HypothesisSetTransition:
        """Return a new set replacing one hypothesis without mutating history."""
        if not isinstance(replacement, Hypothesis):
            raise ValueError("replacement must be a Hypothesis instance")
        if replacement.hypothesis_id == hypothesis_id:
            raise ValueError("replacement hypothesis_id must be distinct from existing identity")
        if hypothesis_id not in {item.hypothesis_id for item in self.hypotheses}:
            raise ValueError("hypothesis_id not found in set")
        new_state = CompetingHypothesisSet(
            hypotheses=tuple(
                sorted(
                    (
                        replacement if item.hypothesis_id == hypothesis_id else item
                        for item in self.hypotheses
                    ),
                    key=lambda h: h.hypothesis_id,
                )
            ),
            timestamp_logical=timestamp_logical,
        )
        self._validate_transition_timestamp(new_state, provenance)
        return HypothesisSetTransition(self, new_state, provenance)

    def _validate_transition_timestamp(
        self,
        new_state: "CompetingHypothesisSet",
        provenance: Any,
    ) -> None:
        if provenance is None:
            raise ValueError("provenance is required for hypothesis-set transitions")
        if new_state.timestamp_logical <= self.timestamp_logical:
            raise ValueError("timestamp_logical must strictly increase")
