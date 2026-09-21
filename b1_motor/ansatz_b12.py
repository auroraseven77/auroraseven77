from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from b1_motor.mps import MPS, cnot, ry, rz

B12_N_QUBITS = 64
B12_LAYERS = 3
B12_PARAMETERS_PER_QUBIT_PER_LAYER = 2
B12_PARAMETER_COUNT = (
    B12_N_QUBITS * B12_LAYERS * B12_PARAMETERS_PER_QUBIT_PER_LAYER
)


@dataclass(frozen=True)
class AnsatzExecutionReport:
    n_qubits: int
    layers: int
    cx_count: int
    max_bond_dimension: int
    total_discarded_weight_squared: float
    truncations: int


@dataclass(frozen=True)
class SymmetricVQEAnsatz:
    """B1.2 RY/RZ + linear-CX MPS ansatz.

    Each layer applies RY(q), then RZ(q), for every logical qubit, followed
    by CX(q, q+1) for q=0..N-2. The implementation returns a fresh MPS and
    never mutates a caller-supplied state.
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
        return self.n_qubits * self.layers * B12_PARAMETERS_PER_QUBIT_PER_LAYER

    @property
    def is_b12(self) -> bool:
        return self.n_qubits == B12_N_QUBITS and self.layers == B12_LAYERS

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
            raise IndexError(f"layer must satisfy 0 <= layer < {self.layers}")
        if not 0 <= qubit < self.n_qubits:
            raise IndexError(f"qubit must satisfy 0 <= qubit < {self.n_qubits}")
        if gate not in {"RY", "RZ"}:
            raise ValueError("gate must be RY or RZ")
        offset = (layer * self.n_qubits + qubit) * 2
        return offset if gate == "RY" else offset + 1

    def initial_parameters(self, seed: int) -> np.ndarray:
        """Return deterministic parameters from an explicitly supplied seed."""
        if not isinstance(seed, (int, np.integer)):
            raise TypeError("seed must be an integer")
        rng = np.random.default_rng(int(seed))
        return rng.uniform(-np.pi, np.pi, size=self.parameter_count).astype(np.float64)

    @staticmethod
    def rotation_matrix(gate: str, theta: float) -> np.ndarray:
        if gate == "RY":
            return ry(theta)
        if gate == "RZ":
            return rz(theta)
        raise ValueError("gate must be RY or RZ")

    def _validate_parameters(self, params) -> np.ndarray:
        values = np.asarray(params, dtype=np.float64)
        if values.ndim != 1 or values.size != self.parameter_count:
            raise ValueError(
                f"expected {self.parameter_count} parameters, received "
                f"{values.size if values.ndim == 1 else 'non-1D input'}"
            )
        if not np.all(np.isfinite(values)):
            raise ValueError("parameters must contain only finite values")
        return values

    def _prepare_state(self, bond_dim: int, state: MPS | None) -> MPS:
        if state is None:
            return MPS(self.n_qubits, bond_dim=bond_dim)
        if not isinstance(state, MPS):
            raise TypeError("state must be an MPS instance")
        if state.n_qubits != self.n_qubits:
            raise ValueError("state.n_qubits must match ansatz.n_qubits")
        if state.bond_dim != bond_dim:
            raise ValueError("state.bond_dim must match bond_dim")
        prepared = MPS(self.n_qubits, bond_dim=bond_dim)
        prepared.tensors = [tensor.copy() for tensor in state.tensors]
        prepared.validate_structure()
        return prepared

    def apply_with_report(
        self,
        params,
        *,
        bond_dim: int = 128,
        state: MPS | None = None,
    ) -> tuple[MPS, AnsatzExecutionReport]:
        values = self._validate_parameters(params)
        if not isinstance(bond_dim, (int, np.integer)):
            raise TypeError("bond_dim must be an integer")

        prepared = self._prepare_state(int(bond_dim), state)
        cx = cnot()
        total_discarded = 0.0
        truncations = 0
        cx_count = 0

        for layer in range(self.layers):
            for qubit in range(self.n_qubits):
                ry_index = self.parameter_index(layer, qubit, "RY")
                rz_index = self.parameter_index(layer, qubit, "RZ")
                prepared.apply_local_rotation(qubit, ry(values[ry_index]))
                prepared.apply_local_rotation(qubit, rz(values[rz_index]))

            for control, target in self.cx_pairs:
                report = prepared.apply_two_qubit_gate(control, cx)
                total_discarded += report["discarded_weight_squared"]
                truncations += int(report["truncated"])
                cx_count += 1

        prepared.validate_structure()
        return prepared, AnsatzExecutionReport(
            n_qubits=self.n_qubits,
            layers=self.layers,
            cx_count=cx_count,
            max_bond_dimension=prepared.max_bond_dimension,
            total_discarded_weight_squared=float(total_discarded),
            truncations=truncations,
        )

    def apply(
        self,
        params,
        *,
        bond_dim: int = 128,
        state: MPS | None = None,
    ) -> MPS:
        """Prepare the ansatz state on MPS without dense statevector materialization."""
        prepared, _ = self.apply_with_report(
            params,
            bond_dim=bond_dim,
            state=state,
        )
        return prepared
