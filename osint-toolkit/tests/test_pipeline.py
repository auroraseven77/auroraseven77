import json
from pathlib import Path
from unittest.mock import patch
from osint_toolkit import pipeline


def test_dns_pipeline_writes_normalized(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with patch("osint_toolkit.pipeline.dns.collect", return_value=[]):
        observations = pipeline.run("example.com", ["example.com"], out_path="obs.jsonl", evidence_root="evidence")
    assert observations == []
    assert (tmp_path / "obs.jsonl").exists()
