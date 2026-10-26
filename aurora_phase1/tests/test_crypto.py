"""Testes de aurora_phase1.core.crypto (Bloco 1)."""
import unittest

from aurora_phase1.core.crypto import (
    GENESIS_PREV_HASH,
    canonical_json,
    hash_bytes,
    hash_object,
    hash_string,
)


class TestCrypto(unittest.TestCase):

    def test_canonical_json_sorts_keys(self):
        self.assertEqual(
            canonical_json({"b": 1, "a": 2}),
            '{"a":2,"b":1}',
        )

    def test_canonical_json_no_spaces(self):
        self.assertEqual(canonical_json({"a": 1}), '{"a":1}')

    def test_hash_object_is_deterministic(self):
        h1 = hash_object({"a": 1, "b": 2})
        h2 = hash_object({"b": 2, "a": 1})
        self.assertEqual(h1, h2)

    def test_hash_object_differentiates(self):
        self.assertNotEqual(
            hash_object({"a": 1}),
            hash_object({"a": 2}),
        )

    def test_hash_object_returns_64_hex(self):
        h = hash_object({"x": 1})
        self.assertEqual(len(h), 64)
        int(h, 16)  # raises if not hex

    def test_hash_string(self):
        h = hash_string("hello")
        self.assertEqual(len(h), 64)

    def test_hash_bytes(self):
        h = hash_bytes(b"hello")
        self.assertEqual(len(h), 64)

    def test_genesis_prev_hash(self):
        self.assertEqual(GENESIS_PREV_HASH, "0" * 64)


if __name__ == "__main__":
    unittest.main()
