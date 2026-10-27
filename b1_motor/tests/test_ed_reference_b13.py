"""B1.3 tests for the independent Exact Diagonalization oracle."""

from __future__ import annotations

import numpy as np
import pytest

from b1_motor.b13.ed_reference import (
    build_tfim_matrix,
    exact_diagonalization,
)


@pytest.mark.parametrize("n_qubits", [4, 6, 8])
def test_ed_hamiltonian_is_hermitian(n_qubits: int) -> None:
    H = build_tfim_matrix(n_qubits)

    assert H.shape == (2**n_qubits, 2**n_qubits)
    assert np.allclose(H, H.conj().T)


@pytest.mark.parametrize("n_qubits", [4, 6, 8])
def test_ed_spectrum_is_real_and_sorted(n_qubits: int) -> None:
    result = exact_diagonalization(n_qubits)

    values = np.asarray(result.eigenvalues)

    assert np.all(np.isfinite(values))
    assert np.allclose(values.imag, 0.0)
    assert np.all(values[:-1] <= values[1:])


@pytest.mark.parametrize("n_qubits", [4, 6, 8])
def test_ed_ground_energy_is_finite(n_qubits: int) -> None:
    result = exact_diagonalization(n_qubits)

    assert np.isfinite(result.ground_energy)


def test_interface_term_is_explicit_and_independent() -> None:
    H_base = build_tfim_matrix(4)

    H_with_interface = build_tfim_matrix(
        4,
        interface_terms=((0, 3, 0.5),),
    )

    assert not np.allclose(H_base, H_with_interface)

    # The extra term is exactly +0.5 Z_0 Z_3.
    Z = np.array(
        [[1.0, 0.0], [0.0, -1.0]],
        dtype=np.complex128,
    )
    I = np.eye(2, dtype=np.complex128)

    expected_term = 0.5
    expected = expected_term

    term = np.array([[1.0]], dtype=np.complex128)
    for q in range(4):
        term = np.kron(
            term,
            Z if q in (0, 3) else I,
        )

    assert np.allclose(
        H_with_interface - H_base,
        expected * term,
    )
