"""Independent dense reference for the B1.2 RY/RZ + linear-CX ansatz."""

from __future__ import annotations

import numpy as np


def ry(theta: float) -> np.ndarray:
    c = np.cos(theta / 2.0)
    s = np.sin(theta / 2.0)
    return np.array(
        [[c, -s], [s, c]],
        dtype=np.complex128,
    )


def rz(theta: float) -> np.ndarray:
    return np.array(
        [
            [np.exp(-1j * theta / 2.0), 0.0],
            [0.0, np.exp(1j * theta / 2.0)],
        ],
        dtype=np.complex128,
    )


def cnot() -> np.ndarray:
    return np.array(
        [
            [1, 0, 0, 0],
            [0, 1, 0, 0],
            [0, 0, 0, 1],
            [0, 0, 1, 0],
        ],
        dtype=np.complex128,
    )


def _apply_single_qubit(
    state: np.ndarray,
    gate: np.ndarray,
    qubit: int,
    n_qubits: int,
) -> np.ndarray:
    tensor = state.reshape((2,) * n_qubits)
    tensor = np.moveaxis(tensor, qubit, 0)
    tensor = np.tensordot(gate, tensor, axes=(1, 0))
    tensor = np.moveaxis(tensor, 0, qubit)
    return tensor.reshape(-1)


def _apply_cnot(
    state: np.ndarray,
    control: int,
    target: int,
    n_qubits: int,
) -> np.ndarray:
    tensor = state.reshape((2,) * n_qubits)
    tensor = np.moveaxis(tensor, (control, target), (0, 1))

    original_shape = tensor.shape
    pair = tensor.reshape(4, -1)
    pair = cnot() @ pair

    tensor = pair.reshape(original_shape)
    tensor = np.moveaxis(tensor, (0, 1), (control, target))
    return tensor.reshape(-1)


def prepare_dense_state(
    params: np.ndarray,
    n_qubits: int,
    layers: int = 3,
) -> np.ndarray:
    values = np.asarray(params, dtype=float)

    expected = n_qubits * layers * 2
    if values.ndim != 1:
        raise ValueError("params must be one-dimensional")
    if values.size != expected:
        raise ValueError(
            f"expected {expected} parameters, got {values.size}"
        )
    if not np.all(np.isfinite(values)):
        raise ValueError("params must be finite")

    state = np.zeros(2**n_qubits, dtype=np.complex128)
    state[0] = 1.0

    index = 0

    for _layer in range(layers):
        for qubit in range(n_qubits):
            state = _apply_single_qubit(
                state,
                ry(values[index]),
                qubit,
                n_qubits,
            )
            index += 1

            state = _apply_single_qubit(
                state,
                rz(values[index]),
                qubit,
                n_qubits,
            )
            index += 1

        for control in range(n_qubits - 1):
            state = _apply_cnot(
                state,
                control,
                control + 1,
                n_qubits,
            )

    norm = np.linalg.norm(state)
    if not np.isfinite(norm) or norm == 0.0:
        raise ValueError("invalid dense state norm")

    return state / norm


def energy_from_dense_state(
    state: np.ndarray,
    hamiltonian: np.ndarray,
) -> float:
    value = np.vdot(state, hamiltonian @ state)

    if abs(value.imag) > 1e-10:
        raise ValueError(
            f"dense energy has non-negligible imaginary part: {value.imag}"
        )

    return float(value.real)
