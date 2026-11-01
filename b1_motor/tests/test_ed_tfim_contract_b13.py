from __future__ import annotations

import numpy as np
import pytest

from b1_motor.b13.ed_reference import (
    build_tfim_matrix,
    exact_diagonalization,
)
from b1_motor.hamiltonian_b12 import TFIMSignConvention
from b1_motor.vqe_b12 import build_tfim_hamiltonian


def _pauli_matrix(
    n_qubits: int,
    sites: tuple[int, ...],
    operators: tuple[str, ...],
) -> np.ndarray:
    I = np.eye(2, dtype=np.complex128)
    X = np.array(
        [[0.0, 1.0], [1.0, 0.0]],
        dtype=np.complex128,
    )
    Z = np.array(
        [[1.0, 0.0], [0.0, -1.0]],
        dtype=np.complex128,
    )

    lookup = {"I": I, "X": X, "Z": Z}

    result = np.array([[1.0]], dtype=np.complex128)

    mapping = dict(zip(sites, operators))

    for q in range(n_qubits):
        result = np.kron(
            result,
            lookup[mapping.get(q, "I")],
        )

    return result


def pauli_sum_to_dense(hamiltonian, n_qubits: int) -> np.ndarray:
    result = np.zeros(
        (2**n_qubits, 2**n_qubits),
        dtype=np.complex128,
    )

    for term in hamiltonian.terms:
        result += term.coefficient * _pauli_matrix(
            n_qubits,
            term.sites,
            term.operators,
        )

    return result


@pytest.mark.parametrize("n_qubits", [4, 6, 8])
@pytest.mark.parametrize(
    "interaction_sign,field_sign",
    [
        (-1, -1),
        (-1, 1),
        (1, -1),
        (1, 1),
    ],
)
def test_ed_matches_b12_small_n_tfim_contract(
    n_qubits: int,
    interaction_sign: int,
    field_sign: int,
) -> None:
    convention = TFIMSignConvention(
        interaction_sign=interaction_sign,
        field_sign=field_sign,
    )

    b12 = build_tfim_hamiltonian(
        n_qubits,
        J=1.0,
        h=1.0,
        sign_convention=convention,
    )

    dense_b12 = pauli_sum_to_dense(b12, n_qubits)

    dense_ed = build_tfim_matrix(
        n_qubits,
        J=1.0,
        h=1.0,
        interface_terms=(),
    )

    # The ED oracle uses the same explicitly supplied signs.
    #
    # build_tfim_matrix's canonical construction is intentionally
    # independent from the B1.2 PauliSum implementation, so its
    # default convention is -J ZZ -h X. For the other sign combinations
    # construct the independent reference directly below.
    if (interaction_sign, field_sign) != (-1, -1):
        dim = 2**n_qubits
        dense_ed = np.zeros(
            (dim, dim),
            dtype=np.complex128,
        )

        X = np.array(
            [[0.0, 1.0], [1.0, 0.0]],
            dtype=np.complex128,
        )
        Z = np.array(
            [[1.0, 0.0], [0.0, -1.0]],
            dtype=np.complex128,
        )
        I = np.eye(2, dtype=np.complex128)

        def op(site_ops):
            result = np.array([[1.0]], dtype=np.complex128)
            mapping = dict(site_ops)

            for q in range(n_qubits):
                result = np.kron(
                    result,
                    mapping.get(q, I),
                )
            return result

        for q in range(n_qubits):
            dense_ed += field_sign * op(((q, X),))

        for q in range(n_qubits - 1):
            dense_ed += interaction_sign * op(
                ((q, Z), (q + 1, Z))
            )

    assert np.allclose(
        dense_b12,
        dense_ed,
        atol=1e-12,
        rtol=1e-12,
    )


@pytest.mark.parametrize("n_qubits", [4, 6, 8])
@pytest.mark.parametrize(
    "site_a,site_b",
    [(21, 22), (22, 21), (43, 44), (44, 43)],
)
def test_ed_interface_coordinates_are_rejected_not_remapped(
    n_qubits: int,
    site_a: int,
    site_b: int,
) -> None:
    # The physical B1.2 interface coordinates are outside these reduced
    # small-N systems. The actual oracle must reject them, not merely document
    # that the constants happen to be larger than N.
    with pytest.raises(ValueError, match="outside system"):
        build_tfim_matrix(
            n_qubits,
            interface_terms=((site_a, site_b, 0.5),),
        )
