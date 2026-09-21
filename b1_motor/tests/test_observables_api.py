import numpy as np
import pytest

from b1_motor.mps import MPS, ry
from b1_motor.observables import PauliSum, PauliTerm, expectation


def test_pauli_term_contract():
    term = PauliTerm(sites=(0, 2), operators=("Z", "X"), coefficient=0.5)
    assert term.sites == (0, 2)
    assert term.operators == ("Z", "X")
    assert term.coefficient == 0.5 + 0j


@pytest.mark.parametrize(
    "sites,operators",
    [
        ((0,), ("A",)),
        ((1, 0), ("Z", "Z")),
        ((0, 0), ("Z", "Z")),
        ((0,), ("Z", "X")),
    ],
)
def test_pauli_term_rejects_invalid_contract(sites, operators):
    with pytest.raises((TypeError, ValueError)):
        PauliTerm(sites=sites, operators=operators)


def test_pauli_sum_and_single_term_expectation():
    state = MPS(2, bond_dim=2)
    value = expectation(state, PauliTerm(sites=(0,), operators=("Z",)))
    assert np.allclose(value, 1.0)

    hamiltonian = PauliSum(
        terms=(
            PauliTerm(sites=(0,), operators=("Z",), coefficient=2.0),
            PauliTerm(sites=(1,), operators=("X",), coefficient=3.0),
        )
    )
    assert np.allclose(expectation(state, hamiltonian), 2.0)


def test_noncontiguous_pauli_string_on_mps():
    state = MPS(4, bond_dim=2)
    state.apply_local_rotation(1, ry(np.pi / 2.0))
    value = expectation(
        state,
        PauliTerm(sites=(0, 2), operators=("Z", "Z")),
    )
    assert np.allclose(value, 1.0)


def test_observable_does_not_mutate_mps():
    state = MPS(4, bond_dim=2)
    before = [tensor.copy() for tensor in state.tensors]
    expectation(state, PauliTerm(sites=(1,), operators=("X",)))
    for actual, expected in zip(state.tensors, before):
        assert np.array_equal(actual, expected)


def test_observable_rejects_out_of_range_site():
    state = MPS(2)
    with pytest.raises(ValueError):
        expectation(state, PauliTerm(sites=(2,), operators=("Z",)))


def test_pauli_sum_is_empty_identity():
    state = MPS(2)
    assert np.allclose(expectation(state, PauliSum(())), 0.0)
