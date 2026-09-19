import yaml
import json
import hashlib
import sys

def verify_pre_execution_integrity():
    print("=== INICIANDO AUDITORIA PRÉ-EXECUÇÃO (P3) ===")

    try:
        with open("B1_INTEGRITY_ENVELOPE.yaml", "r") as f:
            envelope = yaml.safe_load(f)

        sealed_h_pre = envelope["integrity_anchors"]["H_pre"]
        print(f"[OK] Envelope carregado. H_pre selado: {sealed_h_pre}")
    except Exception as e:
        print(f"[FALHA] Não foi possível ler o envelope: {e}")
        sys.exit(1)

    try:
        with open("MANIFEST_B1.yaml", "r") as f:
            manifest_p0 = yaml.safe_load(f)

        print("[OK] Manifesto P0 carregado do disco.")
    except Exception as e:
        print(f"[FALHA] Não foi possível ler o manifesto: {e}")
        sys.exit(1)

    p1_canonical = json.dumps(
        manifest_p0,
        sort_keys=True,
        separators=(",", ":")
    )

    computed_h_pre = hashlib.sha256(
        p1_canonical.encode("utf-8")
    ).hexdigest()

    print(f"[OK] H_pre recomputado: {computed_h_pre}")

    if sealed_h_pre == computed_h_pre:
        print("\n=== VEREDITO: INTEGRIDADE CONFIRMADA ===")
        print("O manifesto em disco corresponde ao H_pre selado no envelope.")
        print("A barreira causal P3 está intacta.")
        print("Status: PRONTO PARA P4 (Execução).")
        sys.exit(0)
    else:
        print("\n=== VEREDITO: VIOLAÇÃO DE INTEGRIDADE ===")
        print("O manifesto em disco foi alterado ou o envelope está corrompido.")
        sys.exit(1)

if __name__ == "__main__":
    verify_pre_execution_integrity()
