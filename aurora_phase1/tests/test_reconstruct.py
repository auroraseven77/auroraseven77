"""Testes de aurora_phase1.core.reconstruct (Bloco 5)."""
import tempfile
import unittest
from pathlib import Path

from aurora_phase1.core.agent import EphemeralAgent
from aurora_phase1.core.ledger import Ledger
from aurora_phase1.core.reconstruct import WorldReconstructor
from aurora_phase1.core.tuu import TUU, STATUS_APPROVED


TUU_POLICY = {
    "contract_id": "tuu_policy_v1",
    "version": "1.0.0",
    "authorization": {"default_decision": "reject"},
    "circuit_breaker": {
        "max_invalid_proposals": 10,
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
    "allowed_actions": ["PROPOSE_OBSERVATION"],
    "disallowed_actions": ["EXECUTE_DIRECTLY"],
    "hypothesis_max_length": 512,
    "denied_patterns": [],
}

CONTEXT = {"fluxo": 0.142}


class TestReconstruct(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.ledger_path = self.tmpdir / "ledger.jsonl"
        self.ledger = Ledger(self.ledger_path)

    def test_reconstruct_empty(self):
        recon = WorldReconstructor(self.ledger)
        result = recon.reconstruct()
        self.assertTrue(result.success)
        self.assertEqual(result.blocks_processed, 0)
        self.assertEqual(result.state["tick"], 0)
        self.assertEqual(result.stopped_at_seq, -1)

    def test_reconstruct_after_one_approval(self):
        tuu = TUU(ledger=self.ledger, contract=TUU_POLICY)
        agent = EphemeralAgent(seed=42, context=CONTEXT, contract=ARGOS_CONTRACT)
        p = agent.propose(
            "PROPOSE_OBSERVATION", {"x": 1}, timestamp_logical=0, hypothesis="H1"
        )
        d = tuu.evaluate_proposal(p.to_dict())
        self.assertEqual(d.status, STATUS_APPROVED)

        recon = WorldReconstructor(self.ledger)
        result = recon.reconstruct()
        self.assertTrue(result.success)
        self.assertEqual(result.blocks_processed, 1)
        self.assertEqual(result.state["tick"], 1)
        self.assertEqual(result.state["completed_cycles"], 1)
        self.assertEqual(result.stopped_at_seq, 0)

    def test_state_hash_matches_tuu(self):
        tuu = TUU(ledger=self.ledger, contract=TUU_POLICY)
        agent = EphemeralAgent(seed=42, context=CONTEXT, contract=ARGOS_CONTRACT)
        p = agent.propose(
            "PROPOSE_OBSERVATION", {"x": 1}, timestamp_logical=0, hypothesis="H"
        )
        tuu.evaluate_proposal(p.to_dict())

        recon = WorldReconstructor(self.ledger)
        result = recon.reconstruct()
        self.assertEqual(result.state_hash, tuu.state_hash())
        self.assertEqual(result.state["tick"], tuu.tick)

    def test_seen_proposal_ids_preserved(self):
        tuu = TUU(ledger=self.ledger, contract=TUU_POLICY)
        agent = EphemeralAgent(seed=42, context=CONTEXT, contract=ARGOS_CONTRACT)
        p = agent.propose(
            "PROPOSE_OBSERVATION", {"x": 1}, timestamp_logical=0, hypothesis="H"
        )
        tuu.evaluate_proposal(p.to_dict())

        recon = WorldReconstructor(self.ledger)
        result = recon.reconstruct()
        self.assertIn(p.proposal_id, result.seen_proposal_ids)

    def test_reconstruction_deterministic(self):
        tuu = TUU(ledger=self.ledger, contract=TUU_POLICY)
        agent = EphemeralAgent(seed=42, context=CONTEXT, contract=ARGOS_CONTRACT)
        p = agent.propose(
            "PROPOSE_OBSERVATION", {"x": 1}, timestamp_logical=0, hypothesis="H"
        )
        tuu.evaluate_proposal(p.to_dict())

        recon = WorldReconstructor(self.ledger)
        r1 = recon.reconstruct()
        r2 = recon.reconstruct()
        self.assertEqual(r1.state_hash, r2.state_hash)
        self.assertEqual(r1.seen_proposal_ids, r2.seen_proposal_ids)

    def test_strict_stop_on_corruption(self):
        tuu = TUU(ledger=self.ledger, contract=TUU_POLICY)
        agent = EphemeralAgent(seed=42, context=CONTEXT, contract=ARGOS_CONTRACT)
        for i in range(3):
            p = agent.propose(
                "PROPOSE_OBSERVATION",
                {"i": i},
                timestamp_logical=0,
                hypothesis=f"H{i}",
            )
            tuu.evaluate_proposal(p.to_dict())

        # adiciona bloco forjado
        with open(self.ledger_path, "a") as f:
            f.write(
                '{"seq":3,"tick":0,"event_type":"FORGED","payload":{},'
                '"prev_hash":"deadbeef' + "0" * 56 + '",'
                '"entry_hash":"' + "x" * 64 + '"}\n'
            )

        recon = WorldReconstructor(self.ledger)
        result = recon.reconstruct()
        self.assertFalse(result.success)
        self.assertEqual(result.stopped_at_seq, 2)
        self.assertEqual(result.blocks_processed, 3)

    def test_unknown_event_ignored(self):
        ledger2 = Ledger(self.tmpdir / "ledger2.jsonl")
        ledger2.add_block("GENESIS_INITIALIZED", {}, tick=0)
        ledger2.add_block("UNKNOWN_FUTURE_EVENT", {"x": 1}, tick=1)
        ledger2.add_block(
            "PROPOSAL_PROCESSED_AND_APPROVED",
            {"proposal_id": "p1", "agent_id": "abc"},
            tick=2,
        )
        recon = WorldReconstructor(ledger2)
        result = recon.reconstruct()
        self.assertTrue(result.success)
        self.assertEqual(result.blocks_processed, 3)
        self.assertIn("desconhecidos ignorados", result.diagnostic.lower())


if __name__ == "__main__":
    unittest.main()
