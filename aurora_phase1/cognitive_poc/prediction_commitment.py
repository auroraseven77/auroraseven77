"""Immutable prediction commitment primitive."""

from dataclasses import dataclass
from typing import Any

from aurora_phase1.core.crypto import hash_object


@dataclass(frozen=True)
class PredictionCommitment:
    """Immutable cryptographic commitment to a prediction."""

    hypothesis_id: str
    prediction: Any
    conditions: Any
    timestamp_logical: int

    @property
    def canonical_object(self) -> dict[str, Any]:
        """Return exactly the fields covered by the commitment hash."""
        return {
            "hypothesis_id": self.hypothesis_id,
            "prediction": self.prediction,
            "conditions": self.conditions,
            "timestamp_logical": self.timestamp_logical,
        }

    @property
    def prediction_hash(self) -> str:
        """Return the SHA-256 hash of the canonical commitment object."""
        return hash_object(self.canonical_object)


_COMMITMENT_FIELDS = frozenset({
    "hypothesis_id",
    "prediction",
    "conditions",
    "timestamp_logical",
})


def verify_commitment(
    commitment_object: dict[str, Any],
    expected_hash: str,
) -> str:
    """Verify a prediction commitment without mutating the input."""
    if not isinstance(commitment_object, dict):
        return "COMMITMENT_MALFORMED"

    if set(commitment_object) != _COMMITMENT_FIELDS:
        return "COMMITMENT_MALFORMED"

    if not isinstance(expected_hash, str) or len(expected_hash) != 64:
        return "COMMITMENT_MALFORMED"

    actual_hash = hash_object(commitment_object)

    if actual_hash != expected_hash:
        return "COMMITMENT_HASH_MISMATCH"

    return "COMMITMENT_VALID"
