"""V5 — executable attestation/hash-chain evidence.

This test intentionally fails closed when the repository contains only a
specification and no executable ledger implementation.
"""
from __future__ import annotations

from pathlib import Path


def test_executable_ledger_implementation_exists() -> None:
    source_files = [
        path
        for path in Path(".").rglob("*.py")
        if ".git" not in path.parts and "tests" not in path.parts
    ]

    candidates = []
    for path in source_files:
        text = path.read_text(encoding="utf-8", errors="ignore").lower()
        if "ledger" in text and "sha256" in text:
            candidates.append(path)

    assert candidates, (
        "V5 FAIL: no executable ledger implementation containing both "
        "ledger semantics and SHA-256 chaining was found. The policy document "
        "is a specification, not runtime evidence; hash-chain reconstruction "
        "cannot be honestly marked PASS until an executable ledger exists."
    )
