import numpy as np
import pytest

from b1_motor.mps import MPS, rx, ry, rz


@pytest.mark.parametrize("gen", [rx, ry, rz])
@pytest.mark.parametrize(
    "theta",
    [0.0, np.pi / 4, np.pi / 2, np.pi, 2 * np.pi],
)
def test_generators_properties(gen, theta):
    U = gen(theta)

    assert U.shape == (2, 2)
    assert U.dtype == np.complex128

    identity = np.eye(2, dtype=np.complex128)

    assert np.allclose(
        U.conj().T @ U,
        identity,
        rtol=0.0,
        atol=1e-14,
    )


def test_apply_local_rotation_n64_target_isolation():
    n_qubits = 64
    target_qubit = 7

    mps = MPS(
        n_qubits=n_qubits,
        bond_dim=128,
    )

    original_tensors = [
        tensor.copy()
        for tensor in mps.tensors
    ]

    original_shapes = [
        tensor.shape
        for tensor in mps.tensors
    ]

    mps.apply_local_rotation(
        target_qubit,
        rx(np.pi / 2),
    )

    for q in range(n_qubits):
        if q == target_qubit:
            assert not np.array_equal(
                mps.tensors[q],
                original_tensors[q],
            )
        else:
            assert np.array_equal(
                mps.tensors[q],
                original_tensors[q],
            ), f"Vazamento detectado: tensor {q} foi alterado."

    assert [
        tensor.shape
        for tensor in mps.tensors
    ] == original_shapes

    assert all(
        tensor.shape == (1, 2, 1)
        for tensor in mps.tensors
    )

    assert mps.max_bond_dimension == 1

    target_tensor = mps.tensors[target_qubit]

    expected_state = np.array(
        [
            1.0 / np.sqrt(2.0),
            -1j / np.sqrt(2.0),
        ],
        dtype=np.complex128,
    )

    np.testing.assert_allclose(
        target_tensor[0, :, 0],
        expected_state,
        rtol=0.0,
        atol=1e-14,
    )

    norm_sq = np.vdot(
        target_tensor,
        target_tensor,
    ).real

    np.testing.assert_allclose(
        norm_sq,
        1.0,
        rtol=0.0,
        atol=1e-14,
    )


def test_apply_local_rotation_other_generators():
    for gate in (
        ry(np.pi / 2),
        rz(np.pi / 2),
    ):
        mps = MPS(
            n_qubits=4,
            bond_dim=8,
        )

        mps.apply_local_rotation(2, gate)

        assert mps.tensors[2].shape == (1, 2, 1)
        assert mps.max_bond_dimension == 1


def test_apply_local_rotation_rejection_contract():
    mps = MPS(
        n_qubits=64,
        bond_dim=128,
    )

    valid_u = rx(np.pi / 2)

    with pytest.raises(
        IndexError,
        match="qubit_idx must satisfy",
    ):
        mps.apply_local_rotation(-1, valid_u)

    with pytest.raises(
        IndexError,
        match="qubit_idx must satisfy",
    ):
        mps.apply_local_rotation(64, valid_u)

    with pytest.raises(
        TypeError,
        match="qubit_idx must be an integer",
    ):
        mps.apply_local_rotation("7", valid_u)

    with pytest.raises(
        ValueError,
        match=r"U must have shape \(2, 2\)",
    ):
        mps.apply_local_rotation(
            0,
            np.eye(3, dtype=np.complex128),
        )

    with pytest.raises(
        ValueError,
        match=r"U must have shape \(2, 2\)",
    ):
        mps.apply_local_rotation(
            0,
            np.array(
                [1.0, 0.0],
                dtype=np.complex128,
            ),
        )

    nan_matrix = np.array(
        [[np.nan, 0.0], [0.0, 1.0]],
        dtype=np.complex128,
    )

    with pytest.raises(
        ValueError,
        match="U must contain only finite values",
    ):
        mps.apply_local_rotation(0, nan_matrix)

    inf_matrix = np.array(
        [[np.inf, 0.0], [0.0, 1.0]],
        dtype=np.complex128,
    )

    with pytest.raises(
        ValueError,
        match="U must contain only finite values",
    ):
        mps.apply_local_rotation(0, inf_matrix)

    non_unitary = np.array(
        [[1.5, 0.0], [0.0, 1.0]],
        dtype=np.complex128,
    )

    with pytest.raises(
        ValueError,
        match="U must be unitary",
    ):
        mps.apply_local_rotation(0, non_unitary)
