import math
import json
import datetime
import hashlib


class TUULocalBackend:
    def __init__(self):
        # |00> = [1, 0, 0, 0]
        # Índices: 0=|00>, 1=|01>, 2=|10>, 3=|11>
        self.state = [
            complex(1, 0),
            complex(0, 0),
            complex(0, 0),
            complex(0, 0),
        ]
        self.log = []

    def h_q0(self):
        """Hadamard no qubit 0, tratado como MSB."""
        inv_sqrt2 = 1.0 / math.sqrt(2)
        s = self.state

        new_s0 = (s[0] + s[2]) * inv_sqrt2
        new_s1 = (s[1] + s[3]) * inv_sqrt2
        new_s2 = (s[0] - s[2]) * inv_sqrt2
        new_s3 = (s[1] - s[3]) * inv_sqrt2

        self.state = [new_s0, new_s1, new_s2, new_s3]
        self.log.append("GATE: H(q0)")

    def cx_q0_q1(self):
        """CNOT: q0 controle, q1 alvo."""
        s = self.state
        self.state = [s[0], s[1], s[3], s[2]]
        self.log.append("GATE: CX(q0 -> q1)")

    def calculate_fidelity(self, target_state):
        """F = |<target|experimental>|²."""
        inner_product = sum(
            exp_val * tgt_val.conjugate()
            for exp_val, tgt_val in zip(self.state, target_state)
        )
        return abs(inner_product) ** 2


def run_experiment():
    print("=== TUU LOCAL BACKEND B0 ===")

    backend = TUULocalBackend()

    # C0: H(q0) -> CX(q0 -> q1)
    backend.h_q0()
    backend.cx_q0_q1()

    # Q0: Bell state |Phi+>
    inv_sqrt2 = 1.0 / math.sqrt(2)
    target_state = [
        complex(inv_sqrt2, 0),
        complex(0, 0),
        complex(0, 0),
        complex(inv_sqrt2, 0),
    ]

    f_recv = backend.calculate_fidelity(target_state)
    backend.log.append(f"MEASUREMENT: Fidelity = {f_recv:.12f}")

    state_vector = [
        (c.real, c.imag)
        for c in backend.state
    ]

    # Payload experimental determinístico:
    # não contém timestamp nem hash de si próprio.
    experimental_payload = {
        "backend": "pure-python-statevector-b0",
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

    # Log bruto concreto inclui timestamp.
    raw_log = {
        "timestamp_utc": datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat(),
        **experimental_payload,
        "experiment_hash": experiment_hash,
    }

    log_json = json.dumps(
        raw_log,
        indent=2,
        sort_keys=True,
    )

    raw_log_hash = hashlib.sha256(
        log_json.encode("utf-8")
    ).hexdigest()

    print(log_json)
    print(f"\nEXPERIMENT_HASH: {experiment_hash}")
    print(f"RAW_LOG_SHA256: {raw_log_hash}")


if __name__ == "__main__":
    run_experiment()
