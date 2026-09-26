"""Prediction Commitment integration specification for the existing Ledger."""

from aurora_phase1.cognitive_poc.prediction_commitment import PredictionCommitment
from aurora_phase1.core.ledger import Ledger


def test_prediction_commitment_can_be_recorded_in_existing_ledger(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    commitment = PredictionCommitment(
        hypothesis_id="H-001",
        prediction={"temperature": 42},
        conditions={"cpu_load": 0.8},
        timestamp_logical=10,
    )

    block = ledger.add_block(
        "PREDICTION_COMMITTED",
        {
            "prediction_hash": commitment.prediction_hash,
            "commitment": commitment.canonical_object,
        },
        tick=10,
    )

    assert block.event_type == "PREDICTION_COMMITTED"
    assert block.payload["prediction_hash"] == commitment.prediction_hash
    assert block.payload["commitment"] == commitment.canonical_object


def test_prediction_hash_and_ledger_entry_hash_are_distinct(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    commitment = PredictionCommitment(
        hypothesis_id="H-001",
        prediction={"temperature": 42},
        conditions={},
        timestamp_logical=10,
    )

    block = ledger.add_block(
        "PREDICTION_COMMITTED",
        {
            "prediction_hash": commitment.prediction_hash,
            "commitment": commitment.canonical_object,
        },
        tick=10,
    )

    assert commitment.prediction_hash != block.entry_hash


def test_prediction_hash_excludes_ledger_metadata(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    commitment = PredictionCommitment(
        hypothesis_id="H-001",
        prediction={"temperature": 42},
        conditions={},
        timestamp_logical=10,
    )

    original_hash = commitment.prediction_hash

    block = ledger.add_block(
        "PREDICTION_COMMITTED",
        {
            "prediction_hash": original_hash,
            "commitment": commitment.canonical_object,
            "metadata": {"operator": "test"},
        },
        tick=99,
    )


    assert commitment.prediction_hash == original_hash
    assert block.tick == 99
    assert block.entry_hash != original_hash


def test_prediction_commitment_event_preserves_chain_integrity(tmp_path):
    ledger = Ledger(tmp_path / "ledger.jsonl")
    commitment = PredictionCommitment(
        hypothesis_id="H-001",
        prediction={"temperature": 42},
        conditions={},
        timestamp_logical=10,
    )

    ledger.add_block(
        "PREDICTION_COMMITTED",
        {
            "prediction_hash": commitment.prediction_hash,
            "commitment": commitment.canonical_object,
        },
        tick=10,
    )


    result = ledger.audit_chain()
    assert result.chain_integrity is True
    assert result.total_blocks == 1
    assert result.failed_seq is None
