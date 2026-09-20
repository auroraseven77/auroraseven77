from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np

from b1_motor.types import CHI_MAX, LOGICAL_QUBITS_MAX, TruncationReport


@dataclass(frozen=True)
class MPSContract:
    n_qubits: int
    bond_dim: int
    physical_dim: int = 2


class MPS:
    def __init__(self, n_qubits: int, bond_dim: int = CHI_MAX):
        if not 1 <= n_qubits <= LOGICAL_QUBITS_MAX:
            raise ValueError(
                f"n_qubits must satisfy 1 <= n_qubits <= {LOGICAL_QUBITS_MAX}"
            )

        if not 1 <= bond_dim <= CHI_MAX:
            raise ValueError(
                f"bond_dim must satisfy 1 <= bond_dim <= {CHI_MAX}"
            )

        self.contract = MPSContract(
            n_qubits=n_qubits,
            bond_dim=bond_dim,
        )
        self.tensors: List[np.ndarray] = self._zero_product_state()

    def _zero_product_state(self) -> List[np.ndarray]:
        tensors: List[np.ndarray] = []

        for _ in range(self.contract.n_qubits):
            tensor = np.zeros(
                (1, self.contract.physical_dim, 1),
                dtype=np.complex128,
            )
            tensor[0, 0, 0] = 1.0
            tensors.append(tensor)

        return tensors

    @property
    def n_qubits(self) -> int:
        return self.contract.n_qubits

    @property
    def bond_dim(self) -> int:
        return self.contract.bond_dim

    @property
    def physical_dim(self) -> int:
        return self.contract.physical_dim

    @property
    def max_bond_dimension(self) -> int:
        maximum = 0
        for tensor in self.tensors:
            maximum = max(maximum, tensor.shape[0], tensor.shape[-1])
        return maximum

    @property
    def tensor_ranks(self) -> tuple[int, ...]:
        return tuple(tensor.ndim for tensor in self.tensors)

    @property
    def structural_parameter_count(self) -> int:
        return sum(tensor.size for tensor in self.tensors)

    def validate_structure(self) -> None:
        if len(self.tensors) != self.n_qubits:
            raise AssertionError("tensor count does not match n_qubits")

        for index, tensor in enumerate(self.tensors):
            if tensor.ndim != 3:
                raise AssertionError(f"tensor {index} must have rank 3, got {tensor.ndim}")
            if tensor.shape[1] != self.physical_dim:
                raise AssertionError(f"tensor {index} has invalid physical dimension")
            if tensor.shape[0] > self.bond_dim:
                raise AssertionError(f"tensor {index} exceeds left bond dimension")
            if tensor.shape[-1] > self.bond_dim:
                raise AssertionError(f"tensor {index} exceeds right bond dimension")

        if self.max_bond_dimension > self.bond_dim:
            raise AssertionError("bond dimension contract violated")

    def to_global_state_vector(self) -> np.ndarray:
        """
        Trava de segurança arquitetural:
        Impede a materialização acidental de vetores densos grandes.
        """
        dense_limit = 15
        if self.n_qubits > dense_limit:
            raise RuntimeError(
                f"ANTI-DENSE VIOLATION: Refusing to construct state vector for N={self.n_qubits}. "
                f"Global dense representations are strictly forbidden for N > {dense_limit}."
            )
        raise NotImplementedError("State vector contraction is not implemented yet.")


def svd_truncate(
    matrix: np.ndarray,
    chi_max: int,
    *,
    step: int = 0,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, TruncationReport]:
    if not isinstance(matrix, np.ndarray):
        raise TypeError("matrix must be a numpy.ndarray")
    if matrix.ndim != 2:
        raise ValueError("matrix must be two-dimensional")
    if matrix.size == 0:
        raise ValueError("matrix cannot be empty")
    if not np.isfinite(matrix).all():
        raise ValueError("matrix must contain only finite values")
    if not 1 <= chi_max <= CHI_MAX:
        raise ValueError(f"chi_max must satisfy 1 <= chi_max <= {CHI_MAX}")
    if step < 0:
        raise ValueError("step must be >= 0")

    u, singular_values, vh = np.linalg.svd(
        matrix,
        full_matrices=False,
    )

    rank = len(singular_values)
    kept = min(rank, chi_max)
    discarded = singular_values[kept:]
    discarded_weight_loss = float(np.sum(np.abs(discarded) ** 2))

    report = TruncationReport(
        step=step,
        bond_dimension_before=rank,
        bond_dimension_after=kept,
        discarded_weight_loss=discarded_weight_loss,
        chi_max_cap=chi_max,
    )

    return (
        u[:, :kept],
        singular_values[:kept],
        vh[:kept, :],
        report,
    )
