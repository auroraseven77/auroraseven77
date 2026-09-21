"""
B1.3 — Exact Diagonalization reference oracle.

IMPORTANT:
    This module intentionally does NOT import b1_motor.mps.

The purpose is to provide an independent reference calculation for
small systems (N=4,6,8), suitable for validating the MPS energy layer.

Hamiltonian convention used by the B1.2 TFIM contract:

    H = -J * sum_i Z_i Z_{i+1}
        -h * sum_i X_i

Additional ZZ interface terms may be supplied explicitly through
`interface_terms`.

The interface terms are deliberately data-driven. B1.3 must not invent
a reduced-N remapping of the 64-qubit interface topology.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class EDResult:
    n_qubits: int
    ground_energy: float
    eigenvalues: tuple[float, ...]


def _pauli_x() -> np.ndarray:
    return np.array(
        [[0.0, 1.0], [1.0, 0.0]],
        dtype=np.complex128,
    )


def _pauli_z() -> np.ndarray:
    return np.array(
        [[1.0, 0.0], [0.0, -1.0]],
        dtype=np.complex128,
    )


def _identity() -> np.ndarray:
    return np.eye(2, dtype=np.complex128)


def _local_operator(
    n_qubits: int,
    operator: np.ndarray,
    site: int,
) -> np.ndarray:
    if n_qubits < 1:
        raise ValueError("n_qubits must be >= 1")
    if not 0 <= site < n_qubits:
        raise ValueError(
            f"site={site} outside [0, {n_qubits - 1}]"
        )

    result = np.array([[1.0]], dtype=np.complex128)

    for q in range(n_qubits):
        factor = operator if q == site else _identity()
        result = np.kron(result, factor)

    return result


def _two_site_operator(
    n_qubits: int,
    operator_a: np.ndarray,
    site_a: int,
    operator_b: np.ndarray,
    site_b: int,
) -> np.ndarray:
    if site_a == site_b:
        raise ValueError("two-site operator requires distinct sites")

    if not 0 <= site_a < n_qubits:
        raise ValueError(f"site_a={site_a} outside system")
    if not 0 <= site_b < n_qubits:
        raise ValueError(f"site_b={site_b} outside system")

    result = np.array([[1.0]], dtype=np.complex128)

    for q in range(n_qubits):
        if q == site_a:
            factor = operator_a
        elif q == site_b:
            factor = operator_b
        else:
            factor = _identity()

        result = np.kron(result, factor)

    return result


def build_tfim_matrix(
    n_qubits: int,
    *,
    J: float = 1.0,
    h: float = 1.0,
    interface_terms: Iterable[tuple[int, int, float]] = (),
) -> np.ndarray:
    """
    Build the complete small-N Hamiltonian independently of the MPS code.

    interface_terms:
        iterable of (site_a, site_b, coupling), representing

            coupling * Z(site_a) Z(site_b)

        The sign is therefore encoded directly in `coupling`.
    """
    if n_qubits < 1:
        raise ValueError("n_qubits must be >= 1")

    H = np.zeros(
        (2**n_qubits, 2**n_qubits),
        dtype=np.complex128,
    )

    X = _pauli_x()
    Z = _pauli_z()

    # Base 1D TFIM.
    for q in range(n_qubits):
        H += -float(h) * _local_operator(n_qubits, X, q)

    for q in range(n_qubits - 1):
        H += -float(J) * _two_site_operator(
            n_qubits,
            Z,
            q,
            Z,
            q + 1,
        )

    # Explicit additional interface couplings.
    for site_a, site_b, coupling in interface_terms:
        H += float(coupling) * _two_site_operator(
            n_qubits,
            Z,
            int(site_a),
            Z,
            int(site_b),
        )

    # Numerical Hermiticity guard for the reference construction.
    H = 0.5 * (H + H.conj().T)

    return H


def exact_diagonalization(
    n_qubits: int,
    *,
    J: float = 1.0,
    h: float = 1.0,
    interface_terms: Iterable[tuple[int, int, float]] = (),
) -> EDResult:
    """
    Independent ED oracle.

    Uses eigh because the Hamiltonian is Hermitian.
    """
    H = build_tfim_matrix(
        n_qubits,
        J=J,
        h=h,
        interface_terms=interface_terms,
    )

    eigenvalues = np.linalg.eigvalsh(H)
    eigenvalues = np.real_if_close(eigenvalues, tol=1000)

    if np.iscomplexobj(eigenvalues):
        raise AssertionError(
            "ED Hamiltonian produced non-real eigenvalues"
        )

    eigenvalues = np.asarray(eigenvalues, dtype=np.float64)

    return EDResult(
        n_qubits=n_qubits,
        ground_energy=float(eigenvalues[0]),
        eigenvalues=tuple(float(x) for x in eigenvalues),
    )
