"""Append-only evidence ledger for TUU v2.1."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Mapping


def canonical_event_bytes(event: Mapping[str, Any]) -> bytes:
    """Deterministic JSON bytes for the current ledger evidence boundary."""
    try:
        payload = json.dumps(
            dict(event),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise ValueError("event is not canonicalizable JSON") from exc
    return payload.encode("utf-8")


def event_digest(previous_hash: str, event: Mapping[str, Any]) -> str:
    return hashlib.sha256(
        previous_hash.encode("ascii") + canonical_event_bytes(event)
    ).hexdigest()


@dataclass(frozen=True)
class LedgerEntry:
    sequence: int
    previous_hash: str
    event: Mapping[str, Any]
    event_hash: str


class AttestationLedger:
    """Append-only hash chain with deterministic independent verification."""

    GENESIS = "0" * 64

    def __init__(self) -> None:
        self._entries: list[LedgerEntry] = []

    @property
    def entries(self) -> tuple[LedgerEntry, ...]:
        return tuple(self._entries)

    def append(self, event: Mapping[str, Any]) -> LedgerEntry:
        frozen_event = json.loads(canonical_event_bytes(event).decode("utf-8"))
        previous_hash = self._entries[-1].event_hash if self._entries else self.GENESIS
        entry_hash = event_digest(previous_hash, frozen_event)
        entry = LedgerEntry(
            sequence=len(self._entries),
            previous_hash=previous_hash,
            event=frozen_event,
            event_hash=entry_hash,
        )
        self._entries.append(entry)
        return entry

    def verify(self) -> bool:
        previous = self.GENESIS
        for expected_sequence, entry in enumerate(self._entries):
            if entry.sequence != expected_sequence:
                return False
            if entry.previous_hash != previous:
                return False
            if entry.event_hash != event_digest(previous, entry.event):
                return False
            previous = entry.event_hash
        return True
