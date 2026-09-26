"""Immutable Decision / Action Proposal primitives for Cognitive Core Block 6."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import isfinite
from types import MappingProxyType
from typing import Any


def _freeze_json_value(value: Any) -> Any:
    """Recursively freeze JSON-like values."""
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
            raise ValueError("value must contain only finite JSON numbers")
        return value
    if isinstance(value, (str, int, bool)) or value is None:
        return value
    raise ValueError(f"value must be JSON-like, got {type(value).__name__}")


def _thaw_json_value(value: Any) -> Any:
    """Return a JSON-serializable copy of a frozen JSON-like value."""
    if isinstance(value, MappingProxyType):
        return {key: _thaw_json_value(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json_value(item) for item in value]
    return value


class DecisionStatus(Enum):
    """Epistemic status of a Decision Assessment."""

    PROPOSED = "PROPOSED"
    UNRESOLVED = "UNRESOLVED"
    NOT_YET_DECIDABLE = "NOT_YET_DECIDABLE"


@dataclass(frozen=True)
class DecisionAssessment:
    """Immutable assessment state; never an authorization."""

    decision_id: str
    decision_status: DecisionStatus
    rationale: Any
    timestamp_logical: int

    def __post_init__(self) -> None:
        if not isinstance(self.decision_id, str) or not self.decision_id:
            raise ValueError("decision_id must be a non-empty string")
        if not isinstance(self.decision_status, DecisionStatus):
            raise ValueError("decision_status must be a DecisionStatus")
        if not isinstance(self.timestamp_logical, int) or isinstance(
            self.timestamp_logical, bool
        ):
            raise ValueError("timestamp_logical must be an integer")
        object.__setattr__(
            self,
            "rationale",
            _freeze_json_value(self.rationale),
        )

    @property
    def canonical_object(self) -> dict[str, Any]:
        """Return exactly the canonical Decision Assessment representation."""
        return {
            "decision_id": self.decision_id,
            "decision_status": self.decision_status.value,
            "rationale": _thaw_json_value(self.rationale),
            "timestamp_logical": self.timestamp_logical,
        }

    @property
    def is_determined(self) -> bool:
        """Whether this assessment may support a determined action proposal."""
        return self.decision_status is DecisionStatus.PROPOSED


@dataclass(frozen=True)
class DecisionActionProvenance:
    """Provenance kept separate from canonical decision/action state."""

    decision_id: str
    decision_context: Any
    evidence: Any
    criteria: Any
    source: str
    timestamp_logical: int
    evaluator_id: str | None = None
    referenced_cognitive_objects: Any = None
    external_model_involvement: Any = None
    proposal_source: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.decision_id, str) or not self.decision_id:
            raise ValueError("decision_id must be a non-empty string")
        if not isinstance(self.source, str) or not self.source:
            raise ValueError("source must be a non-empty string")
        if not isinstance(self.timestamp_logical, int) or isinstance(
            self.timestamp_logical, bool
        ):
            raise ValueError("timestamp_logical must be an integer")
        if self.evaluator_id is not None and (
            not isinstance(self.evaluator_id, str) or not self.evaluator_id
        ):
            raise ValueError("evaluator_id must be a non-empty string when provided")
        if self.proposal_source is not None and (
            not isinstance(self.proposal_source, str) or not self.proposal_source
        ):
            raise ValueError(
                "proposal_source must be a non-empty string when provided"
            )

        object.__setattr__(
            self,
            "decision_context",
            _freeze_json_value(self.decision_context),
        )
        object.__setattr__(self, "evidence", _freeze_json_value(self.evidence))
        object.__setattr__(self, "criteria", _freeze_json_value(self.criteria))

        if self.referenced_cognitive_objects is not None:
            object.__setattr__(
                self,
                "referenced_cognitive_objects",
                _freeze_json_value(self.referenced_cognitive_objects),
            )

        if self.external_model_involvement is not None:
            object.__setattr__(
                self,
                "external_model_involvement",
                _freeze_json_value(self.external_model_involvement),
            )


@dataclass(frozen=True)
class ActionProposal:
    """Immutable proposed action; never authorization or execution."""

    action_id: str
    action_type: str
    parameters: Any
    preconditions: Any
    expected_effects: Any
    timestamp_logical: int

    def __post_init__(self) -> None:
        if not isinstance(self.action_id, str) or not self.action_id:
            raise ValueError("action_id must be a non-empty string")
        if not isinstance(self.action_type, str) or not self.action_type:
            raise ValueError("action_type must be a non-empty string")
        if not isinstance(self.timestamp_logical, int) or isinstance(
            self.timestamp_logical, bool
        ):
            raise ValueError("timestamp_logical must be an integer")

        object.__setattr__(
            self,
            "parameters",
            _freeze_json_value(self.parameters),
        )
        object.__setattr__(
            self,
            "preconditions",
            _freeze_json_value(self.preconditions),
        )
        object.__setattr__(
            self,
            "expected_effects",
            _freeze_json_value(self.expected_effects),
        )

    @property
    def canonical_object(self) -> dict[str, Any]:
        """Return exactly the canonical Action Proposal representation."""
        return {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "parameters": _thaw_json_value(self.parameters),
            "preconditions": _thaw_json_value(self.preconditions),
            "expected_effects": _thaw_json_value(self.expected_effects),
            "timestamp_logical": self.timestamp_logical,
        }


@dataclass(frozen=True)
class ActionProposalCollection:
    """Immutable deterministic collection of Action Proposals."""

    proposals: tuple[ActionProposal, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.proposals, tuple):
            raise ValueError("proposals must be a tuple")
        if not all(isinstance(item, ActionProposal) for item in self.proposals):
            raise ValueError("proposals must contain only ActionProposal instances")

        action_ids = [item.action_id for item in self.proposals]
        if len(action_ids) != len(set(action_ids)):
            raise ValueError("action_id values must be unique within a collection")

        object.__setattr__(
            self,
            "proposals",
            tuple(sorted(self.proposals, key=lambda item: item.action_id)),
        )

    @property
    def canonical_object(self) -> list[dict[str, Any]]:
        """Return proposals in deterministic action_id order."""
        return [proposal.canonical_object for proposal in self.proposals]


def validate_action_against_decision(
    *,
    action: ActionProposal,
    decision: DecisionAssessment,
    provenance: DecisionActionProvenance,
) -> None:
    """Validate the explicit decision/action association without authorizing."""
    if not isinstance(action, ActionProposal):
        raise ValueError("action must be an ActionProposal")
    if not isinstance(decision, DecisionAssessment):
        raise ValueError("decision must be a DecisionAssessment")
    if not isinstance(provenance, DecisionActionProvenance):
        raise ValueError(
            "provenance must be a DecisionActionProvenance"
        )

    if provenance.decision_id != decision.decision_id:
        raise ValueError(
            "provenance decision_id must match the associated Decision Assessment"
        )

    if action.timestamp_logical < decision.timestamp_logical:
        raise ValueError(
            "action timestamp_logical must not precede decision timestamp_logical"
        )

    if not decision.is_determined:
        raise ValueError(
            "UNRESOLVED or NOT_YET_DECIDABLE decisions cannot represent a determined action"
        )
