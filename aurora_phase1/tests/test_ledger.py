"""Testes de aurora_phase1.core.ledger, incluindo parsing estrito de JSONL."""
import json
import tempfile
import unittest
from pathlib import Path

from aurora_phase1.core.crypto import GENESIS_PREV_HASH, hash_bytes
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
        self.ledger.add_block("GENESIS_INITIALIZED", {}, tick=0)
        b1 = self.ledger.add_block("AGENT_BORN", {"agent_id": "abc"}, tick=0)
        self.assertEqual(self.ledger.top_hash(), b1.entry_hash)

    def test_chain_corruption_detected(self):
        self.ledger.add_block("GENESIS_INITIALIZED", {}, tick=0)
        self.ledger.add_block("AGENT_BORN", {"agent_id": "abc"}, tick=0)
        # Um hash sintaticamente válido permite testar a quebra da cadeia,
        # separada da validação lexical dos hashes.
        with self.ledger_path.open("a", encoding="utf-8") as f:
            f.write(
                '{"seq":2,"tick":0,"event_type":"FORGED","payload":{},'
                '"prev_hash":"deadbeef' + "0" * 56 + '",'
                '"entry_hash":"' + "0" * 64 + '"}\n'
            )
        r = self.ledger.audit_chain()
        self.assertFalse(r.chain_integrity)
        self.assertEqual(r.failed_seq, 2)
        self.assertEqual(r.last_valid_seq, 1)

    def test_record_finding(self):
        evidence = self.tmpdir / "test_evidence.md"
        evidence.write_text("# Attack 1\nFound vulnerability.", encoding="utf-8")
        block = self.ledger.record_finding("attack_1", evidence, tick=0)
        self.assertEqual(block.event_type, "ATTACK_FINDING_RECORDED")
        self.assertEqual(block.payload["attack_id"], "attack_1")
        self.assertEqual(
            block.payload["evidence_hash"],
            hash_bytes(evidence.read_bytes()),
        )

    def test_record_finding_hashes_raw_binary_bytes(self):
        evidence = self.tmpdir / "binary_evidence.bin"
        raw = b"\x00\xff\x80\n"
        evidence.write_bytes(raw)
        block = self.ledger.record_finding("binary-fixture", evidence, tick=4)
        self.assertEqual(block.payload["evidence_hash"], hash_bytes(raw))
        self.assertTrue(self.ledger.audit_chain().chain_integrity)

    def test_record_finding_streams_large_evidence_without_read_bytes(self):
        import hashlib
        from unittest.mock import patch

        evidence = self.tmpdir / "large_binary_evidence.bin"
        raw = b"0123456789abcdef" * 65536  # 1 MiB deterministic fixture
        evidence.write_bytes(raw)

        with patch.object(
            Path,
            "read_bytes",
            side_effect=AssertionError("evidence hashing must stream raw bytes"),
        ):
            block = self.ledger.record_finding("large-fixture", evidence, tick=4)

        self.assertEqual(block.payload["evidence_hash"], hashlib.sha256(raw).hexdigest())
        self.assertTrue(self.ledger.audit_chain().chain_integrity)

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

    def test_add_block_rejects_blank_event_type(self):
        with self.assertRaisesRegex(TypeError, "event_type"):
            self.ledger.add_block("   ", {})

    def test_add_block_rejects_bool_tick(self):
        with self.assertRaisesRegex(TypeError, "tick"):
            self.ledger.add_block("EVENT", {}, tick=True)

    def test_audit_rejects_unhashed_extra_top_level_field(self):
        self.ledger.add_block("GENESIS_INITIALIZED", {})
        data = json.loads(self.ledger_path.read_text(encoding="utf-8"))
        data["operator_note"] = "not covered by entry_hash"
        self.ledger_path.write_text(json.dumps(data) + "\n", encoding="utf-8")
        result = self.ledger.audit_chain()
        self.assertFalse(result.chain_integrity)
        self.assertIn("campos não autenticados", result.diagnostic)

    def test_audit_rejects_duplicate_json_keys(self):
        self.ledger.add_block("GENESIS_INITIALIZED", {})
        line = self.ledger_path.read_text(encoding="utf-8").rstrip("\n")
        line = line.replace('"seq": 0', '"seq": 0, "seq": 0', 1)
        self.ledger_path.write_text(line + "\n", encoding="utf-8")
        result = self.ledger.audit_chain()
        self.assertFalse(result.chain_integrity)
        self.assertIn("chave JSON duplicada", result.diagnostic)

    def test_audit_rejects_blank_physical_lines(self):
        self.ledger.add_block("GENESIS_INITIALIZED", {})
        with self.ledger_path.open("a", encoding="utf-8") as f:
            f.write("\n")
        result = self.ledger.audit_chain()
        self.assertFalse(result.chain_integrity)
        self.assertIn("Linha 2 vazia", result.diagnostic)

    def test_audit_rejects_boolean_sequence_number(self):
        self.ledger.add_block("GENESIS_INITIALIZED", {})
        data = json.loads(self.ledger_path.read_text(encoding="utf-8"))
        data["seq"] = True
        self.ledger_path.write_text(json.dumps(data) + "\n", encoding="utf-8")
        result = self.ledger.audit_chain()
        self.assertFalse(result.chain_integrity)
        self.assertIn("seq inválido", result.diagnostic)

    def test_audit_rejects_non_object_payload(self):
        self.ledger.add_block("GENESIS_INITIALIZED", {})
        data = json.loads(self.ledger_path.read_text(encoding="utf-8"))
        data["payload"] = []
        self.ledger_path.write_text(json.dumps(data) + "\n", encoding="utf-8")
        result = self.ledger.audit_chain()
        self.assertFalse(result.chain_integrity)
        self.assertIn("payload inválido", result.diagnostic)

    def test_audit_rejects_nonfinite_json_constants(self):
        line = (
            '{"seq":0,"tick":0,"event_type":"EVENT","payload":{"value":NaN},'
            '"prev_hash":"' + GENESIS_PREV_HASH + '","entry_hash":"' + "0" * 64 + '"}\n'
        )
        self.ledger_path.write_text(line, encoding="utf-8")
        result = self.ledger.audit_chain()
        self.assertFalse(result.chain_integrity)
        self.assertIn("não finita", result.diagnostic)

    def test_audit_rejects_non_hex_hash(self):
        line = (
            '{"seq":0,"tick":0,"event_type":"EVENT","payload":{},'
            '"prev_hash":"' + "g" * 64 + '","entry_hash":"' + "0" * 64 + '"}\n'
        )
        self.ledger_path.write_text(line, encoding="utf-8")
        result = self.ledger.audit_chain()
        self.assertFalse(result.chain_integrity)
        self.assertIn("prev_hash inválido", result.diagnostic)


if __name__ == "__main__":
    unittest.main()
