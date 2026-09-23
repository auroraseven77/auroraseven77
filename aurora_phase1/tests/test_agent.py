"""Testes de aurora_phase1.core.agent (Bloco 3)."""
import unittest

from aurora_phase1.core.agent import EphemeralAgent, Tombstone


CONTRACT = {
    "contract_id": "role_argos_v1",
    "version": "1.0.0",
    "role": "ARGOS",
    "region": "OBSERVATION",
    "allowed_actions": [
        "PROPOSE_OBSERVATION",
        "PROPOSE_ANOMALY_DETECTION",
        "PROPOSE_STATE_SNAPSHOT",
    ],
    "disallowed_actions": [
        "EXECUTE_DIRECTLY",
        "INVOKE_SHELL",
        "MODIFY_CONTRACT",
    ],
    "hypothesis_max_length": 512,
    "denied_patterns": [],
}

CONTEXT = {"fluxo_entropico": 0.142, "pressao_interna": 101.3}


class TestAgent(unittest.TestCase):

    def test_deterministic_birth(self):
        a1 = EphemeralAgent(seed=42, context=CONTEXT, contract=CONTRACT)
        a2 = EphemeralAgent(seed=42, context=CONTEXT, contract=CONTRACT)
        self.assertEqual(a1.agent_id, a2.agent_id)

    def test_different_context(self):
        a1 = EphemeralAgent(seed=42, context=CONTEXT, contract=CONTRACT)
        a3 = EphemeralAgent(
            seed=42, context={**CONTEXT, "x": 1}, contract=CONTRACT
        )
        self.assertNotEqual(a1.agent_id, a3.agent_id)

    def test_different_seed(self):
        a1 = EphemeralAgent(seed=42, context=CONTEXT, contract=CONTRACT)
        a4 = EphemeralAgent(seed=99, context=CONTEXT, contract=CONTRACT)
        self.assertNotEqual(a1.agent_id, a4.agent_id)

    def test_different_contract_version(self):
        a1 = EphemeralAgent(seed=42, context=CONTEXT, contract=CONTRACT)
        v2 = {**CONTRACT, "version": "2.0.0"}
        a5 = EphemeralAgent(seed=42, context=CONTEXT, contract=v2)
        self.assertNotEqual(a1.agent_id, a5.agent_id)

    def test_propose_valid(self):
        a = EphemeralAgent(seed=42, context=CONTEXT, contract=CONTRACT)
        p = a.propose(
            "PROPOSE_OBSERVATION",
            {"temperature": 298.15},
            timestamp_logical=1,
            hypothesis="Equilíbrio normal.",
        )
        self.assertEqual(p.agent_id, a.agent_id)
        self.assertEqual(p.action_type, "PROPOSE_OBSERVATION")
        self.assertEqual(len(p.proposal_id), 64)

    def test_proposal_id_deterministic(self):
        a1 = EphemeralAgent(seed=42, context=CONTEXT, contract=CONTRACT)
        p1 = a1.propose(
            "PROPOSE_OBSERVATION",
            {"temperature": 298.15},
            timestamp_logical=1,
            hypothesis="Equilíbrio normal.",
        )
        a2 = EphemeralAgent(seed=42, context=CONTEXT, contract=CONTRACT)
        p2 = a2.propose(
            "PROPOSE_OBSERVATION",
            {"temperature": 298.15},
            timestamp_logical=1,
            hypothesis="Equilíbrio normal.",
        )
        self.assertEqual(p1.proposal_id, p2.proposal_id)

    def test_propose_disallowed(self):
        a = EphemeralAgent(seed=42, context=CONTEXT, contract=CONTRACT)
        with self.assertRaises(PermissionError):
            a.propose("EXECUTE_DIRECTLY", {}, timestamp_logical=1)

    def test_propose_unknown(self):
        a = EphemeralAgent(seed=42, context=CONTEXT, contract=CONTRACT)
        with self.assertRaises(PermissionError):
            a.propose("UNKNOWN", {}, timestamp_logical=1)

    def test_die_returns_tombstone(self):
        a = EphemeralAgent(seed=42, context=CONTEXT, contract=CONTRACT)
        a.propose(
            "PROPOSE_OBSERVATION",
            {"t": 1},
            timestamp_logical=1,
            hypothesis="h",
        )
        tomb = a.die()
        self.assertIsInstance(tomb, Tombstone)
        self.assertEqual(tomb.agent_id, a.agent_id)
        self.assertEqual(tomb.role, "ARGOS")
        self.assertEqual(tomb.proposals_made, 1)
        self.assertEqual(tomb.status, "TERMINATED")

    def test_propose_after_death_raises(self):
        a = EphemeralAgent(seed=42, context=CONTEXT, contract=CONTRACT)
        a.die()
        with self.assertRaises(RuntimeError):
            a.propose("PROPOSE_OBSERVATION", {}, timestamp_logical=2)

    def test_die_idempotent(self):
        a = EphemeralAgent(seed=42, context=CONTEXT, contract=CONTRACT)
        a.die()
        with self.assertRaises(RuntimeError):
            a.die()

    def test_tombstone_deterministic(self):
        a1 = EphemeralAgent(seed=42, context=CONTEXT, contract=CONTRACT)
        a1.propose(
            "PROPOSE_OBSERVATION",
            {"t": 1},
            timestamp_logical=1,
            hypothesis="h",
        )
        t1 = a1.die()

        a2 = EphemeralAgent(seed=42, context=CONTEXT, contract=CONTRACT)
        a2.propose(
            "PROPOSE_OBSERVATION",
            {"t": 1},
            timestamp_logical=1,
            hypothesis="h",
        )
        t2 = a2.die()

        self.assertEqual(t1.to_dict(), t2.to_dict())


if __name__ == "__main__":
    unittest.main()
