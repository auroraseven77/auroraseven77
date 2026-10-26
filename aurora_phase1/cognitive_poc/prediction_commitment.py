"""Immutable prediction commitment primitive."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

from aurora_phase1.core.crypto import hash_object


def _freeze_json_value(value: Any) -> Any:
    """Recursively freeze JSON-compatible mutable containers."""
    if isinstance(value, MappingProxyType):
        return value
    if isinstance(value, dict):
        return MappingProxyType(
            {key: _freeze_json_value(item) for key, item in value.items()}
        )
    if isinstance(value, list):
        return tuple(_freeze_json_value(item) for item in value)
    if isinstance(value, tuple):
        return tuple(_freeze_json_value(item) for item in value)
    return value


def _thaw_json_value(value: Any) -> Any:
    """Recursively return a JSON-compatible copy of a frozen value."""
    if isinstance(value, MappingProxyType):
        return {
            key: _thaw_json_value(item)
            for key, item in value.items()
        }
    if isinstance(value, tuple):
        return [_thaw_json_value(item) for item in value]
    return value


@dataclass(frozen=True)
class PredictionCommitment:
    """Immutable cryptographic commitment to a prediction."""

    hypothesis_id: str
    prediction: Any
    conditions: Any
    timestamp_logical: int

    def __post_init__(self) -> None:
        if not isinstance(self.hypothesis_id, str):
            raise ValueError("hypothesis_id must be a string")
        if not self.hypothesis_id:
            raise ValueError("hypothesis_id must be a non-empty string")
        if not isinstance(self.timestamp_logical, int) or isinstance(
            self.timestamp_logical, bool
        ):
            raise ValueError("timestamp_logical must be an integer")

        object.__setattr__(
            self,
            "prediction",
            _freeze_json_value(self.prediction),
        )
        object.__setattr__(
            self,
            "conditions",
            _freeze_json_value(self.conditions),
        )

    @property
    def canonical_object(self) -> dict[str, Any]:
        """Return exactly the fields covered by the commitment hash."""
        return {
            "hypothesis_id": self.hypothesis_id,
            "prediction": _thaw_json_value(self.prediction),
            "conditions": _thaw_json_value(self.conditions),
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

    if not isinstance(commitment_object["hypothesis_id"], str):
        return "COMMITMENT_MALFORMED"

    if not isinstance(commitment_object["timestamp_logical"], int) or isinstance(
        commitment_object["timestamp_logical"], bool
    ):
        return "COMMITMENT_MALFORMED"

    actual_hash = hash_object(commitment_object)

    if actual_hash != expected_hash:
        return "COMMITMENT_HASH_MISMATCH"

    return "COMMITMENT_VALID"
