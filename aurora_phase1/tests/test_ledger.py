"""Testes de aurora_phase1.core.ledger (Bloco 2)."""
import tempfile
import unittest
from pathlib import Path

from aurora_phase1.core.crypto import GENESIS_PREV_HASH
from aurora_phase1.core.ledger import Ledger


class TestLedger(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.ledger_path = self.tmpdir / "test_ledger.jsonl"
        self.ledger = Ledger(self.ledger_path)

    def test_empty_ledger_is_integro(self):
        r = self.ledger.audit_chain()
        self.assertTrue(r.chain_integrity)
        self.assertEqual(r.total_blocks, 0)

    def test_genesis_block(self):
        b0 = self.ledger.add_block("GENESIS_INITIALIZED", {}, tick=0)
        self.assertEqual(b0.seq, 0)
        self.assertEqual(b0.prev_hash, GENESIS_PREV_HASH)
        self.assertEqual(len(b0.entry_hash), 64)

    def test_chaining(self):
        b0 = self.ledger.add_block("GENESIS_INITIALIZED", {}, tick=0)
        b1 = self.ledger.add_block("AGENT_BORN", {"agent_id": "abc"}, tick=0)
        self.assertEqual(b1.seq, 1)
        self.assertEqual(b1.prev_hash, b0.entry_hash)
        self.assertNotEqual(b1.prev_hash, GENESIS_PREV_HASH)

    def test_audit_integro(self):
        self.ledger.add_block("GENESIS_INITIALIZED", {}, tick=0)
        self.ledger.add_block("AGENT_BORN", {"agent_id": "abc"}, tick=0)
        r = self.ledger.audit_chain()
        self.assertTrue(r.chain_integrity)
        self.assertEqual(r.total_blocks, 2)
        self.assertEqual(r.last_valid_seq, 1)
        self.assertIsNone(r.failed_seq)

    def test_top_hash_clean(self):
        b0 = self.ledger.add_block("GENESIS_INITIALIZED", {}, tick=0)
        b1 = self.ledger.add_block("AGENT_BORN", {"agent_id": "abc"}, tick=0)
        self.assertEqual(self.ledger.top_hash(), b1.entry_hash)

    def test_chain_corruption_detected(self):
        self.ledger.add_block("GENESIS_INITIALIZED", {}, tick=0)
        self.ledger.add_block("AGENT_BORN", {"agent_id": "abc"}, tick=0)
        # adiciona bloco forjado
        with open(self.ledger_path, "a") as f:
            f.write(
                '{"seq":2,"tick":0,"event_type":"FORGED","payload":{},'
                '"prev_hash":"deadbeef' + "0" * 56 + '",'
                '"entry_hash":"' + "x" * 64 + '"}\n'
            )
        r = self.ledger.audit_chain()
        self.assertFalse(r.chain_integrity)
        self.assertEqual(r.failed_seq, 2)
        self.assertEqual(r.last_valid_seq, 1)

    def test_record_finding(self):
        evidence = self.tmpdir / "test_evidence.md"
        evidence.write_text("# Attack 1\nFound vulnerability.")
        block = self.ledger.record_finding("attack_1", evidence, tick=0)
        self.assertEqual(block.event_type, "ATTACK_FINDING_RECORDED")
        self.assertEqual(block.payload["attack_id"], "attack_1")
        self.assertEqual(len(block.payload["evidence_hash"]), 64)

    def test_seen_proposal_ids(self):
        self.ledger.add_block(
            "PROPOSAL_PROCESSED_AND_APPROVED", {"proposal_id": "p1"}
        )
        self.ledger.add_block("PROPOSAL_REJECTED", {"proposal_id": "p2"})
        seen = self.ledger.seen_proposal_ids()
        self.assertEqual(seen, {"p1", "p2"})

    def test_determinism_between_ledgers(self):
        ledger_a = Ledger(self.tmpdir / "det_a.jsonl")
        ledger_b = Ledger(self.tmpdir / "det_b.jsonl")
        for l in (ledger_a, ledger_b):
            l.add_block("GENESIS_INITIALIZED", {}, tick=0)
            l.add_block("AGENT_BORN", {"agent_id": "xyz"}, tick=0)
        self.assertEqual(ledger_a.top_hash(), ledger_b.top_hash())


if __name__ == "__main__":
    unittest.main()
