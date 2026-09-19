import hashlib
import os

def verify_v0_1(
    evidence_file="EVIDENCE_B0_PRIME.yaml",
    log_file="raw_log_b0_prime.json",
):
    print("=== INICIANDO VERIFICAÇÃO CRIPTOGRÁFICA V0.1 ===")

    expected_hash = None

    try:
        with open(evidence_file, "r", encoding="utf-8") as f:
            for line in f:
                if "raw_log_sha256:" in line:
                    expected_hash = (
                        line.split(":", 1)[1]
                        .strip()
                        .strip('"')
                        .strip("'")
                    )
                    break
    except FileNotFoundError:
        print(f"FALHA: Recibo {evidence_file} não encontrado.")
        return

    if not expected_hash:
        print("FALHA: raw_log_sha256 não encontrado no recibo.")
        return

    print(f"[ V0.1.A ] Hash atestado no recibo: {expected_hash}")

    if not os.path.exists(log_file):
        print(
            f"FALHA: Objeto material {log_file} "
            "evaporou ou não foi retido."
        )
        return

    with open(log_file, "rb") as f:
        file_bytes = f.read()

    actual_hash = hashlib.sha256(file_bytes).hexdigest()

    print(f"[ V0.1.B ] Hash físico recalculado:  {actual_hash}")
    print(f"[ V0.1.C ] Massa do artefato lido:   {len(file_bytes)} bytes")

    if expected_hash == actual_hash:
        print(
            "\n=> ESTADO V0.1: APROVADO "
            "(Integridade criptográfica e política de retenção validadas)."
        )
    else:
        print(
            "\n=> ESTADO V0.1: REJEITADO "
            "(Divergência entre o registro e a materialidade)."
        )

if __name__ == "__main__":
    verify_v0_1()
