from .gates import apply_ry, apply_rz, apply_cx

def evaluate_ansatz(params):
    if len(params) != 48:
        raise ValueError(f"Esperados 48 parâmetros, recebidos {len(params)}")
        
    state = [0.0 + 0.0j] * 256
    state[0] = 1.0 + 0.0j
    
    param_idx = 0
    
    for layer in range(3):
        # RY Layer
        for q in range(8):
            state = apply_ry(state, q, params[param_idx])
            param_idx += 1
            
        # RZ Layer
        for q in range(8):
            state = apply_rz(state, q, params[param_idx])
            param_idx += 1
            
        # Linear Entanglement Layer (CX) - Apenas para layer 0 e 1 (Profundidade Entanglement = 2)
        if layer < 2: 
            for q in range(7):
                state = apply_cx(state, q, q + 1)
                
    return state
