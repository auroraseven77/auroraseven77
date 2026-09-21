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
    """Contract-only RY/RZ ansatz descriptor.

    The B1.2 default is exactly 64 qubits and 3 rotation layers. The class
    also permits N=2/4/6 for contract tests before any N=64 execution.
    Gate application is intentionally absent until the manifest closes the
    exact CX placement/order/orientation.
    """

    n_qubits: int = B12_N_QUBITS
    layers: int = B12_LAYERS

    def __post_init__(self) -> None:
        if not isinstance(self.n_qubits, (int, np.integer)):
            raise TypeError("n_qubits must be an integer")
        if self.n_qubits < 1:
            raise ValueError("n_qubits must be >= 1")
        if self.layers != B12_LAYERS:
            raise ValueError("B1.2 requires exactly 3 rotation layers")

    @property
    def parameter_count(self) -> int:
        return (
            self.n_qubits
            * self.layers
            * B12_PARAMETERS_PER_QUBIT_PER_LAYER
        )

    @property
    def is_b12(self) -> bool:
        return (
            self.n_qubits == B12_N_QUBITS
            and self.layers == B12_LAYERS
        )

    @staticmethod
    def gate_names() -> tuple[str, str]:
        return ("RY", "RZ")

    @property
    def rotation_order(self) -> tuple[str, str]:
        return ("RY", "RZ")

    @property
    def cx_pairs(self) -> tuple[tuple[int, int], ...]:
        return tuple((q, q + 1) for q in range(self.n_qubits - 1))

    @property
    def cx_orientation(self) -> str:
        return "lower_to_higher"

    @property
    def entangler_placement(self) -> str:
        return "after_rotations"

    def parameter_index(self, layer: int, qubit: int, gate: str) -> int:
        if not 0 <= layer < self.layers:
            raise IndexError(
                f"layer must satisfy 0 <= layer < {self.layers}"
            )
        if not 0 <= qubit < self.n_qubits:
            raise IndexError(
                f"qubit must satisfy 0 <= qubit < {self.n_qubits}"
            )
        if gate not in {"RY", "RZ"}:
            raise ValueError("gate must be RY or RZ")
        offset = (layer * self.n_qubits + qubit) * 2
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
