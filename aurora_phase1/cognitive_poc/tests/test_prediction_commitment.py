"""Executable specification for Prediction Commitment."""

import pytest


def test_prediction_commitment_module_exists():
    """The implementation module must exist before Block 1A can pass."""
    from aurora_phase1.cognitive_poc.prediction_commitment import PredictionCommitment
    assert PredictionCommitment is not None


def test_canonical_commitment_has_exact_four_fields():
    from aurora_phase1.cognitive_poc.prediction_commitment import PredictionCommitment

    commitment = PredictionCommitment(
        hypothesis_id="H-001",
        prediction={"temperature": 42},
        conditions={"cpu_load": 0.8},
        timestamp_logical=10,
    )

    assert set(commitment.canonical_object) == {
        "hypothesis_id",
        "prediction",
        "conditions",
        "timestamp_logical",
    }


def test_prediction_hash_is_64_hex_characters():
    from aurora_phase1.cognitive_poc.prediction_commitment import PredictionCommitment

    commitment = PredictionCommitment(
        hypothesis_id="H-001",
        prediction={"temperature": 42},
        conditions={"cpu_load": 0.8},
        timestamp_logical=10,
    )

    assert len(commitment.prediction_hash) == 64
    assert all(c in "0123456789abcdef" for c in commitment.prediction_hash)


def test_prediction_hash_uses_existing_hash_object():
    from aurora_phase1.cognitive_poc.prediction_commitment import PredictionCommitment
    from aurora_phase1.core.crypto import hash_object

    commitment = PredictionCommitment(
        hypothesis_id="H-001",
        prediction={"temperature": 42},
        conditions={"cpu_load": 0.8},
        timestamp_logical=10,
    )

    assert commitment.prediction_hash == hash_object(commitment.canonical_object)


def test_mutating_any_committed_field_changes_hash():
    from aurora_phase1.cognitive_poc.prediction_commitment import PredictionCommitment

    base = dict(
        hypothesis_id="H-001",
        prediction={"temperature": 42},
        conditions={"cpu_load": 0.8},
        timestamp_logical=10,
    )
    original = PredictionCommitment(**base).prediction_hash

    mutations = [
        {**base, "hypothesis_id": "H-002"},
        {**base, "prediction": {"temperature": 43}},
        {**base, "conditions": {"cpu_load": 0.9}},
        {**base, "timestamp_logical": 11},
    ]

    for mutated in mutations:
        assert PredictionCommitment(**mutated).prediction_hash != original


def test_invalid_numeric_values_are_rejected_by_hash_api():
    from aurora_phase1.cognitive_poc.prediction_commitment import PredictionCommitment

    with pytest.raises((TypeError, ValueError)):
        PredictionCommitment(
            hypothesis_id="H-001",
            prediction={"temperature": float("nan")},
            conditions={},
            timestamp_logical=10,
        ).prediction_hash


def test_prediction_commitment_does_not_expose_ledger_entry_hash():
    from aurora_phase1.cognitive_poc.prediction_commitment import PredictionCommitment

    commitment = PredictionCommitment(
        hypothesis_id="H-001",
        prediction={"temperature": 42},
        conditions={},
        timestamp_logical=10,
    )

    assert not hasattr(commitment, "ledger_entry_hash")


def test_original_commitment_is_not_mutated():
    from aurora_phase1.cognitive_poc.prediction_commitment import PredictionCommitment

    commitment = PredictionCommitment(
        hypothesis_id="H-001",
        prediction={"temperature": 42},
        conditions={},
        timestamp_logical=10,
    )
    original_hash = commitment.prediction_hash

    assert commitment.prediction_hash == original_hash
    assert commitment.canonical_object["prediction"] == {"temperature": 42}
    assert commitment.canonical_object["timestamp_logical"] == 10
