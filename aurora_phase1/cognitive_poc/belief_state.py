"""Immutable belief-state primitives for Cognitive Core Block 2."""

from dataclasses import dataclass
from enum import Enum
import math
from typing import Any


class BeliefStatus(Enum):
    """Epistemic status for unresolved belief state."""
    BELIEF_UNRESOLVED = "BELIEF_UNRESOLVED"



@dataclass(frozen=True)
class UnresolvedBelief:
    """Explicit absence of a numerically resolved belief."""
    hypothesis_id: str
    timestamp_logical: int
    status: BeliefStatus = BeliefStatus.BELIEF_UNRESOLVED


@dataclass(frozen=True)
class BeliefTransition:
    previous_state: "BeliefState"
    new_state: "BeliefState"
    provenance: Any


@dataclass(frozen=True)
class BeliefState:
    """Immutable numerically resolved belief state."""
    hypothesis_id: str
    belief: float
    timestamp_logical: int

    def __post_init__(self) -> None:
        if not isinstance(self.hypothesis_id, str) or not self.hypothesis_id:
            raise ValueError("hypothesis_id must be a non-empty string")
        if not isinstance(self.timestamp_logical, int) or isinstance(self.timestamp_logical, bool):
            raise ValueError("timestamp_logical must be an integer")
        if not isinstance(self.belief, (int, float)) or isinstance(self.belief, bool):
            raise ValueError("belief must be numeric")
        if not math.isfinite(float(self.belief)):
            raise ValueError("belief must be finite")
        if not 0.0 <= float(self.belief) <= 1.0:
            raise ValueError("belief must be within [0.0, 1.0]")

    @property
    def canonical_object(self) -> dict[str, Any]:
        """Return exactly the canonical fields covered by the state."""
        return {
            "hypothesis_id": self.hypothesis_id,
            "belief": self.belief,
            "timestamp_logical": self.timestamp_logical,
        }

    def update(self, *, belief: float, timestamp_logical: int, provenance: Any) -> "BeliefTransition":
        """Create a new belief state without mutating the predecessor."""
        if provenance is None:
            raise ValueError("provenance is required for belief updates")
        if timestamp_logical <= self.timestamp_logical:
            raise ValueError("timestamp_logical must strictly increase")
        new_state = BeliefState(
            hypothesis_id=self.hypothesis_id,
            belief=belief,
            timestamp_logical=timestamp_logical,
        )
        return BeliefTransition(
            previous_state=self,
            new_state=new_state,
            provenance=provenance,
        )
