import pytest
import numpy as np
import math

from b1_motor.boundary import apply_boundary_schmidt, deterministic_tensor_hash
from b1_motor.types import BoundaryID

def test_boundary_metadata_and_hashes():
    """Garante que orientação (Agentes/Qubits) e hashes raw entram no relatório."""
    t_left = np.random.rand(4, 2, 8) + 1j * np.random.rand(4, 2, 8)
    t_right = np.random.rand(8, 2, 4) + 1j * np.random.rand(8, 2, 4)
    
    _, _, report = apply_boundary_schmidt(t_left, t_right, boundary_id=BoundaryID.AH, chi_max=5)
    
    assert report.boundary_id == BoundaryID.AH
    assert report.agent_left_id == "ARGOS"
    assert report.qubit_left_id == 21
    assert report.agent_right_id == "HEPHAESTUS"
    assert report.qubit_right_id == 22
    
    assert report.hash_tensor_left_in == deterministic_tensor_hash(t_left)
    assert report.hash_tensor_right_in == deterministic_tensor_hash(t_right)


def test_boundary_physics_conservation():
    """
    Teste permanente de conservação de probabilidade e norma de reconstrução.
    Valida a identidade: ||Theta_after||^2 = 1 - w_discarded.
    """
    # Tensor espesso (dim=20) forçará truncamento pesado
    t_left = np.random.rand(10, 2, 20) + 1j * np.random.rand(10, 2, 20)
    t_right = np.random.rand(20, 2, 10) + 1j * np.random.rand(20, 2, 10)
    
    chi_max = 5
    new_left, new_right, report = apply_boundary_schmidt(t_left, t_right, boundary_id=BoundaryID.HE, chi_max=chi_max)
    
    assert report.truncation_applied is True
    
    # 1. Recupera espectros
    w_disc = report.discarded_weight_loss
    w_kept = sum(s**2 for s in report.singular_values_kept)
    
    # 2. Conservação da probabilidade normalizada
    assert math.isclose(w_kept + w_disc, 1.0, abs_tol=1e-14)
    
    # 3. Identidade da Norma de Reconstrução
    theta_after = np.tensordot(new_left, new_right, axes=([-1], [0]))
    norm_after = float(np.linalg.norm(theta_after))
    expected_norm = math.sqrt(1.0 - w_disc)
    
    assert math.isclose(norm_after, expected_norm, abs_tol=1e-14)
