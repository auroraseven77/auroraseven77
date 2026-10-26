from __future__ import annotations

import http.client

import pytest

from scripts.aurora_mcp_preflight import probe_health, validate_target


class FakeResponse:
    def __init__(self, status: int, body: bytes = b"private-response-body"):
        self.status = status
        self._body = body

    def read(self, amount: int = -1) -> bytes:
        return self._body[:amount]


class FakeConnection:
    outcomes: list[int | OSError] = []
    requests: list[tuple[str, str]] = []

    def __init__(self, host: str, port: int, timeout: float):
        self.host, self.port, self.timeout = host, port, timeout

    def request(self, method: str, path: str, headers: dict[str, str]) -> None:
        self.requests.append((method, path))

    def getresponse(self) -> FakeResponse:
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, OSError):
            raise outcome
        return FakeResponse(outcome)

    def close(self) -> None:
        pass


def test_rejects_remote_host_before_network_activity():
    with pytest.raises(ValueError, match="loopback"):
        validate_target("example.com", 8787, 2)


@pytest.mark.parametrize("port", [0, -1, 65536, True, "8787"])
def test_rejects_invalid_port(port):
    with pytest.raises(ValueError, match="port"):
        validate_target("127.0.0.1", port, 2)


@pytest.mark.parametrize("timeout", [0, -1, 10.1, True])
def test_rejects_invalid_timeout(timeout):
    with pytest.raises(ValueError, match="timeout"):
        validate_target("127.0.0.1", 8787, timeout)


def test_probe_only_issues_bounded_health_gets_and_hides_body(monkeypatch):
    FakeConnection.outcomes = [200, 404]
    FakeConnection.requests = []
    monkeypatch.setattr(http.client, "HTTPConnection", FakeConnection)

    report = probe_health()

    assert report["state"] == "HEALTH_REACHABLE"
    assert report["probes"][0]["http_status"] == 200
    assert report["probes"][1]["http_status"] == 404
    assert FakeConnection.requests == [("GET", "/healthz"), ("GET", "/health")]
    assert "private-response-body" not in str(report)
    assert report["stdio_mcp"] == "NOT_TESTED_BY_HTTP_PROBE"


def test_refused_connection_is_reported_as_not_connected(monkeypatch):
    FakeConnection.outcomes = [ConnectionRefusedError("refused"), ConnectionRefusedError("refused")]
    FakeConnection.requests = []
    monkeypatch.setattr(http.client, "HTTPConnection", FakeConnection)

    report = probe_health()

    assert report["state"] == "NOT_CONNECTED"
    assert all(item["state"] == "NOT_CONNECTED" for item in report["probes"])
