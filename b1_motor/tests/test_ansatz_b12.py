import numpy as np
import pytest

from b1_motor.ansatz_b12 import (
    B12_LAYERS,
    B12_N_QUBITS,
    B12_PARAMETER_COUNT,
    SymmetricVQEAnsatz,
)


@pytest.mark.parametrize("n_qubits", [2, 4, 6])
def test_small_n_contract_is_explicitly_not_b12(n_qubits):
    with pytest.raises(ValueError):
        SymmetricVQEAnsatz(n_qubits=n_qubits)


def test_b12_has_64_qubits_3_layers_and_384_parameters():
    ansatz = SymmetricVQEAnsatz()
    assert ansatz.n_qubits == 64
    assert ansatz.layers == 3
    assert ansatz.parameter_count == 384
    assert ansatz.parameter_count == B12_PARAMETER_COUNT
    assert ansatz.gate_names() == ("RY", "RZ")


def test_parameter_indexing_is_deterministic_and_complete():
    ansatz = SymmetricVQEAnsatz()
    indices = []
    for layer in range(B12_LAYERS):
        for qubit in range(B12_N_QUBITS):
            indices.extend(
                [
                    ansatz.parameter_index(layer, qubit, "RY"),
                    ansatz.parameter_index(layer, qubit, "RZ"),
                ]
            )

    assert indices == list(range(B12_PARAMETER_COUNT))
    assert ansatz.parameter_index(0, 0, "RY") == 0
    assert ansatz.parameter_index(0, 0, "RZ") == 1
    assert ansatz.parameter_index(0, 63, "RY") == 126
    assert ansatz.parameter_index(1, 0, "RY") == 128
    assert ansatz.parameter_index(2, 63, "RZ") == 383


def test_initialization_is_deterministic_for_same_seed():
    ansatz = SymmetricVQEAnsatz()
    first = ansatz.initial_parameters(777314159)
    second = ansatz.initial_parameters(777314159)
    assert first.shape == (384,)
    assert first.dtype == np.float64
    assert np.array_equal(first, second)


def test_different_seeds_produce_distinct_parameter_vectors():
    ansatz = SymmetricVQEAnsatz()
    first = ansatz.initial_parameters(1)
    second = ansatz.initial_parameters(2)
    assert not np.array_equal(first, second)


def test_rotation_matrices_are_ry_rz_only():
    ansatz = SymmetricVQEAnsatz()
    for gate in ("RY", "RZ"):
        matrix = ansatz.rotation_matrix(gate, 0.37)
        assert matrix.shape == (2, 2)
        assert matrix.dtype == np.complex128
        assert np.allclose(matrix.conj().T @ matrix, np.eye(2), atol=1e-12)
