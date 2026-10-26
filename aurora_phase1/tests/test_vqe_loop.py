"""Testes de aurora_phase1.core.vqe_loop (Bloco 9)."""
import json
import unittest
from pathlib import Path

from aurora_phase1.core.quantum_bridge import QuantumBridge
from aurora_phase1.core.vqe_loop import VQELoop


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_contracts():
    bridge_path = (
        REPO_ROOT / "aurora_phase1" / "contracts" / "quantum_observer_role.json"
    )
    vqe_path = (
        REPO_ROOT / "aurora_phase1" / "contracts" / "vqe_loop_policy.json"
    )
    return (
        json.loads(bridge_path.read_text(encoding="utf-8")),
        json.loads(vqe_path.read_text(encoding="utf-8")),
    )


class TestVQELoop(unittest.TestCase):

    def setUp(self):
        bridge_contract, vqe_policy = _load_contracts()
        self.bridge = QuantumBridge(bridge_contract)
        self.vqe_policy = vqe_policy
        self.loop = VQELoop(bridge=self.bridge, policy=vqe_policy)

    def test_loop_runs(self):
        result = self.loop.run(seed=42, target_energy=0.0)
        self.assertGreater(result.iterations, 0)
        self.assertLessEqual(result.iterations, self.vqe_policy["max_iterations"])
        self.assertEqual(len(result.history), result.iterations)

    def test_history_fields(self):
        result = self.loop.run(seed=42, target_energy=0.0)
        h0 = result.history[0]
        self.assertEqual(h0.iteration, 0)
        self.assertGreater(len(h0.params), 0)
        self.assertIsInstance(h0.energy, float)
        self.assertIsNotNone(h0.measurement_hash)

    def test_determinism(self):
        r1 = self.loop.run(seed=42, target_energy=0.0)
        r2 = self.loop.run(seed=42, target_energy=0.0)
        self.assertEqual(r1.iterations, r2.iterations)
        self.assertEqual(r1.final_energy, r2.final_energy)
        self.assertEqual(r1.result_hash, r2.result_hash)

    def test_different_seeds(self):
        r1 = self.loop.run(seed=42, target_energy=0.0)
        r3 = self.loop.run(seed=99, target_energy=0.0)
        self.assertNotEqual(r1.result_hash, r3.result_hash)

    def test_max_iterations_reached(self):
        loop_short = VQELoop(
            bridge=self.bridge,
            policy={
                **self.vqe_policy,
                "max_iterations": 3,
                "convergence_threshold": 1e-15,
            },
        )
        result = loop_short.run(seed=42, target_energy=1e6)
        self.assertEqual(result.iterations, 3)
        self.assertFalse(result.converged)
        self.assertTrue(result.max_iterations_reached)

    def test_final_energy_is_best(self):
        loop_short = VQELoop(
            bridge=self.bridge,
            policy={
                **self.vqe_policy,
                "max_iterations": 3,
                "convergence_threshold": 1e-15,
            },
        )
        result = loop_short.run(seed=42, target_energy=1e6)
        energies = [h.energy for h in result.history]
        self.assertEqual(result.final_energy, min(energies))

    def test_converged_true(self):
        result = self.loop.run(seed=42, target_energy=0.0)
        first_energy = result.history[0].energy
        loop_conv = VQELoop(
            bridge=self.bridge,
            policy={
                **self.vqe_policy,
                "max_iterations": 5,
                "convergence_threshold": 1e6,
            },
        )
        result_conv = loop_conv.run(seed=42, target_energy=first_energy)
        self.assertTrue(result_conv.converged)


if __name__ == "__main__":
    unittest.main()
