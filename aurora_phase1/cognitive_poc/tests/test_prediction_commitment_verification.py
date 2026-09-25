"""Verification specification for Prediction Commitment."""

from aurora_phase1.cognitive_poc.prediction_commitment import PredictionCommitment


def _commitment():
    return PredictionCommitment(
        hypothesis_id="H-001",
        prediction={"temperature": 42},
        conditions={"cpu_load": 0.8},
        timestamp_logical=10,
    )


def test_valid_commitment_verifies():
    from aurora_phase1.cognitive_poc.prediction_commitment import verify_commitment

    commitment = _commitment()
    result = verify_commitment(
        commitment.canonical_object,
        commitment.prediction_hash,
    )
    assert result == "COMMITMENT_VALID"


def test_modified_prediction_is_detected():
    from aurora_phase1.cognitive_poc.prediction_commitment import verify_commitment

    commitment = _commitment()
    modified = dict(commitment.canonical_object)
    modified["prediction"] = {"temperature": 43}

    result = verify_commitment(modified, commitment.prediction_hash)
    assert result == "COMMITMENT_HASH_MISMATCH"


def test_modified_conditions_are_detected():
    from aurora_phase1.cognitive_poc.prediction_commitment import verify_commitment

    commitment = _commitment()
    modified = dict(commitment.canonical_object)
    modified["conditions"] = {"cpu_load": 0.9}

    result = verify_commitment(modified, commitment.prediction_hash)
    assert result == "COMMITMENT_HASH_MISMATCH"


def test_missing_field_is_malformed():
    from aurora_phase1.cognitive_poc.prediction_commitment import verify_commitment

    commitment = _commitment()
    malformed = dict(commitment.canonical_object)
    del malformed["prediction"]

    result = verify_commitment(malformed, commitment.prediction_hash)
    assert result == "COMMITMENT_MALFORMED"


def test_extra_field_is_malformed():
    from aurora_phase1.cognitive_poc.prediction_commitment import verify_commitment

    commitment = _commitment()
    malformed = dict(commitment.canonical_object)
    malformed["extra"] = "forbidden"

    result = verify_commitment(malformed, commitment.prediction_hash)
    assert result == "COMMITMENT_MALFORMED"


def test_wrong_hash_is_detected():
    from aurora_phase1.cognitive_poc.prediction_commitment import verify_commitment

    commitment = _commitment()
    wrong_hash = "0" * 64

    result = verify_commitment(commitment.canonical_object, wrong_hash)
    assert result == "COMMITMENT_HASH_MISMATCH"
