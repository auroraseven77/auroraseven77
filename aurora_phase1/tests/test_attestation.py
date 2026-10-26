"""Testes de aurora_phase1.core.attestation (Bloco 6)."""
import tempfile
import unittest
from pathlib import Path

from aurora_phase1.core.attestation import AttestationEngine


class TestAttestation(unittest.TestCase):

    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
        self.contracts = self.tmpdir / "contracts"
        self.contracts.mkdir()
        (self.contracts / "argos_role.json").write_text('{"a": 1}')
        (self.contracts / "tuu_policy.json").write_text('{"b": 2}')

    def test_seal_two_contracts(self):
        engine = AttestationEngine(self.contracts)
        att = engine.seal()
        self.assertEqual(len(att), 2)
        self.assertIn("argos_role.json", att)
        self.assertIn("tuu_policy.json", att)
        for h in att.values():
            self.assertEqual(len(h), 64)

    def test_master_hash_deterministic(self):
        engine = AttestationEngine(self.contracts)
        engine.seal()
        m1 = engine.master_attestation_hash
        m2 = engine.master_attestation_hash
        self.assertEqual(m1, m2)
        self.assertEqual(len(m1), 64)

    def test_verify_ok(self):
        engine = AttestationEngine(self.contracts)
        engine.seal()
        result = engine.verify_disk_integrity()
        self.assertTrue(result.integrity)
        self.assertEqual(result.changes, {})

    def test_modification_detected(self):
        engine = AttestationEngine(self.contracts)
        engine.seal()
        (self.contracts / "argos_role.json").write_text('{"a": 999}')
        result = engine.verify_disk_integrity()
        self.assertFalse(result.integrity)
        self.assertEqual(result.changes, {"argos_role.json": "modified"})

    def test_deletion_detected(self):
        engine = AttestationEngine(self.contracts)
        engine.seal()
        (self.contracts / "argos_role.json").unlink()
        result = engine.verify_disk_integrity()
        self.assertFalse(result.integrity)
        self.assertEqual(result.changes, {"argos_role.json": "deleted"})

    def test_addition_detected(self):
        engine = AttestationEngine(self.contracts)
        engine.seal()
        (self.contracts / "new_contract.json").write_text('{"c": 3}')
        result = engine.verify_disk_integrity()
        self.assertFalse(result.integrity)
        self.assertEqual(result.changes, {"new_contract.json": "added"})

    def test_boot_verify_raises(self):
        engine = AttestationEngine(self.contracts)
        engine.seal()
        (self.contracts / "argos_role.json").write_text('{"a": 999}')
        with self.assertRaises(RuntimeError):
            engine.boot_verify()

    def test_boot_verify_degraded(self):
        engine = AttestationEngine(self.contracts)
        engine.seal()
        (self.contracts / "argos_role.json").write_text('{"a": 999}')
        result = engine.boot_verify(degraded=True)
        self.assertFalse(result.integrity)
        self.assertIn("tampering", result.diagnostic.lower())

    def test_empty_dir_ok(self):
        empty = self.tmpdir / "empty"
        empty.mkdir()
        engine = AttestationEngine(empty)
        engine.seal()
        result = engine.verify_disk_integrity()
        self.assertTrue(result.integrity)
        self.assertEqual(engine.attestation, {})

    def test_deterministic_between_engines(self):
        engine1 = AttestationEngine(self.contracts)
        engine1.seal()
        engine2 = AttestationEngine(self.contracts)
        engine2.seal()
        self.assertEqual(engine1.attestation, engine2.attestation)
        self.assertEqual(
            engine1.master_attestation_hash,
            engine2.master_attestation_hash,
        )


if __name__ == "__main__":
    unittest.main()
