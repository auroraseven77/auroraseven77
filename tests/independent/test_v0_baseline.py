"""V0 — immutable baseline identity."""
from __future__ import annotations

import subprocess

BASELINE = "5d56b6eaff29d2bcb98efff6b7f1fad1f31ff6df"


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], text=True, stderr=subprocess.STDOUT
    ).strip()


def test_reference_baseline_exists_and_is_ancestor() -> None:
    assert git("cat-file", "-t", BASELINE) == "commit"
    assert git("merge-base", "--is-ancestor", BASELINE, "HEAD") == ""
