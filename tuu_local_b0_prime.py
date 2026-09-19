import datetime
import hashlib
import json
import math
import os


RAW_LOG = "raw_log_b0_prime.json"


class TUULocalBackend:
    def __init__(self):
        self.state = [
            complex(1, 0),
            complex(0, 0),
            complex(0, 0),
            complex(0, 0),
        ]
        self.log = []

    def h_q0(self):
        inv_sqrt2 = 1.0 / math.sqrt(2)
        s = self.state

        self.state = [
            (s[0] + s[2]) * inv_sqrt2,
            (s[1] + s[3]) * inv_sqrt2,
            (s[0] - s[2]) * inv_sqrt2,
            (s[1] - s[3]) * inv_sqrt2,
        ]

        self.log.append("GATE: H(q0)")

    def cx_q0_q1(self):
        s = self.state
        self.state = [s[0], s[1], s[3], s[2]]
        self.log.append("GATE: CX(q0 -> q1)")

    def calculate_fidelity(self, target_state):
        inner_product = sum(
            exp_val * tgt_val.conjugate()
            for exp_val, tgt_val in zip(self.state, target_state)
        )
        return abs(inner_product) ** 2


def sha256_file(path):
    digest = hashlib.sha256()

    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            digest.update(chunk)

    return digest.hexdigest()


def run_experiment():
    print("=== TUU LOCAL BACKEND B0' ===")

    backend = TUULocalBackend()

    backend.h_q0()
    backend.cx_q0_q1()

    inv_sqrt2 = 1.0 / math.sqrt(2)

    target_state = [
        complex(inv_sqrt2, 0),
        complex(0, 0),
        complex(0, 0),
        complex(inv_sqrt2, 0),
    ]

    f_recv = backend.calculate_fidelity(target_state)

    backend.log.append(
        f"MEASUREMENT: Fidelity = {f_recv:.12f}"
    )

    state_vector = [
        [c.real, c.imag]
        for c in backend.state
    ]

    experimental_payload = {
        "backend": "pure-python-statevector-b0-prime",
        "circuit_id": "C0",
        "circuit_execution": backend.log,
        "final_state_vector": state_vector,
        "metric_F_recv": f_recv,
        "target_state": "Phi_plus",
    }

    canonical_experiment = json.dumps(
        experimental_payload,
        sort_keys=True,
        separators=(",", ":"),
    )

    experiment_hash = hashlib.sha256(
        canonical_experiment.encode("utf-8")
    ).hexdigest()

    raw_log = {
        "timestamp_utc": datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat(),
        **experimental_payload,
        "experiment_hash": experiment_hash,
    }

    # Serialização única e materialização física.
    log_json = json.dumps(
        raw_log,
        indent=2,
        sort_keys=True,
        ensure_ascii=False,
    ) + "\n"

    with open(RAW_LOG, "w", encoding="utf-8", newline="\n") as f:
        f.write(log_json)
        f.flush()
        os.fsync(f.fileno())

    # O hash é calculado SOMENTE a partir do arquivo retido.
    raw_log_hash = sha256_file(RAW_LOG)

    print(log_json, end="")
    print(f"EXPERIMENT_HASH: {experiment_hash}")
    print(f"RAW_LOG_SHA256: {raw_log_hash}")
    print(f"RAW_LOG_PATH: {RAW_LOG}")

    # Verificação imediata de existência e tamanho.
    size = os.path.getsize(RAW_LOG)

    print(f"RAW_LOG_EXISTS: {os.path.isfile(RAW_LOG)}")
    print(f"RAW_LOG_BYTES: {size}")


if __name__ == "__main__":
    run_experiment()
