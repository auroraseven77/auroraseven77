import numpy as np
import pytest

from b1_motor.mps import MPS, cnot, rx, zz


# ==============================================================================
# GRUPO 1: GERADORES 2-QUBIT (CNOT, ZZ)
# ==============================================================================

def test_cnot_generator_matrix_contract():
    """Matriz CNOT deve ser 4x4 complex128 e unitária na ordem |00>,|01>,|10>,|11>."""
    U = cnot()
    assert U.shape == (4, 4)
    assert U.dtype == np.complex128

    identity = np.eye(4, dtype=np.complex128)
    np.testing.assert_allclose(U.conj().T @ U, identity, atol=1e-14)

    expected = np.array([
        [1, 0, 0, 0],
        [0, 1, 0, 0],
        [0, 0, 0, 1],
        [0, 0, 1, 0],
    ], dtype=np.complex128)
    np.testing.assert_array_equal(U, expected)


@pytest.mark.parametrize("theta", [0.0, np.pi / 4, np.pi / 2, np.pi])
def test_zz_generator_matrix_contract(theta):
    """Matriz ZZ(theta) deve ser diag(exp(-i th/2), exp(+i th/2), exp(+i th/2), exp(-i th/2))."""
    U = zz(theta)
    assert U.shape == (4, 4)
    assert U.dtype == np.complex128

    identity = np.eye(4, dtype=np.complex128)
    np.testing.assert_allclose(U.conj().T @ U, identity, atol=1e-14)

    diag_expected = np.array([
        np.exp(-1j * theta / 2.0),
        np.exp(1j * theta / 2.0),
        np.exp(1j * theta / 2.0),
        np.exp(-1j * theta / 2.0),
    ], dtype=np.complex128)
    np.testing.assert_allclose(np.diag(U), diag_expected, atol=1e-14)


# ==============================================================================
# GRUPO 2: EVOLUÇÃO E ISOLAMENTO LOCAL (N=64)
# ==============================================================================

def test_apply_two_qubit_gate_n64_isolation_and_cnot_bell():
    """
    P2.7-B:
    Aplica Rx(pi/2) no q0, depois CNOT em (q0, q1) em N=64.
    Mede a formação do estado de Bell (|00> + -i|11>)/sqrt(2) em q0,q1
    e garante isolamento absoluto dos tensores q2..q63.
    """
    n_qubits = 64
    mps = MPS(n_qubits=n_qubits, bond_dim=128)

    mps.apply_local_rotation(0, rx(np.pi / 2))

    original_tensors = [t.copy() for t in mps.tensors]

    report = mps.apply_two_qubit_gate(0, cnot())

    assert not np.array_equal(mps.tensors[0], original_tensors[0])
    assert not np.array_equal(mps.tensors[1], original_tensors[1])

    for q in range(2, n_qubits):
        assert np.array_equal(
            mps.tensors[q], original_tensors[q]
        ), f"Vazamento detectado no qubit {q}"

    assert mps.tensors[0].shape[2] == 2
    assert mps.tensors[1].shape[0] == 2
    assert report["chi_actual"] == 2
    assert report["truncated"] is False


# ==============================================================================
# GRUPO 3: GUARDRAILS E REJEIÇÃO DE CONTRATO
# ==============================================================================

def test_apply_two_qubit_gate_rejection_contract():
    """Valida rejeição de índices inválidos, shapes e não-unitariedade."""
    mps = MPS(n_qubits=4, bond_dim=8)
    valid_u = cnot()

    with pytest.raises(IndexError, match="qubit_idx must satisfy"):
        mps.apply_two_qubit_gate(3, valid_u)

    with pytest.raises(IndexError, match="qubit_idx must satisfy"):
        mps.apply_two_qubit_gate(-1, valid_u)

    with pytest.raises(ValueError, match=r"U must have shape \(4, 4\)"):
        mps.apply_two_qubit_gate(0, np.eye(2, dtype=np.complex128))

    non_unitary = np.eye(4, dtype=np.complex128)
    non_unitary[0, 0] = 2.0
    with pytest.raises(ValueError, match="U must be unitary"):
        mps.apply_two_qubit_gate(0, non_unitary)


# ==========================================================================
# GRUPO 4: ZZ E CONSERVAÇÃO DE NORMA
# ==========================================================================

def _two_qubit_state_norm(mps):
    """Calcula a norma por contração tensorial para N=2, sem vetor denso."""
    assert mps.n_qubits == 2
    a0 = mps.tensors[0]
    a1 = mps.tensors[1]

    theta = np.tensordot(a0, a1, axes=([2], [0]))
    return float(np.sqrt(np.sum(np.abs(theta) ** 2)))


@pytest.mark.parametrize("theta", [0.0, np.pi / 7, np.pi / 2, np.pi])
def test_zz_preserves_norm(theta):
    """ZZ é unitária; em N=2 a norma tensorial deve ser preservada."""
    mps = MPS(n_qubits=2, bond_dim=4)

    mps.apply_local_rotation(0, rx(np.pi / 3))
    mps.apply_local_rotation(1, rx(np.pi / 5))

    norm_before = _two_qubit_state_norm(mps)

    report = mps.apply_two_qubit_gate(0, zz(theta))

    norm_after = _two_qubit_state_norm(mps)

    assert norm_before == pytest.approx(1.0, abs=1e-12)
    assert norm_after == pytest.approx(norm_before, abs=1e-12)
    assert isinstance(report["truncated"], bool)
    assert report["discarded_weight_squared"] == pytest.approx(0.0, abs=1e-24)
    assert report["L_abs"] == pytest.approx(0.0, abs=1e-12)


# ==========================================================================
# GRUPO 5: UNITÁRIA ARBITRÁRIA 4x4
# ==========================================================================

def _deterministic_unitary_4x4():
    """Constrói uma unitária 4x4 determinística via QR."""
    rng = np.random.default_rng(20260920)
    z = (
        rng.normal(size=(4, 4))
        + 1j * rng.normal(size=(4, 4))
    ).astype(np.complex128)

    q, r = np.linalg.qr(z)

    phases = np.diag(r)
    phases = np.where(
        np.abs(phases) > 0,
        phases / np.abs(phases),
        1.0,
    )

    return (q * phases.conj()).astype(np.complex128)


def test_apply_two_qubit_gate_accepts_arbitrary_valid_unitary():
    """Uma unitária 4x4 válida deve passar pelo contrato genérico."""
    U = _deterministic_unitary_4x4()

    identity = np.eye(4, dtype=np.complex128)
    np.testing.assert_allclose(
        U.conj().T @ U,
        identity,
        rtol=0.0,
        atol=1e-14,
    )

    mps = MPS(n_qubits=2, bond_dim=4)
    report = mps.apply_two_qubit_gate(0, U)

    assert isinstance(report, dict)
    assert report["chi_actual"] >= 1
    assert report["chi_actual"] <= mps.bond_dim
    assert report["discarded_weight_squared"] >= 0.0
    assert report["L_abs"] >= 0.0


# ==========================================================================
# GRUPO 6: REJEIÇÕES ADICIONAIS
# ==========================================================================

def test_apply_two_qubit_gate_rejects_invalid_types_and_values():
    """Valida tipo de índice, dtype, finitude e dimensão da entrada."""
    mps = MPS(n_qubits=4, bond_dim=8)

    with pytest.raises(TypeError, match="qubit_idx"):
        mps.apply_two_qubit_gate("0", cnot())

    with pytest.raises(TypeError, match="np.ndarray"):
        mps.apply_two_qubit_gate(0, [[1, 0, 0, 0]] * 4)

    with pytest.raises(TypeError, match="complex128"):
        mps.apply_two_qubit_gate(
            0,
            np.eye(4, dtype=np.complex64),
        )

    non_finite = cnot().copy()
    non_finite[0, 0] = np.nan

    with pytest.raises(ValueError, match="finit"):
        mps.apply_two_qubit_gate(0, non_finite)


# ==========================================================================
# GRUPO 7: ISOLAMENTO ABSOLUTO DOS TENSORES
# ==========================================================================

def test_two_qubit_gate_changes_only_target_pair():
    """Somente os dois tensores do par alvo podem sofrer mutação."""
    mps = MPS(n_qubits=8, bond_dim=8)

    mps.apply_local_rotation(3, rx(np.pi / 2))
    original_tensors = [tensor.copy() for tensor in mps.tensors]

    mps.apply_two_qubit_gate(3, cnot())

    for q, (before, after) in enumerate(
        zip(original_tensors, mps.tensors)
    ):
        if q not in (3, 4):
            assert np.array_equal(before, after), (
                f"Tensor fora do par alvo foi alterado: q={q}"
            )

    assert not np.array_equal(original_tensors[3], mps.tensors[3])
    assert not np.array_equal(original_tensors[4], mps.tensors[4])


# ==========================================================================
# GRUPO 8: TRUNCAMENTO E CONTRATO DO REPORT
# ==========================================================================

def test_truncation_report_matches_discarded_singular_weight():
    """
    Com bond_dim=1, o estado Bell exige rank 2 e força truncamento.
    O peso descartado deve ser 1/2 e L_abs=sqrt(1/2).
    """
    mps = MPS(n_qubits=2, bond_dim=1)

    mps.apply_local_rotation(0, rx(np.pi / 2))
    report = mps.apply_two_qubit_gate(0, cnot())

    assert set(report) == {
        "chi_actual",
        "discarded_weight_squared",
        "L_abs",
        "truncated",
    }

    assert report["chi_actual"] == 1
    assert report["chi_actual"] <= mps.bond_dim
    assert report["truncated"] is True

    expected_discarded_weight_squared = 0.5
    expected_l_abs = np.sqrt(expected_discarded_weight_squared)

    assert report["discarded_weight_squared"] == pytest.approx(
        expected_discarded_weight_squared,
        abs=1e-12,
    )
    assert report["L_abs"] == pytest.approx(
        expected_l_abs,
        abs=1e-12,
    )


# ==========================================================================
# GRUPO 9: DETERMINISMO
# ==========================================================================

def test_two_qubit_gate_is_deterministic():
    """Mesma entrada e mesmo ambiente devem produzir o mesmo resultado."""
    mps_a = MPS(n_qubits=4, bond_dim=8)
    mps_b = MPS(n_qubits=4, bond_dim=8)

    rotation = rx(np.pi / 2)
    gate = cnot()

    mps_a.apply_local_rotation(0, rotation)
    mps_b.apply_local_rotation(0, rotation)

    report_a = mps_a.apply_two_qubit_gate(0, gate)
    report_b = mps_b.apply_two_qubit_gate(0, gate)

    assert report_a["chi_actual"] == report_b["chi_actual"]
    assert report_a["truncated"] == report_b["truncated"]

    assert report_a["discarded_weight_squared"] == pytest.approx(
        report_b["discarded_weight_squared"],
        abs=1e-15,
    )
    assert report_a["L_abs"] == pytest.approx(
        report_b["L_abs"],
        abs=1e-15,
    )

    assert len(mps_a.tensors) == len(mps_b.tensors)

    for tensor_a, tensor_b in zip(mps_a.tensors, mps_b.tensors):
        np.testing.assert_allclose(
            tensor_a,
            tensor_b,
            rtol=0.0,
            atol=1e-14,
        )


# ==========================================================================
# GRUPO 10: N=64 TENSORIAL / ANTI-DENSE
# ==========================================================================

def test_n64_two_qubit_gate_remains_tensorial_and_global_vector_forbidden():
    """N=64 deve permanecer representado exclusivamente pelos tensores MPS."""
    mps = MPS(n_qubits=64, bond_dim=128)

    assert len(mps.tensors) == 64

    report = mps.apply_two_qubit_gate(10, zz(np.pi / 3))

    assert report["chi_actual"] == 1
    assert isinstance(report["truncated"], bool)
    assert report["discarded_weight_squared"] == pytest.approx(
        0.0,
        abs=1e-24,
    )
    assert report["L_abs"] == pytest.approx(0.0, abs=1e-12)

    for tensor in mps.tensors:
        assert tensor.ndim == 3
        assert tensor.shape[1] == 2

    with pytest.raises(RuntimeError, match="ANTI-DENSE"):
        mps.to_global_state_vector()
