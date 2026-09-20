"""
TUU / B1.2 / P2.3 — Deterministic Partitioning Validators.
Enforces exact coverage of [0, 63], mutual exclusivity, and manifest alignment.
"""

from __future__ import annotations

from b1_motor.types import PARTITIONS, LOGICAL_QUBITS_MAX, AgentId


def validate_global_partitions() -> None:
    """
    Valida que o conjunto de partições dos agentes cobre exatamente o intervalo
    contíguo [0, LOGICAL_QUBITS_MAX - 1], sem sobreposições ou lacunas.
    """
    all_qubits = set()
    expected_total = LOGICAL_QUBITS_MAX  # 64 qubits (0 a 63)

    for agent_id, (start, end) in PARTITIONS.items():
        if start < 0 or end >= expected_total:
            raise ValueError(
                f"Range ({start}, {end}) for {agent_id} is out of bounds [0, {expected_total - 1}]"
            )
        if start > end:
            raise ValueError(
                f"Invalid range ({start}, {end}) for {agent_id}: start > end"
            )

        qubit_set = set(range(start, end + 1))
        if not qubit_set.isdisjoint(all_qubits):
            raise ValueError(f"Security/Structural Violation: Overlap detected in partitions at agent {agent_id}")
        
        all_qubits.update(qubit_set)

    if len(all_qubits) != expected_total:
        raise ValueError(
            f"Partition coverage mismatch: got {len(all_qubits)} qubits, expected {expected_total}"
        )

    expected_span = set(range(expected_total))
    if all_qubits != expected_span:
        raise ValueError("Partition coverage does not match exact contiguous range [0, 63]")


def get_agent_for_qubit(qubit_index: int) -> AgentId:
    """
    Retorna o AgentId responsável por um determinado índice de qubit de forma determinística.
    """
    if not 0 <= qubit_index < LOGICAL_QUBITS_MAX:
        raise ValueError(f"Qubit index {qubit_index} out of bounds [0, {LOGICAL_QUBITS_MAX - 1}]")
    
    for agent_id, (start, end) in PARTITIONS.items():
        if start <= qubit_index <= end:
            return agent_id
            
    raise ValueError(f"Qubit index {qubit_index} not covered by any partition")
