import pytest
from b1_motor.types import AgentPartition, TruncationReport, PARTITIONS, CHI_MAX

def test_agent_partitions_bounds():
    assert PARTITIONS["ARGOS"] == (0, 21)
    assert PARTITIONS["HEPHAESTUS"] == (22, 43)
    assert PARTITIONS["HERMES"] == (44, 63)
    
    p_argos = AgentPartition(agent_id="ARGOS", qubit_range=(0, 21))
    assert p_argos.agent_id == "ARGOS"

    with pytest.raises(ValueError):
        AgentPartition(agent_id="ARGOS", qubit_range=(0, 22))

def test_truncation_report_invariants():
    report = TruncationReport(
        step=1,
        bond_dimension_before=140,
        bond_dimension_after=128,
        discarded_weight_loss=1e-5
    )
    assert report.bond_dimension_after == CHI_MAX

    with pytest.raises(ValueError):
        TruncationReport(
            step=2,
            bond_dimension_before=150,
            bond_dimension_after=129,
            discarded_weight_loss=1e-5
        )

    with pytest.raises(ValueError):
        TruncationReport(
            step=3,
            bond_dimension_before=100,
            bond_dimension_after=100,
            discarded_weight_loss=-0.01
        )
