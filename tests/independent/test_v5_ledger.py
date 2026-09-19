"""V5 — independent reconstruction of the executable evidence chain."""
from __future__ import annotations

import hashlib
import json

from TUU.attestation_ledger import AttestationLedger, canonical_event_bytes


def independent_digest(previous_hash: str, event: dict) -> str:
    canonical = json.dumps(
        event,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(previous_hash.encode("ascii") + canonical).hexdigest()


def test_ledger_chain_is_reconstructable_independently() -> None:
    ledger = AttestationLedger()
    ledger.append({"event": "authorized", "job_id": "job-001", "score": 0.88})
    ledger.append({"event": "executed", "job_id": "job-001", "returncode": 0})

    assert ledger.verify()
    previous = ledger.GENESIS
    for sequence, entry in enumerate(ledger.entries):
        assert entry.sequence == sequence
        assert entry.previous_hash == previous
        assert entry.event_hash == independent_digest(previous, dict(entry.event))
        previous = entry.event_hash
    assert canonical_event_bytes({"b": 2, "a": 1}) == b'{"a":1,"b":2}'


def test_ledger_detects_tampering() -> None:
    ledger = AttestationLedger()
    ledger.append({"event": "authorized", "job_id": "job-001"})
    ledger.append({"event": "executed", "job_id": "job-001", "returncode": 0})
    original = ledger._entries[0]
    ledger._entries[0] = type(original)(
        sequence=original.sequence,
        previous_hash=original.previous_hash,
        event={**original.event, "job_id": "tampered"},
        event_hash=original.event_hash,
    )
    assert not ledger.verify()
