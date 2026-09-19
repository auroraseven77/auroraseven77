import hashlib
import json


EVIDENCE_FILE = "EVIDENCE_B0_PRIME.yaml"
RAW_LOG_FILE = "raw_log_b0_prime.json"


def extract_yaml_value(path, key):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            prefix = f"{key}:"
            if stripped.startswith(prefix):
                return stripped[len(prefix):].strip().strip('"').strip("'")
    return None


def canonical_experiment_payload(raw):
    # Reconstrução EXATA do payload usado pelo gerador B0'.
    # Não incluir timestamp_utc nem experiment_hash.
    return {
        "backend": raw["backend"],
        "circuit_id": raw["circuit_id"],
        "circuit_execution": raw["circuit_execution"],
        "final_state_vector": raw["final_state_vector"],
        "metric_F_recv": raw["metric_F_recv"],
        "target_state": raw["target_state"],
    }


def verify_v0_2():
    print("=== INICIANDO VERIFICAÇÃO DE IDENTIDADE V0.2 ===")

    expected_hash = extract_yaml_value(
        EVIDENCE_FILE,
        "experiment_hash",
    )

    if not expected_hash:
        print("FALHA: experiment_hash não encontrado no recibo.")
        return False

    print(f"[ V0.2.A ] Hash experimental atestado: {expected_hash}")

    try:
        with open(RAW_LOG_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except FileNotFoundError:
        print(f"FALHA: {RAW_LOG_FILE} não encontrado.")
        return False
    except json.JSONDecodeError as exc:
        print(f"FALHA: JSON inválido: {exc}")
        return False

    required = {
        "backend",
        "circuit_id",
        "circuit_execution",
        "final_state_vector",
        "metric_F_recv",
        "target_state",
        "experiment_hash",
        "timestamp_utc",
    }

    missing = sorted(required - raw.keys())

    if missing:
        print(f"FALHA: campos ausentes no raw log: {missing}")
        return False

    stored_in_log = raw["experiment_hash"]

    print(f"[ V0.2.B ] Hash experimental no raw log: {stored_in_log}")

    payload = canonical_experiment_payload(raw)

    canonical = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
    )

    recomputed_hash = hashlib.sha256(
        canonical.encode("utf-8")
    ).hexdigest()

    print(
        f"[ V0.2.C ] Hash experimental recalculado: {recomputed_hash}"
    )

    internal_match = stored_in_log == recomputed_hash
    receipt_match = expected_hash == recomputed_hash

    print(
        "[ V0.2.D ] "
        f"Raw-log hash == recomputado: "
        f"{'PASS' if internal_match else 'FAIL'}"
    )

    print(
        "[ V0.2.E ] "
        f"Recibo == recomputado: "
        f"{'PASS' if receipt_match else 'FAIL'}"
    )

    if internal_match and receipt_match:
        print(
            "\n=> ESTADO V0.2: APROVADO "
            "(Identidade determinística do experimento reconstruída "
            "independentemente)."
        )
        return True

    print(
        "\n=> ESTADO V0.2: REJEITADO "
        "(A identidade determinística não pôde ser reconstruída)."
    )
    return False


if __name__ == "__main__":
    raise SystemExit(0 if verify_v0_2() else 1)
