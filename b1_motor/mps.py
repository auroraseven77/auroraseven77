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


# ==============================================================================
# GERADORES DE PORTAS DE DOIS QUBITS (P2.7-B)
# ==============================================================================

def cnot() -> np.ndarray:
    """Return the CNOT unitary in |00>, |01>, |10>, |11> order."""
    return np.array(
        [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0],
        ],
        dtype=np.complex128,
    )


def zz(theta: float) -> np.ndarray:
    """Return ZZ(theta) = exp(-i theta/2 Z tensor Z)."""
    return np.diag(
        [
            np.exp(-1j * theta / 2.0),
            np.exp(1j * theta / 2.0),
            np.exp(1j * theta / 2.0),
            np.exp(-1j * theta / 2.0),
        ]
    ).astype(np.complex128)


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

    def apply_local_rotation(
        self,
        qubit_idx: int,
        U: np.ndarray,
    ) -> None:
        """Apply a validated single-qubit unitary to one MPS tensor.

        This operation is strictly local: it changes only the physical
        index and preserves both virtual bond dimensions. No SVD or
        truncation is performed.
        """
        if not isinstance(qubit_idx, (int, np.integer)):
            raise TypeError("qubit_idx must be an integer")

        if not 0 <= qubit_idx < self.n_qubits:
            raise IndexError(
                f"qubit_idx must satisfy 0 <= qubit_idx < {self.n_qubits}"
            )

        U = np.asarray(U)

        if U.shape != (self.physical_dim, self.physical_dim):
            raise ValueError(
                f"U must have shape "
                f"({self.physical_dim}, {self.physical_dim})"
            )

        if not np.issubdtype(U.dtype, np.number):
            raise TypeError("U must contain numeric values")

        if not np.all(np.isfinite(U)):
            raise ValueError("U must contain only finite values")

        identity = np.eye(self.physical_dim, dtype=np.complex128)

        if not np.allclose(
            U.conj().T @ U,
            identity,
            rtol=0.0,
            atol=1e-12,
        ):
            raise ValueError("U must be unitary")

        tensor = self.tensors[qubit_idx]

        self.tensors[qubit_idx] = np.einsum(
            "ab,lbr->lar",
            U,
            tensor,
            optimize=True,
        )

    def apply_two_qubit_gate(
        self,
        qubit_idx: int,
        U: np.ndarray,
    ) -> dict:
        """Apply a validated nearest-neighbor two-qubit unitary locally."""

        if not isinstance(qubit_idx, (int, np.integer)):
            raise TypeError(
                f"qubit_idx deve ser inteiro, recebido {type(qubit_idx)}"
            )

        if qubit_idx < 0 or qubit_idx >= self.n_qubits - 1:
            raise IndexError(
                "qubit_idx must satisfy "
                f"0 <= qubit_idx < {self.n_qubits - 1}, "
                f"recebido {qubit_idx}"
            )

        if not isinstance(U, np.ndarray):
            raise TypeError(
                f"U deve ser np.ndarray, recebido {type(U)}"
            )

        if U.dtype != np.complex128:
            raise TypeError(
                "U.dtype deve ser estritamente complex128, "
                f"recebido {U.dtype}"
            )

        if U.shape != (4, 4):
            raise ValueError(
                f"U must have shape (4, 4), recebido {U.shape}"
            )

        if not np.all(np.isfinite(U)):
            raise ValueError("U deve conter apenas valores finitos")

        identity = np.eye(4, dtype=np.complex128)

        if not np.allclose(
            U.conj().T @ U,
            identity,
            rtol=0.0,
            atol=1e-14,
        ):
            raise ValueError(
                "U must be unitary (|U^dag U - I| <= 1e-14)"
            )

        A1 = self.tensors[qubit_idx]
        A2 = self.tensors[qubit_idx + 1]

        chi_L, _, chi_M = A1.shape
        _, _, chi_R = A2.shape

        Theta = np.tensordot(
            A1,
            A2,
            axes=([2], [0]),
        )

        U_tensor = U.reshape(2, 2, 2, 2)

        Theta_prime = np.einsum(
            "ijkl,aklb->aijb",
            U_tensor,
            Theta,
        )

        Theta_mat = Theta_prime.reshape(
            chi_L * 2,
            2 * chi_R,
        )

        U_svd, S, Vh = np.linalg.svd(
            Theta_mat,
            full_matrices=False,
        )

        chi_max = self.bond_dim
        epsilon_trunc = 1.0e-8

        valid_sv_count = int(
            np.sum(S >= epsilon_trunc)
        )

        k = max(
            1,
            min(
                chi_max,
                valid_sv_count,
            ),
        )

        discarded_S = S[k:]

        discarded_weight_squared = float(
            np.sum(discarded_S ** 2)
        )

        L_abs = float(
            np.sqrt(discarded_weight_squared)
        )

        truncated = len(discarded_S) > 0

        U_k = U_svd[:, :k]
        S_k = S[:k]
        Vh_k = Vh[:k, :]

        A1_new = U_k.reshape(
            chi_L,
            2,
            k,
        )

        A2_new = (
            S_k[:, None] * Vh_k
        ).reshape(
            k,
            2,
            chi_R,
        )

        self.tensors[qubit_idx] = A1_new
        self.tensors[qubit_idx + 1] = A2_new

        return {
            "chi_actual": int(k),
            "discarded_weight_squared": discarded_weight_squared,
            "L_abs": L_abs,
            "truncated": truncated,
        }

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


def rx(theta: float) -> np.ndarray:
    """Return the single-qubit Rx(theta) unitary in complex128."""
    c = np.cos(theta / 2.0)
    s = np.sin(theta / 2.0)
    return np.array(
        [
            [c, -1j * s],
            [-1j * s, c],
        ],
        dtype=np.complex128,
    )


def ry(theta: float) -> np.ndarray:
    """Return the single-qubit Ry(theta) unitary in complex128."""
    c = np.cos(theta / 2.0)
    s = np.sin(theta / 2.0)
    return np.array(
        [
            [c, -s],
            [s, c],
        ],
        dtype=np.complex128,
    )


def rz(theta: float) -> np.ndarray:
    """Return the single-qubit Rz(theta) unitary in complex128."""
    return np.array(
        [
            [np.exp(-1j * theta / 2.0), 0.0],
            [0.0, np.exp(1j * theta / 2.0)],
        ],
        dtype=np.complex128,
    )
