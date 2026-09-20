from __future__ import annotations
import hashlib
from typing import Tuple
import numpy as np

from b1_motor.types import BoundaryID, BoundaryExchangeReport

def deterministic_tensor_hash(t: np.ndarray) -> str:
    """Gera hash SHA-256 estrito baseado na representação hex de ponto flutuante."""
    h = hashlib.sha256()
    for x in np.nditer(t, order='C'):
        h.update(float(x.real).hex().encode('utf-8'))
        h.update(float(x.imag).hex().encode('utf-8'))
    return h.hexdigest()

def get_boundary_metadata(boundary_id: BoundaryID) -> Tuple[str, str, int, int]:
    """Mapeamento canônico (Agente L, Agente R, Qubit L, Qubit R)."""
    if boundary_id == BoundaryID.AH:
        return ("ARGOS", "HEPHAESTUS", 21, 22)
    elif boundary_id == BoundaryID.HE:
        return ("HEPHAESTUS", "HERMES", 43, 44)
    raise ValueError(f"Unknown BoundaryID: {boundary_id}")

def apply_boundary_schmidt(
    tensor_left: np.ndarray,
    tensor_right: np.ndarray,
    boundary_id: BoundaryID,
    chi_max: int = 128,
) -> Tuple[np.ndarray, np.ndarray, BoundaryExchangeReport]:
    
    if tensor_left.ndim != 3 or tensor_right.ndim != 3:
        raise ValueError("Os tensores de fronteira devem ter rank 3 (D_left, d, D_right).")
        
    D_L, d_L, D_mid_L = tensor_left.shape
    D_mid_R, d_R, D_R = tensor_right.shape
    
    if D_mid_L != D_mid_R:
        raise ValueError(f"Dimensões incompatíveis: {D_mid_L} != {D_mid_R}")

    # Snapshot RAW
    hash_left_in = deterministic_tensor_hash(tensor_left)
    hash_right_in = deterministic_tensor_hash(tensor_right)

    # Contração
    theta = np.tensordot(tensor_left, tensor_right, axes=([-1], [0]))
    matrix = theta.reshape(D_L * d_L, d_R * D_R)
    
    u, s, vh = np.linalg.svd(matrix, full_matrices=False)
    
    # NORMALIZAÇÃO ESTRITA
    norm = float(np.linalg.norm(s))
    if norm > 1e-15:
        s = s / norm
        
    kept = min(len(s), chi_max)
    s_kept = s[:kept]
    s_discarded = s[kept:]
    
    # Perda relativa exata
    discarded_loss = float(np.sum(s_discarded**2))
    
    u_kept = u[:, :kept]
    vh_kept = vh[:kept, :]
    
    vh_absorbed = np.diag(s_kept) @ vh_kept
    
    new_tensor_left = u_kept.reshape(D_L, d_L, kept)
    new_tensor_right = vh_absorbed.reshape(kept, d_R, D_R)
    
    agent_L, agent_R, q_L, q_R = get_boundary_metadata(boundary_id)
    
    report = BoundaryExchangeReport(
        boundary_id=boundary_id,
        agent_left_id=agent_L,
        agent_right_id=agent_R,
        qubit_left_id=q_L,
        qubit_right_id=q_R,
        hash_tensor_left_in=hash_left_in,
        hash_tensor_right_in=hash_right_in,
        effective_bond_dim=kept,
        chi_used=kept,
        singular_values_kept=tuple(float(x) for x in s_kept),
        singular_values_discarded=tuple(float(x) for x in s_discarded),
        truncation_applied=len(s_discarded) > 0,
        discarded_weight_loss=discarded_loss
    )
    
    return new_tensor_left, new_tensor_right, report
