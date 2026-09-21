"""B1.3 validation of dense reference versus MPS energy."""

import numpy as np
import pytest

from b1_motor.ansatz_b12 import SymmetricVQEAnsatz
from b1_motor.b13.dense_reference import (
    energy_from_dense_state,
    prepare_dense_state,
)
from b1_motor.b13.ed_reference import build_tfim_matrix
from b1_motor.b13.sign_contract import B13_SIGN_CONVENTION
from b1_motor.vqe_b12 import evaluate_energy


SEED = 20260921
TOLERANCE = 1e-10


def _reference(n_qubits: int):
    ansatz = SymmetricVQEAnsatz(n_qubits=n_qubits)
    params = ansatz.initial_parameters(seed=SEED)

    state = prepare_dense_state(
        params,
        n_qubits=n_qubits,
        layers=ansatz.layers,
    )

    hamiltonian = build_tfim_matrix(
        n_qubits=n_qubits,
        J=1.0,
        h=1.0,
    )

    energy = energy_from_dense_state(state, hamiltonian)
    ground = float(np.linalg.eigvalsh(hamiltonian)[0])

    return ansatz, params, energy, ground


def test_dense_reference_is_normalized_and_deterministic():
    ansatz = SymmetricVQEAnsatz(n_qubits=4)
    params = ansatz.initial_parameters(seed=SEED)

    state_a = prepare_dense_state(
        params,
        n_qubits=4,
        layers=ansatz.layers,
    )
    state_b = prepare_dense_state(
        params,
        n_qubits=4,
        layers=ansatz.layers,
    )

    assert state_a.shape == (2**4,)
    assert np.isclose(np.linalg.norm(state_a), 1.0, atol=TOLERANCE)
    assert np.array_equal(state_a, state_b)


def test_mps_matches_dense_n4_chi4():
    ansatz, params, dense_energy, _ = _reference(4)

    result = evaluate_energy(
        params,
        sign_convention=B13_SIGN_CONVENTION,
        ansatz=ansatz,
        bond_dim=4,
    )

    assert result.discarded_weight_squared == 0.0
    assert result.truncations == 0
    assert abs(result.energy - dense_energy) < TOLERANCE


@pytest.mark.parametrize(
    "n_qubits,chi",
    [
        (6, 8),
        (8, 8),
    ],
)
def test_mps_matches_dense_at_zero_truncation(n_qubits, chi):
    ansatz, params, dense_energy, _ = _reference(n_qubits)

    result = evaluate_energy(
        params,
        sign_convention=B13_SIGN_CONVENTION,
        ansatz=ansatz,
        bond_dim=chi,
    )

    assert result.discarded_weight_squared == 0.0
    assert result.truncations == 0
    assert abs(result.energy - dense_energy) < TOLERANCE


@pytest.mark.parametrize(
    "n_qubits,chi",
    [
        (4, 2),
        (6, 2),
        (8, 4),
    ],
)
def test_truncation_produces_observable_energy_difference(n_qubits, chi):
    ansatz, params, dense_energy, _ = _reference(n_qubits)

    result = evaluate_energy(
        params,
        sign_convention=B13_SIGN_CONVENTION,
        ansatz=ansatz,
        bond_dim=chi,
    )

    delta = abs(result.energy - dense_energy)

    assert result.discarded_weight_squared > 0.0
    assert result.truncations > 0
    assert delta > TOLERANCE


def test_variational_and_truncation_errors_are_separate():
    ansatz, params, dense_energy, ground_energy = _reference(8)

    result = evaluate_energy(
        params,
        sign_convention=B13_SIGN_CONVENTION,
        ansatz=ansatz,
        bond_dim=4,
    )

    truncation_error = abs(result.energy - dense_energy)
    variational_error = abs(dense_energy - ground_energy)
    total_ground_error = abs(result.energy - ground_energy)

    assert truncation_error > TOLERANCE
    assert variational_error > TOLERANCE
    assert total_ground_error > TOLERANCE

    assert np.isclose(
        total_ground_error,
        abs(result.energy - ground_energy),
        atol=TOLERANCE,
    )
