def get_expectation_zz(state, q1, q2):
    mask1 = 1 << (7 - q1)
    mask2 = 1 << (7 - q2)
    exp_val = 0.0 + 0.0j
    for i in range(256):
        prob = state[i].real**2 + state[i].imag**2
        b1 = (i & mask1) != 0
        b2 = (i & mask2) != 0
        if b1 == b2:
            exp_val += prob
        else:
            exp_val -= prob
    return exp_val

def get_expectation_x(state, q):
    mask = 1 << (7 - q)
    exp_val = 0.0 + 0.0j
    for i in range(256):
        if not (i & mask):
            i_flipped = i | mask
            exp_val += state[i].conjugate() * state[i_flipped]
            exp_val += state[i_flipped].conjugate() * state[i]
    return exp_val

def measure_energy(state):
    energy = 0.0 + 0.0j
    
    # Ordem estrita de acumulação ZZ (0 a 6)
    for i in range(7):
        energy -= get_expectation_zz(state, i, i + 1)
        
    # Ordem estrita de acumulação X (0 a 7)
    for i in range(8):
        energy -= get_expectation_x(state, i)
        
    # Política rigorosa de validação imaginária (limite: 1.0e-12)
    if abs(energy.imag) > 1.0e-12:
        raise ValueError(f"Falha de integridade: componente imaginária {energy.imag} excede a tolerância.")
        
    return energy.real
