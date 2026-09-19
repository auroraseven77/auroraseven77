import math

def apply_ry(state, qubit, theta):
    cos_t = math.cos(theta / 2.0)
    sin_t = math.sin(theta / 2.0)
    mask = 1 << (7 - qubit)
    new_state = list(state)
    
    for i in range(256):
        if not (i & mask):
            i0 = i
            i1 = i | mask
            a = state[i0]
            b = state[i1]
            new_state[i0] = cos_t * a - sin_t * b
            new_state[i1] = sin_t * a + cos_t * b
            
    return new_state

def apply_rz(state, qubit, theta):
    phase_0 = complex(math.cos(-theta / 2.0), math.sin(-theta / 2.0))
    phase_1 = complex(math.cos(theta / 2.0), math.sin(theta / 2.0))
    mask = 1 << (7 - qubit)
    new_state = list(state)
    
    for i in range(256):
        if not (i & mask):
            new_state[i] *= phase_0
        else:
            new_state[i] *= phase_1
            
    return new_state

def apply_cx(state, control, target):
    c_mask = 1 << (7 - control)
    t_mask = 1 << (7 - target)
    new_state = list(state)
    
    for i in range(256):
        # Processa apenas os índices onde o bit de controle é 1 e o alvo é 0
        # Isso garante que a troca (swap) ocorra exatamente uma vez por par
        if (i & c_mask) and not (i & t_mask):
            i_target_0 = i
            i_target_1 = i | t_mask
            new_state[i_target_0], new_state[i_target_1] = state[i_target_1], state[i_target_0]
            
    return new_state
