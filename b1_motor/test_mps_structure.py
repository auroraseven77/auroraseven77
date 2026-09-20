import numpy as np
import pytest

from b1_motor.mps import MPS


def test_64_qubit_mps_contract():
    state = MPS(n_qubits=64, bond_dim=128)

    state.validate_structure()

    assert state.n_qubits == 64
    assert state.physical_dim == 2
    assert len(state.tensors) == 64
    assert state.max_bond_dimension <= 128


def test_tensor_ranks_are_local():
    state = MPS(n_qubits=64, bond_dim=128)

    assert all(rank <= 3 for rank in state.tensor_ranks)


def test_no_dense_statevector_shape():
    state = MPS(n_qubits=64, bond_dim=128)

    for tensor in state.tensors:
        assert 2**64 not in tensor.shape


def test_initial_state_is_zero_product_state():
    state = MPS(n_qubits=64, bond_dim=128)

    for tensor in state.tensors:
        assert np.count_nonzero(tensor) == 1
        assert tensor[(0, 0, 0)] == 1.0


def test_structural_storage_is_linear_for_product_state():
    state = MPS(n_qubits=64, bond_dim=128)

    assert state.structural_parameter_count == 64 * 2


def test_invalid_qubit_count_is_rejected():
    with pytest.raises(ValueError):
        MPS(n_qubits=0, bond_dim=128)


def test_invalid_bond_dimension_is_rejected():
    with pytest.raises(ValueError):
        MPS(n_qubits=64, bond_dim=0)
