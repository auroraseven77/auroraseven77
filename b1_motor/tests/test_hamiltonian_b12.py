import numpy as np

from b1_motor.hamiltonian_b12 import (
    B12_N_QUBITS,
    TFIMSignConvention,
    build_b12_hamiltonian,
)
from b1_motor.mps import MPS
from b1_motor.observables import expectation


def test_b12_hamiltonian_shape_and_agent_boundaries():
    hamiltonian = build_b12_hamiltonian(
        sign_convention=TFIMSignConvention(
            interaction_sign=-1,
            field_sign=-1,
        )
    )
    assert len(hamiltonian.terms) == 64 + 63 + 2

    boundary_terms = [
        term
        for term in hamiltonian.terms
        if term.sites in ((21, 22), (43, 44))
    ]
    assert [term.coefficient for term in boundary_terms] == [0.5 + 0j, 0.5 + 0j]
    assert all(term.operators == ("Z", "Z") for term in boundary_terms)


def test_b12_signs_are_explicit():
    plus = build_b12_hamiltonian(
        sign_convention=TFIMSignConvention(
            interaction_sign=1,
            field_sign=1,
        )
    )
    minus = build_b12_hamiltonian(
        sign_convention=TFIMSignConvention(
            interaction_sign=-1,
            field_sign=-1,
        )
    )
    assert plus.terms[0].coefficient == 1.0 + 0j
    assert plus.terms[63].coefficient == 1.0 + 0j
    assert minus.terms[0].coefficient == -1.0 + 0j
    assert minus.terms[63].coefficient == -1.0 + 0j


def test_b12_hamiltonian_runs_on_mps_without_dense_statevector():
    state = MPS(B12_N_QUBITS, bond_dim=2)
    hamiltonian = build_b12_hamiltonian(
        sign_convention=TFIMSignConvention(
            interaction_sign=-1,
            field_sign=-1,
        )
    )
    value = expectation(state, hamiltonian)
    assert np.isfinite(value.real)
    assert abs(value.imag) < 1e-12
