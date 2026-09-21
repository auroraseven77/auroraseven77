from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

_PAULI_SYMBOLS = frozenset({"I", "X", "Y", "Z"})
_PAULI = {
    "I": np.eye(2, dtype=np.complex128),
    "X": np.array([[0, 1], [1, 0]], dtype=np.complex128),
    "Y": np.array([[0, -1j], [1j, 0]], dtype=np.complex128),
    "Z": np.array([[1, 0], [0, -1]], dtype=np.complex128),
}


def _validate_term(sites: tuple[int, ...], operators: tuple[str, ...]) -> None:
    if len(sites) != len(operators):
        raise ValueError("sites and operators must have the same length")
    if len(set(sites)) != len(sites):
        raise ValueError("sites must not contain duplicates")
    if any(not isinstance(site, (int, np.integer)) for site in sites):
        raise TypeError("sites must contain only integers")
    if any(b <= a for a, b in zip(sites, sites[1:])):
        raise ValueError("sites must be strictly increasing")
    if any(operator not in _PAULI_SYMBOLS for operator in operators):
        raise ValueError("operators must contain only I, X, Y, or Z")


@dataclass(frozen=True)
class PauliTerm:
    sites: tuple[int, ...]
    operators: tuple[str, ...]
    coefficient: complex = 1.0

    def __post_init__(self) -> None:
        sites = tuple(self.sites)
        operators = tuple(self.operators)
        _validate_term(sites, operators)
        if not np.isfinite(self.coefficient):
            raise ValueError("coefficient must be finite")
        object.__setattr__(self, "sites", sites)
        object.__setattr__(self, "operators", operators)
        object.__setattr__(self, "coefficient", complex(self.coefficient))

    @property
    def support(self) -> tuple[int, ...]:
        return self.sites


@dataclass(frozen=True)
class PauliSum:
    terms: tuple[PauliTerm, ...]

    def __post_init__(self) -> None:
        terms = tuple(self.terms)
        if not all(isinstance(term, PauliTerm) for term in terms):
            raise TypeError("terms must contain only PauliTerm instances")
        object.__setattr__(self, "terms", terms)


def _expectation_term(state, term: PauliTerm) -> complex:
    site_to_operator = dict(zip(term.sites, term.operators))
    env = np.ones((1, 1), dtype=np.complex128)

    for index, tensor in enumerate(state.tensors):
        operator = _PAULI.get(site_to_operator.get(index, "I"))
        env = np.einsum(
            "ab,air,ij,bjs->rs",
            env,
            tensor.conj(),
            operator,
            tensor,
            optimize=True,
        )

    return complex(env[0, 0])


def expectation(state, observable: PauliTerm | PauliSum) -> complex:
    """Evaluate a Pauli observable directly on the MPS.

    This is read-only: it does not mutate tensors, canonicalize, normalize,
    truncate, or materialize a global statevector.
    """
    if not hasattr(state, "tensors") or not hasattr(state, "n_qubits"):
        raise TypeError("state must provide MPS tensors and n_qubits")

    terms = (observable,) if isinstance(observable, PauliTerm) else observable.terms
    if not isinstance(observable, (PauliTerm, PauliSum)):
        raise TypeError("observable must be PauliTerm or PauliSum")

    for term in terms:
        if any(site < 0 or site >= state.n_qubits for site in term.sites):
            raise ValueError(
                f"observable site must satisfy 0 <= site < {state.n_qubits}"
            )

    return sum(
        (term.coefficient * _expectation_term(state, term) for term in terms),
        0j,
    )
