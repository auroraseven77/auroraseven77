import pytest
from b1_motor.envelope import EvidenceEnvelope

def test_envelope_strict_authority_and_source():
    env = EvidenceEnvelope(
        schema_version="1.0",
        source_agent="ARGOS",
        target_agent="HEPHAESTUS",
        experiment_id="B1.2-64Q-VQE",
        execution_id="exec_001"
    )
    assert env.authority == "none"
    assert env.evidence_source == "computational_simulation_only"

    with pytest.raises(ValueError):
        EvidenceEnvelope(
            schema_version="1.0",
            source_agent="ARGOS",
            target_agent="HEPHAESTUS",
            experiment_id="B1.2-64Q-VQE",
            execution_id="exec_001",
            authority="granted"
        )

    with pytest.raises(ValueError):
        EvidenceEnvelope(
            schema_version="1.0",
            source_agent="ARGOS",
            target_agent="HEPHAESTUS",
            experiment_id="B1.2-64Q-VQE",
            execution_id="exec_001",
            evidence_source="quantum_hardware_backend"
        )
