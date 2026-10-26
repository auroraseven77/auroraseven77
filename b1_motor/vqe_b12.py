from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from b1_motor.ansatz_b12 import SymmetricVQEAnsatz
from b1_motor.hamiltonian_b12 import (
    B12_H,
    B12_J,
    TFIMSignConvention,
    build_b12_hamiltonian,
)
from b1_motor.mps import MPS
from b1_motor.observables import PauliSum, PauliTerm, expectation


@dataclass(frozen=True)
class EnergyEvaluation:
    energy: float
    state: MPS
    discarded_weight_squared: float
    truncations: int


def build_tfim_hamiltonian(
    n_qubits: int,
    *,
    J: float = B12_J,
    h: float = B12_H,
    sign_convention: TFIMSignConvention,
) -> PauliSum:
    """Build an open-chain TFIM PauliSum for arbitrary small-N contract tests."""
    if not isinstance(n_qubits, (int, np.integer)):
        raise TypeError("n_qubits must be an integer")
    if n_qubits < 1:
        raise ValueError("n_qubits must be >= 1")
    if not np.isfinite(J) or not np.isfinite(h):
        raise ValueError("J and h must be finite")

    terms: list[PauliTerm] = []
    for site in range(n_qubits - 1):
        terms.append(
            PauliTerm(
                sites=(site, site + 1),
                operators=("Z", "Z"),
                coefficient=sign_convention.interaction_sign * J,
            )
        )
    for site in range(n_qubits):
        terms.append(
            PauliTerm(
                sites=(site,),
                operators=("X",),
                coefficient=sign_convention.field_sign * h,
            )
        )
    return PauliSum(tuple(terms))


def build_energy_hamiltonian(
    n_qubits: int,
    *,
    sign_convention: TFIMSignConvention,
) -> PauliSum:
    """Return B1.2 H at N=64, or base TFIM for small-N integration tests."""
    if n_qubits == 64:
        return build_b12_hamiltonian(sign_convention=sign_convention)
    return build_tfim_hamiltonian(
        n_qubits,
        J=B12_J,
        h=B12_H,
        sign_convention=sign_convention,
    )


def energy_from_state(state: MPS, hamiltonian: PauliSum) -> float:
    """Evaluate E=<psi|H|psi> directly from MPS observables."""
    value = expectation(state, hamiltonian)
    if abs(value.imag) > 1e-10:
        raise ValueError(f"Hamiltonian expectation is not real: {value}")
    return float(value.real)


def evaluate_energy(
    params,
    *,
    sign_convention: TFIMSignConvention,
    ansatz: SymmetricVQEAnsatz | None = None,
    bond_dim: int = 128,
) -> EnergyEvaluation:
    """Prepare the MPS ansatz and evaluate its energy without statevectors.

    N=64 includes the two +0.5 ZZ agent-boundary terms. Small-N executions
    intentionally use only the base open-chain TFIM so the integration can
    be tested before any 64-qubit run.
    """
    selected = ansatz or SymmetricVQEAnsatz()
    state, report = selected.apply_with_report(params, bond_dim=bond_dim)
    hamiltonian = build_energy_hamiltonian(
        selected.n_qubits,
        sign_convention=sign_convention,
    )
    energy = energy_from_state(state, hamiltonian)
    return EnergyEvaluation(
        energy=energy,
        state=state,
        discarded_weight_squared=report.total_discarded_weight_squared,
        truncations=report.truncations,
    )
