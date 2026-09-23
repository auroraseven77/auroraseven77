"""Testes de aurora_phase1.core.tuu (Bloco 4)."""
import tempfile
import unittest
from pathlib import Path

from aurora_phase1.core.agent import EphemeralAgent
from aurora_phase1.core.ledger import Ledger
from aurora_phase1.core.tuu import (
    STATUS_APPROVED,
    STATUS_REJECTED_HASH_MISMATCH,
    STATUS_REJECTED_MALFORMED,
    STATUS_REJECTED_REPLAY,
    STATUS_REJECTED_TEMPORAL_ANOMALY,
    TUU,
)


TUU_POLICY = {
    "contract_id": "tuu_policy_v1",
    "version": "1.0.0",
    "authorization": {"default_decision": "reject"},
    "circuit_breaker": {
        "max_invalid_proposals": 3,
        "on_threshold_exceeded": "OPEN",
        "reset_on_valid_proposal": False,
    },
    "temporal": {
        "max_future_ticks": 1,
        "allow_negative_ticks": False,
        "require_integer_ticks": True,
    },
    "replay": {
        "rejected_proposals_count_as_seen": True,
        "persist_seen_across_reconstruction": True,
    },
    "denied_patterns": [],
}

ARGOS_CONTRACT = {
    "contract_id": "role_argos_v1",
    "version": "1.0.0",
    "role": "ARGOS",
    "region": "OBSERVATION",
    "allowed_actions": ["PROPOSE_OBSERVATION", "PROPOSE_ANOMALY_DETECTION"],
    "disallowed_actions": ["EXECUTE_DIRECTLY", "INVOKE_SHELL"],
    "hypothesis_max_length": 512,
    "denied_patterns": [],
}

CONTEXT = {"fluxo_entropico": 0.142}


class TestTUU(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.ledger = Ledger(self.tmpdir / "ledger.jsonl")
        self.tuu = TUU(ledger=self.ledger, contract=TUU_POLICY)

    def test_init_empty(self):
        self.assertEqual(self.tuu.tick, 0)
        self.assertEqual(self.tuu.circuit_state, "CLOSED")
        self.assertEqual(self.ledger.count(), 0)

    def test_approve_valid(self):
        agent = EphemeralAgent(seed=42, context=CONTEXT, contract=ARGOS_CONTRACT)
        proposal = agent.propose(
            "PROPOSE_OBSERVATION",
            {"temperature": 298.15},
            timestamp_logical=0,
            hypothesis="Equilíbrio normal.",
        )
        decision = self.tuu.evaluate_proposal(proposal.to_dict())
        self.assertEqual(decision.status, STATUS_APPROVED)
        self.assertEqual(self.tuu.tick, 1)
        self.assertEqual(self.ledger.count(), 1)

    def test_replay(self):
        agent = EphemeralAgent(seed=42, context=CONTEXT, contract=ARGOS_CONTRACT)
        proposal = agent.propose(
            "PROPOSE_OBSERVATION", {"t": 1}, timestamp_logical=0
        )
        self.tuu.evaluate_proposal(proposal.to_dict())
        decision = self.tuu.evaluate_proposal(proposal.to_dict())
        self.assertEqual(decision.status, STATUS_REJECTED_REPLAY)
        self.assertEqual(self.ledger.count(), 1)
        self.assertEqual(self.tuu.tick, 1)

    def test_hash_mismatch(self):
        agent = EphemeralAgent(seed=99, context=CONTEXT, contract=ARGOS_CONTRACT)
        proposal = agent.propose(
            "PROPOSE_OBSERVATION", {"x": 1}, timestamp_logical=0
        )
        tampered = proposal.to_dict()
        tampered["hypothesis"] = "TAMPERED"
        decision = self.tuu.evaluate_proposal(tampered)
        self.assertEqual(decision.status, STATUS_REJECTED_HASH_MISMATCH)

    def test_temporal_anomaly(self):
        agent = EphemeralAgent(seed=123, context=CONTEXT, contract=ARGOS_CONTRACT)
        proposal = agent.propose(
            "PROPOSE_OBSERVATION", {"x": 1}, timestamp_logical=100
        )
        decision = self.tuu.evaluate_proposal(proposal.to_dict())
        self.assertEqual(decision.status, STATUS_REJECTED_TEMPORAL_ANOMALY)

    def test_malformed(self):
        decision = self.tuu.evaluate_proposal({"garbage": True})
        self.assertEqual(decision.status, STATUS_REJECTED_MALFORMED)

    def test_circuit_breaker_opens(self):
        # 3 rejeições REAIS (que contam) — não malformed
        # Replay é detectado pelo portão 1 e conta
        agent = EphemeralAgent(seed=42, context=CONTEXT, contract=ARGOS_CONTRACT)
        p = agent.propose("PROPOSE_OBSERVATION", {"t": 1}, timestamp_logical=0)
        self.tuu.evaluate_proposal(p.to_dict())  # approve

        # 3 replays contam como invalid
        for _ in range(3):
            self.tuu.evaluate_proposal(p.to_dict())

        self.assertEqual(self.tuu.circuit_state, "OPEN")

    def test_hydrate_from_ledger(self):
        agent = EphemeralAgent(seed=42, context=CONTEXT, contract=ARGOS_CONTRACT)
        proposal = agent.propose(
            "PROPOSE_OBSERVATION", {"t": 1}, timestamp_logical=0
        )
        self.tuu.evaluate_proposal(proposal.to_dict())

        tuu2 = TUU(ledger=self.ledger, contract=TUU_POLICY)
        self.assertEqual(len(tuu2._seen_proposal_ids), 0)
        tuu2._hydrate_from_ledger()
        self.assertIn(proposal.proposal_id, tuu2._seen_proposal_ids)

    def test_replay_after_hydrate(self):
        agent = EphemeralAgent(seed=42, context=CONTEXT, contract=ARGOS_CONTRACT)
        proposal = agent.propose(
            "PROPOSE_OBSERVATION", {"t": 1}, timestamp_logical=0
        )
        self.tuu.evaluate_proposal(proposal.to_dict())

        tuu2 = TUU(ledger=self.ledger, contract=TUU_POLICY)
        tuu2._hydrate_from_ledger()
        decision = tuu2.evaluate_proposal(proposal.to_dict())
        self.assertEqual(decision.status, STATUS_REJECTED_REPLAY)

    def test_state_hash_deterministic(self):
        h1 = self.tuu.state_hash()
        h2 = self.tuu.state_hash()
        self.assertEqual(h1, h2)
        self.assertEqual(len(h1), 64)

    def test_determinism_between_tuus(self):
        ledger_a = Ledger(self.tmpdir / "a.jsonl")
        ledger_b = Ledger(self.tmpdir / "b.jsonl")
        tuu_a = TUU(ledger=ledger_a, contract=TUU_POLICY)
        tuu_b = TUU(ledger=ledger_b, contract=TUU_POLICY)

        agent = EphemeralAgent(seed=42, context=CONTEXT, contract=ARGOS_CONTRACT)
        p = agent.propose(
            "PROPOSE_OBSERVATION", {"x": 1}, timestamp_logical=0, hypothesis="H"
        )
        da = tuu_a.evaluate_proposal(p.to_dict())
        db = tuu_b.evaluate_proposal(p.to_dict())
        self.assertEqual(da.status, db.status)
        self.assertEqual(tuu_a.state_hash(), tuu_b.state_hash())
        self.assertEqual(ledger_a.top_hash(), ledger_b.top_hash())


if __name__ == "__main__":
    unittest.main()
