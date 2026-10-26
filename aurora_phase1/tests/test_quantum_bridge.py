"""Testes de aurora_phase1.core.quantum_bridge (Bloco 8)."""
import json
import unittest
from pathlib import Path

from aurora_phase1.core.quantum_bridge import (
    STATUS_MEASUREMENT_COMPLETED,
    STATUS_REJECTED_INVALID_OPERATOR,
    STATUS_REJECTED_QUBIT_LIMIT,
    QuantumBridge,
)


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_contract() -> dict:
    path = REPO_ROOT / "aurora_phase1" / "contracts" / "quantum_observer_role.json"
    return json.loads(path.read_text(encoding="utf-8"))


class TestQuantumBridge(unittest.TestCase):

    def setUp(self):
        self.bridge = QuantumBridge(_load_contract())

    def _proposal(self, n_qubits: int, terms: list) -> dict:
        return {
            "proposal_id": "test",
            "observation_data": {"n_qubits": n_qubits, "terms": terms},
        }

    def test_z0_on_zero_state(self):
        r = self.bridge.execute_measurement(self._proposal(
            4, [{"sites": [0], "operators": ["Z"], "coefficient": 1.0}]
        ))
        self.assertEqual(r.status, STATUS_MEASUREMENT_COMPLETED)
        self.assertAlmostEqual(r.value_real, 1.0, places=10)
        self.assertAlmostEqual(r.value_imag, 0.0, places=10)
        self.assertEqual(r.backend, "b1_motor")
        self.assertEqual(len(r.measurement_hash), 64)

    def test_z0_plus_z1(self):
        r = self.bridge.execute_measurement(self._proposal(4, [
            {"sites": [0], "operators": ["Z"], "coefficient": 1.0},
            {"sites": [1], "operators": ["Z"], "coefficient": 1.0},
        ]))
        self.assertAlmostEqual(r.value_real, 2.0, places=10)

    def test_x0_on_zero_state(self):
        r = self.bridge.execute_measurement(self._proposal(
            4, [{"sites": [0], "operators": ["X"], "coefficient": 1.0}]
        ))
        self.assertAlmostEqual(r.value_real, 0.0, places=10)

    def test_qubit_limit(self):
        r = self.bridge.execute_measurement(self._proposal(
            16, [{"sites": [0], "operators": ["Z"], "coefficient": 1.0}]
        ))
        self.assertEqual(r.status, STATUS_REJECTED_QUBIT_LIMIT)

    def test_invalid_operator(self):
        r = self.bridge.execute_measurement(self._proposal(
            4, [{"sites": [0], "operators": ["Q"], "coefficient": 1.0}]
        ))
        self.assertEqual(r.status, STATUS_REJECTED_INVALID_OPERATOR)

    def test_determinism(self):
        p = self._proposal(
            4, [{"sites": [0], "operators": ["Z"], "coefficient": 1.0}]
        )
        r1 = self.bridge.execute_measurement(p)
        r2 = self.bridge.execute_measurement(p)
        self.assertEqual(r1.measurement_hash, r2.measurement_hash)
        self.assertEqual(r1.value_real, r2.value_real)

    def test_coefficient(self):
        r = self.bridge.execute_measurement(self._proposal(
            4, [{"sites": [0], "operators": ["Z"], "coefficient": 2.5}]
        ))
        self.assertAlmostEqual(r.value_real, 2.5, places=10)

    def test_invalid_site(self):
        r = self.bridge.execute_measurement(self._proposal(
            4, [{"sites": [10], "operators": ["Z"], "coefficient": 1.0}]
        ))
        self.assertEqual(r.status, "REJECTED_INVALID_SITE")

    def test_duplicate_site(self):
        r = self.bridge.execute_measurement(self._proposal(
            4,
            [{"sites": [0, 0], "operators": ["Z", "X"], "coefficient": 1.0}],
        ))
        self.assertEqual(r.status, "REJECTED_DUPLICATE_SITE")

    def test_non_local_zz(self):
        r = self.bridge.execute_measurement(self._proposal(
            6, [{"sites": [0, 5], "operators": ["Z", "Z"], "coefficient": 1.0}]
        ))
        self.assertAlmostEqual(r.value_real, 1.0, places=10)


if __name__ == "__main__":
    unittest.main()
