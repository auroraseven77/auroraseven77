import numpy as np
import pytest

from b1_motor.ansatz_b12 import SymmetricVQEAnsatz
from b1_motor.hamiltonian_b12 import TFIMSignConvention
from b1_motor.mps import MPS
from b1_motor.observables import PauliTerm, expectation
from b1_motor.vqe_b12 import (
    build_energy_hamiltonian,
    evaluate_energy,
    energy_from_state,
)


def test_small_n_ansatz_application_is_mps_only():
    ansatz = SymmetricVQEAnsatz(n_qubits=2)
    params = np.zeros(ansatz.parameter_count)
    state, report = ansatz.apply_with_report(params, bond_dim=2)

    assert isinstance(state, MPS)
    assert state.n_qubits == 2
    assert state.max_bond_dimension <= 2
    assert report.cx_count == 3
    assert report.truncations == 0
    assert np.allclose(
        expectation(state, PauliTerm(sites=(0,), operators=("Z",))),
        1.0,
    )


def test_small_n_ansatz_nonzero_parameters_are_deterministic():
    ansatz = SymmetricVQEAnsatz(n_qubits=4)
    params = ansatz.initial_parameters(777314159)

    first, first_report = ansatz.apply_with_report(params, bond_dim=4)
    second, second_report = ansatz.apply_with_report(params, bond_dim=4)

    for actual, expected in zip(first.tensors, second.tensors):
        assert np.array_equal(actual, expected)
    assert first_report == second_report


def test_ansatz_does_not_mutate_supplied_mps():
    ansatz = SymmetricVQEAnsatz(n_qubits=2)
    params = ansatz.initial_parameters(1)
    source = MPS(2, bond_dim=2)
    before = [tensor.copy() for tensor in source.tensors]

    prepared = ansatz.apply(params, bond_dim=2, state=source)

    for actual, expected in zip(source.tensors, before):
        assert np.array_equal(actual, expected)
    assert prepared is not source


@pytest.mark.parametrize("n_qubits", [2, 4, 6])
def test_energy_evaluation_small_n_before_64q(n_qubits):
    ansatz = SymmetricVQEAnsatz(n_qubits=n_qubits)
    params = np.zeros(ansatz.parameter_count)
    convention = TFIMSignConvention(interaction_sign=-1, field_sign=-1)

    result = evaluate_energy(
        params,
        ansatz=ansatz,
        bond_dim=2,
        sign_convention=convention,
    )

    assert np.isfinite(result.energy)
    assert result.state.n_qubits == n_qubits
    assert result.state.max_bond_dimension <= 2
    assert result.truncations == 0


def test_zero_state_energy_matches_open_chain_tfim():
    state = MPS(4, bond_dim=2)
    hamiltonian = build_energy_hamiltonian(
        4,
        sign_convention=TFIMSignConvention(
            interaction_sign=-1,
            field_sign=-1,
        ),
    )
    # |0000>: ZZ=+1 on all 3 bonds, X=0 -> E=-3.
    assert np.isclose(energy_from_state(state, hamiltonian), -3.0)


def test_b12_hamiltonian_has_agent_boundary_terms():
    hamiltonian = build_energy_hamiltonian(
        64,
        sign_convention=TFIMSignConvention(
            interaction_sign=-1,
            field_sign=-1,
        ),
    )
    assert len(hamiltonian.terms) == 129
    boundary = {
        (term.sites, term.operators): term.coefficient
        for term in hamiltonian.terms
        if term.sites in ((21, 22), (43, 44))
    }
    assert boundary[((21, 22), ("Z", "Z"))] == 0.5 + 0j
    assert boundary[((43, 44), ("Z", "Z"))] == 0.5 + 0j
