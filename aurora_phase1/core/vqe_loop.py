"""Loop VQE multiagente.

Ciclo:
    proposer → measurer → communicator → observer → (loop ou para)

Invariantes:
- Papéis são funções puras determinísticas
- Proposer varia em torno dos melhores params (heurística simples)
- Measurer consulta o QuantumBridge
- Nenhum agente escreve no ledger diretamente (só o TUU escreve)
- Determinismo: mesma seed → mesmo resultado
- Para quando convergir ou atingir max_iterations
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from aurora_phase1.core.crypto import hash_object
from aurora_phase1.core.quantum_bridge import (
    QuantumBridge,
    STATUS_MEASUREMENT_COMPLETED,
)


@dataclass
class VQEIteration:
    iteration: int
    params: tuple[float, ...]
    energy: float
    measurement_hash: Optional[str]
    converged_this_iteration: bool

    def to_dict(self) -> dict:
        return {
            "iteration": self.iteration,
            "params": list(self.params),
            "energy": self.energy,
            "measurement_hash": self.measurement_hash,
            "converged_this_iteration": self.converged_this_iteration,
        }


@dataclass
class VQEResult:
    iterations: int
    final_energy: float
    converged: bool
    target_energy: float
    max_iterations_reached: bool
    history: list[VQEIteration]
    result_hash: str

    def to_dict(self) -> dict:
        return {
            "iterations": self.iterations,
            "final_energy": self.final_energy,
            "converged": self.converged,
            "target_energy": self.target_energy,
            "max_iterations_reached": self.max_iterations_reached,
            "history": [h.to_dict() for h in self.history],
            "result_hash": self.result_hash,
        }


class VQELoop:
    """Loop VQE com 4 papéis determinísticos."""

    def __init__(
        self,
        bridge: QuantumBridge,
        policy: dict,
        *,
        tuu=None,
    ):
        if not isinstance(bridge, QuantumBridge):
            raise TypeError("bridge deve ser QuantumBridge")
        if not isinstance(policy, dict):
            raise TypeError("policy deve ser dict")

        for f in ("max_iterations", "convergence_threshold"):
            if f not in policy:
                raise ValueError(f"policy sem campo obrigatório: {f}")

        self._bridge = bridge
        self._policy = copy.deepcopy(policy)
        self._tuu = tuu  # opcional

        self._max_iterations = policy["max_iterations"]
        self._threshold = policy["convergence_threshold"]
        self._perturbation_scale = policy.get(
            "proposer", {}
        ).get("perturbation_scale", 0.1)
        self._n_qubits = policy.get("n_qubits_default", 4)
        self._bond_dim = policy.get("bond_dim_default", 8)

    # ---- papéis (funções puras) ----

    def _proposer(
        self,
        iteration: int,
        current_best_params: Optional[tuple[float, ...]],
        rng: np.random.Generator,
        param_count: int,
    ) -> tuple[float, ...]:
        """Propõe params: primeira iteração gera do zero;
        demais variam em torno do melhor."""
        if current_best_params is None:
            return tuple(
                float(x) for x in rng.uniform(-np.pi, np.pi, size=param_count)
            )

        perturbed = np.array(current_best_params, dtype=np.float64)
        noise = rng.normal(0.0, self._perturbation_scale, size=param_count)
        return tuple(float(x) for x in (perturbed + noise))

    def _measurer(
        self,
        params: tuple[float, ...],
        ansatz_id: str,
    ) -> tuple[Optional[float], Optional[str]]:
        """Mede energia via bridge. Retorna (energy, measurement_hash)."""
        # Modelo simplificado: usa expectation de Z em cada qubit
        # com coeficiente proporcional ao param.
        terms = []
        for i, p in enumerate(params[: self._n_qubits]):
            terms.append({
                "sites": [i],
                "operators": ["Z"],
                "coefficient": float(np.cos(p)),
            })
        if not terms:
            return None, None

        proposal = {
            "proposal_id": hash_object({
                "ansatz_id": ansatz_id,
                "params": list(params),
                "iteration_tag": "measure",
            }),
            "observation_data": {
                "n_qubits": self._n_qubits,
                "terms": terms,
            },
        }
        result = self._bridge.execute_measurement(proposal)
        if result.status != STATUS_MEASUREMENT_COMPLETED:
            return None, None
        return result.value_real, result.measurement_hash

    @staticmethod
    def _communicator(energy: float, iteration: int) -> dict:
        """Empacota resultado para o observer."""
        return {
            "iteration": iteration,
            "energy": energy,
            "delta_from_target": None,  # preenchido depois
        }

    @staticmethod
    def _observer(
        communicated: dict,
        target_energy: float,
        threshold: float,
        iteration: int,
        max_iterations: int,
    ) -> tuple[bool, bool]:
        """Retorna (converged, stop)."""
        delta = abs(communicated["energy"] - target_energy)
        converged = delta <= threshold
        stop = converged or (iteration + 1 >= max_iterations)
        return converged, stop

    # ---- loop ----

    def run(
        self,
        seed: int,
        target_energy: float,
        *,
        param_count: Optional[int] = None,
    ) -> VQEResult:
        """Executa o loop VQE. Determinístico por seed."""
        if not isinstance(seed, int):
            raise TypeError("seed deve ser int")

        param_count = param_count or (self._n_qubits * 3 * 2)
        rng = np.random.default_rng(seed)

        history: list[VQEIteration] = []
        best_params: Optional[tuple[float, ...]] = None
        best_energy: Optional[float] = None
        converged = False
        max_reached = False
        last_energy: Optional[float] = None

        ansatz_id = hash_object({
            "seed": seed,
            "n_qubits": self._n_qubits,
            "policy_id": self._policy["contract_id"],
        })

        for iteration in range(self._max_iterations):
            # 1. Proposer
            params = self._proposer(
                iteration, best_params, rng, param_count
            )

            # 2. Measurer
            energy, m_hash = self._measurer(params, ansatz_id)
            if energy is None:
                # Medição falhou: para o loop com erro explícito
                result_hash = hash_object({
                    "ansatz_id": ansatz_id,
                    "iterations": iteration,
                    "error": "measurement_failed",
                })
                return VQEResult(
                    iterations=iteration,
                    final_energy=float("nan"),
                    converged=False,
                    target_energy=target_energy,
                    max_iterations_reached=False,
                    history=history,
                    result_hash=result_hash,
                )

            # 3. Communicator
            communicated = self._communicator(energy, iteration)
            communicated["delta_from_target"] = abs(energy - target_energy)

            # 4. Observer
            converged, stop = self._observer(
                communicated,
                target_energy,
                self._threshold,
                iteration,
                self._max_iterations,
            )

            hist_entry = VQEIteration(
                iteration=iteration,
                params=params,
                energy=energy,
                measurement_hash=m_hash,
                converged_this_iteration=converged,
            )
            history.append(hist_entry)

            # atualiza melhor
            if best_energy is None or energy < best_energy:
                best_energy = energy
                best_params = params

            last_energy = energy

            # se convergiu, guarda o melhor
            if converged:
                best_params = params
                best_energy = energy

            if stop:
                max_reached = (not converged) and (
                    iteration + 1 >= self._max_iterations
                )
                break

        result_hash = hash_object({
            "ansatz_id": ansatz_id,
            "iterations": len(history),
            "final_energy": best_energy,
            "converged": converged,
            "target_energy": target_energy,
            "history_hashes": [h.measurement_hash for h in history],
        })

        return VQEResult(
            iterations=len(history),
            final_energy=float(best_energy) if best_energy is not None else float("nan"),
            converged=converged,
            target_energy=target_energy,
            max_iterations_reached=max_reached,
            history=history,
            result_hash=result_hash,
        )


__all__ = ["VQELoop", "VQEResult", "VQEIteration"]
