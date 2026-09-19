import math

def verify_v0(evidence_file="EVIDENCE_B0.yaml"):
    print("=== INICIANDO VERIFICAÇÃO INDEPENDENTE V0 ===")

    try:
        with open(evidence_file, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        print(f"FALHA: Arquivo {evidence_file} não encontrado.")
        return

    f_recv = None
    amplitudes = []

    in_amplitudes = False

    for line in lines:
        line = line.strip()

        if line.startswith("F_recv:"):
            f_recv = float(line.split(":", 1)[1].strip())

        elif line.startswith("final_state_amplitudes:"):
            in_amplitudes = True

        elif in_amplitudes and line.startswith("- ["):
            val_str = line.replace("- [", "").replace("]", "")
            real_val = float(val_str.split(",")[0].strip())
            amplitudes.append(real_val)

        elif in_amplitudes and not line.startswith("-"):
            if len(amplitudes) == 4:
                in_amplitudes = False

    epsilon = 1e-12
    inv_sqrt2 = 1.0 / math.sqrt(2)
    expected_state = [inv_sqrt2, 0.0, 0.0, inv_sqrt2]

    f_recv_pass = (
        f_recv is not None
        and abs(f_recv - 1.0) < epsilon
    )

    norm_sq = sum(a**2 for a in amplitudes)
    norm_pass = (
        len(amplitudes) == 4
        and abs(norm_sq - 1.0) < epsilon
    )

    state_distance = sum(
        (a - e)**2
        for a, e in zip(amplitudes, expected_state)
    )

    state_pass = (
        len(amplitudes) == 4
        and state_distance < epsilon
    )

    print(
        f"[ V0.1 ] Fidelidade ≈ 1 : "
        f"{'PASS' if f_recv_pass else 'FAIL'} "
        f"(Obtido: {f_recv})"
    )

    print(
        f"[ V0.2 ] ||psi||^2 ≈ 1  : "
        f"{'PASS' if norm_pass else 'FAIL'} "
        f"(Obtido: {norm_sq:.16f})"
    )

    print(
        f"[ V0.3 ] psi == |Phi+>  : "
        f"{'PASS' if state_pass else 'FAIL'} "
        f"(Distância: {state_distance:.16e})"
    )

    if f_recv_pass and norm_pass and state_pass:
        print(
            "\n=> ESTADO V0: APROVADO "
            "(As invariantes matemáticas da evidência B0 são consistentes)."
        )
    else:
        print(
            "\n=> ESTADO V0: REJEITADO "
            "(A evidência B0 viola uma ou mais invariantes matemáticas)."
        )

if __name__ == "__main__":
    verify_v0()
