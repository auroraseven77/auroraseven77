"""Ponte entre o Centro e o motor quântico canônico b1_motor.

O bridge recebe propostas estruturadas de medição (não código) e as
traduz para chamadas ao b1_motor. Nunca executa código arbitrário.
Nunca materializa statevector global.

Invariantes:
- Consome b1_motor (não é cópia própria)
- Só aceita parâmetros estruturados (sites, operators, coefficient)
- Valida contra contrato antes de executar
- measurement_hash determinístico
- Não modifica b1_motor
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Optional

from aurora_phase1.core.crypto import hash_object

from b1_motor.observables import PauliTerm, PauliSum, expectation
from b1_motor.mps import MPS


STATUS_MEASUREMENT_COMPLETED = "MEASUREMENT_COMPLETED"
STATUS_REJECTED_MALFORMED = "REJECTED_MALFORMED"
STATUS_REJECTED_QUBIT_LIMIT = "REJECTED_QUBIT_LIMIT"
STATUS_REJECTED_INVALID_OPERATOR = "REJECTED_INVALID_OPERATOR"
STATUS_REJECTED_INVALID_SITE = "REJECTED_INVALID_SITE"
STATUS_REJECTED_TOO_MANY_TERMS = "REJECTED_TOO_MANY_TERMS"
STATUS_REJECTED_CONTENT_VIOLATION = "REJECTED_CONTENT_VIOLATION"
STATUS_REJECTED_DUPLICATE_SITE = "REJECTED_DUPLICATE_SITE"
STATUS_REJECTED_NOT_SORTED = "REJECTED_NOT_SORTED"


@dataclass
class MeasurementResult:
    status: str
    value_real: Optional[float]
    value_imag: Optional[float]
    measurement_hash: Optional[str]
    backend: str
    n_qubits: Optional[int]
    n_terms: Optional[int]
    error_type: Optional[str] = None
    error_message: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "value_real": self.value_real,
            "value_imag": self.value_imag,
            "measurement_hash": self.measurement_hash,
            "backend": self.backend,
            "n_qubits": self.n_qubits,
            "n_terms": self.n_terms,
            "error_type": self.error_type,
            "error_message": self.error_message,
        }


def _reject(
    status: str,
    error_type: str,
    error_message: str,
    *,
    n_qubits: Optional[int] = None,
    n_terms: Optional[int] = None,
) -> MeasurementResult:
    return MeasurementResult(
        status=status,
        value_real=None,
        value_imag=None,
        measurement_hash=None,
        backend="b1_motor",
        n_qubits=n_qubits,
        n_terms=n_terms,
        error_type=error_type,
        error_message=error_message,
    )


class QuantumBridge:
    """Mediador entre propostas de medição e b1_motor."""

    def __init__(self, contract: dict):
        if not isinstance(contract, dict):
            raise TypeError("contract deve ser dict")

        for f in ("allowed_observables", "max_qubits", "max_terms", "backend"):
            if f not in contract:
                raise ValueError(f"contract sem campo obrigatório: {f}")

        if contract["backend"] != "b1_motor":
            raise ValueError(
                f"backend inválido: {contract['backend']}. "
                f"Esperado: 'b1_motor'"
            )

        self._contract = contract
        self._allowed_observables = set(contract["allowed_observables"])
        self._max_qubits = contract["max_qubits"]
        self._max_terms = contract["max_terms"]
        self._denied_patterns = contract.get("denied_patterns", [])
        self._default_bond_dim = contract.get("default_bond_dim", 8)
        self._default_state_type = contract.get(
            "default_state_type", "zeros"
        )

    def _validate(self, proposal: dict) -> Optional[MeasurementResult]:
        if not isinstance(proposal, dict):
            return _reject(
                STATUS_REJECTED_MALFORMED,
                "REJECTED_MALFORMED",
                "proposal deve ser dict",
            )

        obs_data = proposal.get("observation_data")
        if not isinstance(obs_data, dict):
            return _reject(
                STATUS_REJECTED_MALFORMED,
                "REJECTED_MALFORMED",
                "observation_data ausente ou não-dict",
            )

        n_qubits = obs_data.get("n_qubits")
        if not isinstance(n_qubits, int) or n_qubits <= 0:
            return _reject(
                STATUS_REJECTED_MALFORMED,
                "REJECTED_MALFORMED",
                f"n_qubits inválido: {n_qubits!r}",
            )

        if n_qubits > self._max_qubits:
            return _reject(
                STATUS_REJECTED_QUBIT_LIMIT,
                "REJECTED_QUBIT_LIMIT",
                f"n_qubits={n_qubits} excede max_qubits={self._max_qubits}",
                n_qubits=n_qubits,
            )

        raw_terms = obs_data.get("terms")
        if not isinstance(raw_terms, list) or not raw_terms:
            return _reject(
                STATUS_REJECTED_MALFORMED,
                "REJECTED_MALFORMED",
                "terms ausente ou vazio",
                n_qubits=n_qubits,
            )

        if len(raw_terms) > self._max_terms:
            return _reject(
                STATUS_REJECTED_TOO_MANY_TERMS,
                "REJECTED_TOO_MANY_TERMS",
                f"len(terms)={len(raw_terms)} excede max_terms={self._max_terms}",
                n_qubits=n_qubits,
            )

        flat = json.dumps(obs_data, ensure_ascii=False, default=str)
        for pat in self._denied_patterns:
            if re.search(pat, flat):
                return _reject(
                    STATUS_REJECTED_CONTENT_VIOLATION,
                    "REJECTED_CONTENT_VIOLATION",
                    f"proposal bate em denied_pattern: {pat}",
                    n_qubits=n_qubits,
                )

        for i, t in enumerate(raw_terms):
            if not isinstance(t, dict):
                return _reject(
                    STATUS_REJECTED_MALFORMED,
                    "REJECTED_MALFORMED",
                    f"term {i} não é dict",
                    n_qubits=n_qubits,
                )

            sites = t.get("sites")
            operators = t.get("operators")
            coefficient = t.get("coefficient", 1.0)

            if not isinstance(sites, list) or not sites:
                return _reject(
                    STATUS_REJECTED_MALFORMED,
                    "REJECTED_MALFORMED",
                    f"term {i}: sites ausente ou vazio",
                    n_qubits=n_qubits,
                )
            if not isinstance(operators, list) or not operators:
                return _reject(
                    STATUS_REJECTED_MALFORMED,
                    "REJECTED_MALFORMED",
                    f"term {i}: operators ausente ou vazio",
                    n_qubits=n_qubits,
                )
            if len(sites) != len(operators):
                return _reject(
                    STATUS_REJECTED_MALFORMED,
                    "REJECTED_MALFORMED",
                    f"term {i}: sites e operators de tamanhos diferentes",
                    n_qubits=n_qubits,
                )

            for s in sites:
                if not isinstance(s, int) or s < 0 or s >= n_qubits:
                    return _reject(
                        STATUS_REJECTED_INVALID_SITE,
                        "REJECTED_INVALID_SITE",
                        f"term {i}: site {s!r} inválido (0..{n_qubits-1})",
                        n_qubits=n_qubits,
                    )
            if len(set(sites)) != len(sites):
                return _reject(
                    STATUS_REJECTED_DUPLICATE_SITE,
                    "REJECTED_DUPLICATE_SITE",
                    f"term {i}: sites duplicados",
                    n_qubits=n_qubits,
                )
            if any(b <= a for a, b in zip(sites, sites[1:])):
                return _reject(
                    STATUS_REJECTED_NOT_SORTED,
                    "REJECTED_NOT_SORTED",
                    f"term {i}: sites devem ser estritamente crescentes",
                    n_qubits=n_qubits,
                )

            for op in operators:
                if op not in self._allowed_observables:
                    return _reject(
                        STATUS_REJECTED_INVALID_OPERATOR,
                        "REJECTED_INVALID_OPERATOR",
                        f"term {i}: operador {op!r} não permitido "
                        f"(permitidos: {sorted(self._allowed_observables)})",
                        n_qubits=n_qubits,
                    )

            if not isinstance(coefficient, (int, float, complex)):
                return _reject(
                    STATUS_REJECTED_MALFORMED,
                    "REJECTED_MALFORMED",
                    f"term {i}: coefficient deve ser numérico",
                    n_qubits=n_qubits,
                )

        return None

    def execute_measurement(self, proposal: dict) -> MeasurementResult:
        rejection = self._validate(proposal)
        if rejection is not None:
            return rejection

        obs_data = proposal["observation_data"]
        n_qubits = obs_data["n_qubits"]
        raw_terms = obs_data["terms"]

        try:
            state = MPS(n_qubits=n_qubits, bond_dim=self._default_bond_dim)
        except Exception as e:
            return _reject(
                STATUS_REJECTED_MALFORMED,
                "REJECTED_MPS_CONSTRUCTION_FAILED",
                f"falha ao construir MPS: {e}",
                n_qubits=n_qubits,
            )

        try:
            terms = []
            for t in raw_terms:
                terms.append(
                    PauliTerm(
                        sites=tuple(t["sites"]),
                        operators=tuple(t["operators"]),
                        coefficient=t.get("coefficient", 1.0),
                    )
                )
            observable = PauliSum(tuple(terms))
        except Exception as e:
            return _reject(
                STATUS_REJECTED_MALFORMED,
                "REJECTED_PAULI_CONSTRUCTION_FAILED",
                f"falha ao construir PauliSum: {e}",
                n_qubits=n_qubits,
            )

        try:
            raw_value = expectation(state, observable)
            value_complex = complex(raw_value)
        except Exception as e:
            return _reject(
                STATUS_REJECTED_MALFORMED,
                "REJECTED_EXPECTATION_FAILED",
                f"falha na medição: {e}",
                n_qubits=n_qubits,
            )

        value_real = float(value_complex.real)
        value_imag = float(value_complex.imag)

        measurement_hash = hash_object({
            "proposal_id": proposal.get("proposal_id"),
            "n_qubits": n_qubits,
            "terms": raw_terms,
            "value_real": value_real,
            "value_imag": value_imag,
            "backend": "b1_motor",
        })

        return MeasurementResult(
            status=STATUS_MEASUREMENT_COMPLETED,
            value_real=value_real,
            value_imag=value_imag,
            measurement_hash=measurement_hash,
            backend="b1_motor",
            n_qubits=n_qubits,
            n_terms=len(raw_terms),
        )


__all__ = [
    "QuantumBridge",
    "MeasurementResult",
    "STATUS_MEASUREMENT_COMPLETED",
    "STATUS_REJECTED_MALFORMED",
    "STATUS_REJECTED_QUBIT_LIMIT",
    "STATUS_REJECTED_INVALID_OPERATOR",
    "STATUS_REJECTED_INVALID_SITE",
    "STATUS_REJECTED_TOO_MANY_TERMS",
    "STATUS_REJECTED_CONTENT_VIOLATION",
    "STATUS_REJECTED_DUPLICATE_SITE",
    "STATUS_REJECTED_NOT_SORTED",
]
