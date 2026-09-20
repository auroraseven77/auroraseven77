import pytest
from b1_motor.types import PARTITIONS, AgentPartition
from b1_motor.partitions import validate_global_partitions, get_agent_for_qubit


def test_global_partition_coverage_and_exclusivity():
    # Valida cobertura exata e ausência de sobreposição
    validate_global_partitions()

    assert PARTITIONS["ARGOS"] == (0, 21)       # 22 qubits
    assert PARTITIONS["HEPHAESTUS"] == (22, 43) # 22 qubits
    assert PARTITIONS["HERMES"] == (44, 63)     # 20 qubits
    # Soma exata: 22 + 22 + 20 = 64 qubits


def test_agent_qubit_lookup():
    assert get_agent_for_qubit(0) == "ARGOS"
    assert get_agent_for_qubit(21) == "ARGOS"
    assert get_agent_for_qubit(22) == "HEPHAESTUS"
    assert get_agent_for_qubit(43) == "HEPHAESTUS"
    assert get_agent_for_qubit(44) == "HERMES"
    assert get_agent_for_qubit(63) == "HERMES"

    with pytest.raises(ValueError):
        get_agent_for_qubit(-1)

    with pytest.raises(ValueError):
        get_agent_for_qubit(64)


def test_agent_partition_immutable_and_strict():
    p = AgentPartition(agent_id="ARGOS", qubit_range=(0, 21))
    
    # Imutabilidade via frozen=True
    with pytest.raises(AttributeError):
        p.agent_id = "HERMES"

    # Rejeição de range divergente do manifesto
    with pytest.raises(ValueError):
        AgentPartition(agent_id="ARGOS", qubit_range=(0, 20))
