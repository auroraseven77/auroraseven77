from __future__ import annotations

from dataclasses import dataclass

from b1_motor.observables import PauliSum, PauliTerm

B12_N_QUBITS = 64
B12_BOND_DIM = 128
B12_J = 1.0
B12_H = 1.0
B12_AGENT_COUPLING = 0.5


@dataclass(frozen=True)
class TFIMSignConvention:
    """Explicit sign convention for the two TFIM term families.

    The B1.2 manifest declares J=1 and h=1 but does not declare their signs.
    Therefore callers must select the signs explicitly; this module never
    silently chooses one.
    """

    interaction_sign: int
    field_sign: int

    def __post_init__(self) -> None:
        if self.interaction_sign not in (-1, 1):
            raise ValueError("interaction_sign must be +1 or -1")
        if self.field_sign not in (-1, 1):
            raise ValueError("field_sign must be +1 or -1")


def build_b12_hamiltonian(*, sign_convention: TFIMSignConvention) -> PauliSum:
    """Build the sealed B1.2 64-qubit Hamiltonian.

    H = s_J J sum_{i=0}^{63-1} Z_i Z_{i+1}
        + s_h h sum_{i=0}^{63} X_i
        + 0.5 Z_21 Z_22
        + 0.5 Z_43 Z_44

    The manifest leaves s_J and s_h unspecified, so they are mandatory input.
    """
    terms: list[PauliTerm] = []

    for site in range(B12_N_QUBITS - 1):
        terms.append(
            PauliTerm(
                sites=(site, site + 1),
                operators=("Z", "Z"),
                coefficient=sign_convention.interaction_sign * B12_J,
            )
        )

    for site in range(B12_N_QUBITS):
        terms.append(
            PauliTerm(
                sites=(site,),
                operators=("X",),
                coefficient=sign_convention.field_sign * B12_H,
            )
        )

    terms.extend(
        (
            PauliTerm(
                sites=(21, 22),
                operators=("Z", "Z"),
                coefficient=B12_AGENT_COUPLING,
            ),
            PauliTerm(
                sites=(43, 44),
                operators=("Z", "Z"),
                coefficient=B12_AGENT_COUPLING,
            ),
        )
    )

    return PauliSum(tuple(terms))
