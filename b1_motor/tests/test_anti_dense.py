import pytest
from b1_motor.mps import MPS
from b1_motor.types import CHI_MAX, LOGICAL_QUBITS_MAX

def test_mps_max_parameter_bound_vs_dense():
    """
    Prova que, no pior cenário, o MPS atinge um número de parâmetros 
    incomensuravelmente menor que o vetor de estado denso 2^N.
    """
    n = LOGICAL_QUBITS_MAX
    d = 2
    chi = CHI_MAX
    
    # Parâmetros máximos teóricos para um estado MPS com bordas abertas
    # N * d * chi^2
    theoretical_max_params = n * d * (chi ** 2)
    
    # Validando o teto esperado (64 * 2 * 128^2 = 2.097.152 amplitudes)
    assert theoretical_max_params == 2_097_152
    
    # Construindo o motor e validando que ele respeita a barreira
    mps = MPS(n_qubits=n, bond_dim=chi)
    
    assert mps.structural_parameter_count <= theoretical_max_params
    
    # 2^64 é a dimensão do vetor denso puro.
    # O Python lida com inteiros arbitrariamente grandes.
    dense_vector_size = 2 ** n
    assert theoretical_max_params < (dense_vector_size // 1_000_000), "MPS must remain highly compressed"

def test_explicit_anti_dense_lock():
    """
    Garante que a tentativa de extrair o vetor global estoure a trava imediatamente.
    """
    # 64 qubits > limite interno de 15
    mps = MPS(n_qubits=64)
    
    with pytest.raises(RuntimeError) as exc_info:
        mps.to_global_state_vector()
        
    assert "ANTI-DENSE VIOLATION" in str(exc_info.value)

def test_small_system_dense_allowed_but_not_implemented():
    """
    Para sistemas de depuração muito pequenos (ex: N=4), 
    o erro é de NotImplemented, não de violação estrutural.
    """
    mps = MPS(n_qubits=4)
    
    with pytest.raises(NotImplementedError):
        mps.to_global_state_vector()
