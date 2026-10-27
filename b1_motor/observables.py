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
    if any(
        isinstance(site, (bool, np.bool_))
        or not isinstance(site, (int, np.integer))
        for site in sites
    ):
        raise TypeError("sites must contain only integers (not booleans)")
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


def _norm_squared(state) -> float:
    """Contract <psi|psi> without constructing a dense state vector."""
    env = np.ones((1, 1), dtype=np.complex128)
    for tensor in state.tensors:
        if not isinstance(tensor, np.ndarray) or tensor.ndim != 3:
            raise ValueError("state tensors must be rank-3 NumPy arrays")
        if tensor.shape[0] != env.shape[0]:
            raise ValueError("MPS tensor left bond is inconsistent with its environment")
        env = np.einsum(
            "ab,air,bis->rs",
            env,
            tensor.conj(),
            tensor,
            optimize=True,
        )
    value = complex(env[0, 0])
    if not np.isfinite(value.real) or not np.isfinite(value.imag):
        raise ValueError("MPS state norm must be finite")
    if abs(value.imag) > 1e-10 or value.real <= 0.0:
        raise ValueError("MPS state must have a positive real norm")
    return float(value.real)


def expectation(state, observable: PauliTerm | PauliSum) -> complex:
    """Evaluate a normalized Pauli expectation directly on the MPS.

    The value is <psi|O|psi>/<psi|psi>, so truncation-related loss of norm
    does not silently scale the reported observable. The contraction is
    read-only and never materializes a global state vector.
    """
    if not hasattr(state, "tensors") or not hasattr(state, "n_qubits"):
        raise TypeError("state must provide MPS tensors and n_qubits")
    if not isinstance(observable, (PauliTerm, PauliSum)):
        raise TypeError("observable must be PauliTerm or PauliSum")

    terms = (observable,) if isinstance(observable, PauliTerm) else observable.terms
    for term in terms:
        if any(site < 0 or site >= state.n_qubits for site in term.sites):
            raise ValueError(
                f"observable site must satisfy 0 <= site < {state.n_qubits}"
            )

    numerator = sum(
        (term.coefficient * _expectation_term(state, term) for term in terms),
        0j,
    )
    return numerator / _norm_squared(state)
