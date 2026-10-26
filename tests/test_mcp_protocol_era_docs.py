from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PREFLIGHT_DOC = ROOT / "docs" / "MCP_CONNECTION_PREFLIGHT.md"
ERA_DOC = ROOT / "docs" / "MCP_PROTOCOL_ERA_READINESS.md"


def test_protocol_documentation_covers_modern_and_legacy_eras():
    doc = ERA_DOC.read_text(encoding="utf-8")
    assert "2026-07-28" in doc
    assert "server/discover" in doc
    assert "io.modelcontextprotocol/protocolVersion" in doc
    assert "io.modelcontextprotocol/clientCapabilities" in doc
    assert "tools/list" in doc
    assert "2025-11-25" in doc
    assert "notifications/initialized" in doc
    assert "Do **not** switch to `initialize`" in doc


def test_stdio_framing_and_no_unknown_local_execution_are_explicit():
    doc = ERA_DOC.read_text(encoding="utf-8")
    assert "newline-delimited JSON-RPC" in doc
    assert "stdout" in doc
    assert "does not run any candidate file" in doc
    assert "human approval" in doc


def test_health_probe_does_not_claim_protocol_validation():
    doc = PREFLIGHT_DOC.read_text(encoding="utf-8")
    assert "not** MCP protocol-version negotiation" in doc
    assert "No MCP version discovery, legacy initialization, `tools/list`" in doc
    assert "MCP_PROTOCOL_ERA_READINESS.md" in doc
