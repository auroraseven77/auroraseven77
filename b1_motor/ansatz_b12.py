from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from b1_motor.mps import ry, rz

B12_N_QUBITS = 64
B12_LAYERS = 3
B12_PARAMETERS_PER_QUBIT_PER_LAYER = 2
B12_PARAMETER_COUNT = (
    B12_N_QUBITS * B12_LAYERS * B12_PARAMETERS_PER_QUBIT_PER_LAYER
)


@dataclass(frozen=True)
class SymmetricVQEAnsatz:
    """Contract-only B1.2 ansatz descriptor.

    Gate application is intentionally not implemented here. The B1.2 manifest
    does not yet specify the exact CX placement/order/orientation, so this class
    validates only the sealed RY/RZ parameter contract.
    """

    n_qubits: int = B12_N_QUBITS
    layers: int = B12_LAYERS

    def __post_init__(self) -> None:
        if self.n_qubits != B12_N_QUBITS:
            raise ValueError("B1.2 ansatz requires exactly 64 logical qubits")
        if self.layers != B12_LAYERS:
            raise ValueError("B1.2 ansatz requires exactly 3 rotation layers")

    @property
    def parameter_count(self) -> int:
        return (
            self.n_qubits
            * self.layers
            * B12_PARAMETERS_PER_QUBIT_PER_LAYER
        )

    @staticmethod
    def gate_names() -> tuple[str, str]:
        return ("RY", "RZ")

    @staticmethod
    def parameter_index(layer: int, qubit: int, gate: str) -> int:
        if not 0 <= layer < B12_LAYERS:
            raise IndexError("layer must satisfy 0 <= layer < 3")
        if not 0 <= qubit < B12_N_QUBITS:
            raise IndexError("qubit must satisfy 0 <= qubit < 64")
        if gate not in {"RY", "RZ"}:
            raise ValueError("gate must be RY or RZ")
        offset = (layer * B12_N_QUBITS + qubit) * 2
        return offset if gate == "RY" else offset + 1

    def initial_parameters(self, seed: int) -> np.ndarray:
        """Return deterministic parameters from an explicitly supplied seed."""
        if not isinstance(seed, (int, np.integer)):
            raise TypeError("seed must be an integer")
        rng = np.random.default_rng(int(seed))
        return rng.uniform(
            -np.pi,
            np.pi,
            size=self.parameter_count,
        ).astype(np.float64)

    @staticmethod
    def rotation_matrix(gate: str, theta: float) -> np.ndarray:
        if gate == "RY":
            return ry(theta)
        if gate == "RZ":
            return rz(theta)
        raise ValueError("gate must be RY or RZ")
