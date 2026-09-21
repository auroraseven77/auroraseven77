import numpy as np
import pytest

from b1_motor.ansatz_b12 import (
    B12_LAYERS,
    B12_N_QUBITS,
    B12_PARAMETER_COUNT,
    SymmetricVQEAnsatz,
)


@pytest.mark.parametrize(
    ("n_qubits", "expected_parameters"),
    [(2, 12), (4, 24), (6, 36)],
)
def test_small_n_contract_before_64q_execution(n_qubits, expected_parameters):
    ansatz = SymmetricVQEAnsatz(n_qubits=n_qubits)
    assert ansatz.layers == 3
    assert ansatz.parameter_count == expected_parameters
    assert not ansatz.is_b12


def test_b12_has_64_qubits_3_layers_and_384_parameters():
    ansatz = SymmetricVQEAnsatz()
    assert ansatz.n_qubits == 64
    assert ansatz.layers == 3
    assert ansatz.parameter_count == 384
    assert ansatz.parameter_count == B12_PARAMETER_COUNT
    assert ansatz.gate_names() == ("RY", "RZ")
    assert ansatz.is_b12


@pytest.mark.parametrize("n_qubits", [2, 4, 6])
def test_parameter_indexing_is_complete_for_small_n(n_qubits):
    ansatz = SymmetricVQEAnsatz(n_qubits=n_qubits)
    indices = []
    for layer in range(B12_LAYERS):
        for qubit in range(n_qubits):
            indices.extend(
                [
                    ansatz.parameter_index(layer, qubit, "RY"),
                    ansatz.parameter_index(layer, qubit, "RZ"),
                ]
            )
    assert indices == list(range(ansatz.parameter_count))


def test_b12_parameter_indexing_boundaries():
    ansatz = SymmetricVQEAnsatz()
    assert ansatz.parameter_index(0, 0, "RY") == 0
    assert ansatz.parameter_index(0, 0, "RZ") == 1
    assert ansatz.parameter_index(0, 63, "RY") == 126
    assert ansatz.parameter_index(1, 0, "RY") == 128
    assert ansatz.parameter_index(2, 63, "RZ") == 383


@pytest.mark.parametrize("n_qubits", [2, 4, 6, 64])
def test_initialization_is_deterministic_for_same_seed(n_qubits):
    ansatz = SymmetricVQEAnsatz(n_qubits=n_qubits)
    first = ansatz.initial_parameters(777314159)
    second = ansatz.initial_parameters(777314159)
    assert first.shape == (ansatz.parameter_count,)
    assert first.dtype == np.float64
    assert np.array_equal(first, second)


def test_different_seeds_produce_distinct_parameter_vectors():
    ansatz = SymmetricVQEAnsatz(n_qubits=6)
    first = ansatz.initial_parameters(1)
    second = ansatz.initial_parameters(2)
    assert not np.array_equal(first, second)


def test_rotation_matrices_are_ry_rz_only():
    ansatz = SymmetricVQEAnsatz(n_qubits=2)
    for gate in ("RY", "RZ"):
        matrix = ansatz.rotation_matrix(gate, 0.37)
        assert matrix.shape == (2, 2)
        assert matrix.dtype == np.complex128
        assert np.allclose(matrix.conj().T @ matrix, np.eye(2), atol=1e-12)


def test_apply_is_available_after_topology_closure():
    ansatz = SymmetricVQEAnsatz(n_qubits=2)
    params = np.zeros(ansatz.parameter_count)
    state = ansatz.apply(params, bond_dim=2)
    assert state.n_qubits == 2
    assert state.max_bond_dimension <= 2
