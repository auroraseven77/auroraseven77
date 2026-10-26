from __future__ import annotations

import http.client

import pytest

from scripts.aurora_mcp_preflight import probe_health, validate_target


class FakeResponse:
    def __init__(self, status: int, body: bytes = b"private-response-body"):
        self.status = status
        self._body = body
        self.read_limits: list[int] = []

    def read(self, amount: int = -1) -> bytes:
        self.read_limits.append(amount)
        return self._body[:amount]


class FakeConnection:
    outcomes: list[int | OSError] = []
    requests: list[tuple[str, str, dict[str, str]]] = []
    responses: list[FakeResponse] = []
    hosts: list[str] = []

    def __init__(self, host: str, port: int, timeout: float):
        self.host, self.port, self.timeout = host, port, timeout
        self.hosts.append(host)

    def request(self, method: str, path: str, headers: dict[str, str]) -> None:
        self.requests.append((method, path, dict(headers)))

    def getresponse(self) -> FakeResponse:
        outcome = self.outcomes.pop(0)
        if isinstance(outcome, OSError):
            raise outcome
        response = FakeResponse(outcome)
        self.responses.append(response)
        return response

    def close(self) -> None:
        pass


def reset_fake() -> None:
    FakeConnection.outcomes = []
    FakeConnection.requests = []
    FakeConnection.responses = []
    FakeConnection.hosts = []


def test_rejects_remote_host_before_network_activity():
    with pytest.raises(ValueError, match="loopback"):
        validate_target("example.com", 8787, 2)


@pytest.mark.parametrize("host", ["", "example.com", "192.0.2.1", "0.0.0.0", "::1%lo"])
def test_rejects_non_loopback_or_ambiguous_host(host):
    with pytest.raises(ValueError):
        validate_target(host, 8787, 2)


@pytest.mark.parametrize("port", [0, -1, 65536, True, "8787"])
def test_rejects_invalid_port(port):
    with pytest.raises(ValueError, match="port"):
        validate_target("127.0.0.1", port, 2)


@pytest.mark.parametrize("timeout", [0, -1, 10.1, True, float("nan"), float("inf")])
def test_rejects_invalid_timeout(timeout):
    with pytest.raises(ValueError, match="timeout"):
        validate_target("127.0.0.1", 8787, timeout)


def test_probe_only_issues_bounded_health_gets_and_hides_body(monkeypatch):
    reset_fake()
    FakeConnection.outcomes = [200, 404]
    monkeypatch.setattr(http.client, "HTTPConnection", FakeConnection)

    report = probe_health()

    assert report["state"] == "HEALTH_REACHABLE"
    assert report["probes"][0]["http_status"] == 200
    assert report["probes"][1]["http_status"] == 404
    assert [(method, path) for method, path, _ in FakeConnection.requests] == [
        ("GET", "/healthz"),
        ("GET", "/health"),
    ]
    assert all(headers == {
        "Accept": "application/json, text/plain",
        "Connection": "close",
    } for _, _, headers in FakeConnection.requests)
    assert all(response.read_limits == [1024] for response in FakeConnection.responses)
    assert "private-response-body" not in str(report)
    assert report["stdio_mcp"] == "NOT_TESTED_BY_HTTP_PROBE"


def test_localhost_is_canonicalized_to_numeric_loopback(monkeypatch):
    reset_fake()
    FakeConnection.outcomes = [200, 200]
    monkeypatch.setattr(http.client, "HTTPConnection", FakeConnection)

    report = probe_health(host=" LOCALHOST ")

    assert report["target"]["host"] == "127.0.0.1"
    assert FakeConnection.hosts == ["127.0.0.1", "127.0.0.1"]
    assert report["state"] == "HEALTH_REACHABLE"


def test_ipv6_loopback_is_bracketed_for_http_client(monkeypatch):
    reset_fake()
    FakeConnection.outcomes = [200, 200]
    monkeypatch.setattr(http.client, "HTTPConnection", FakeConnection)

    report = probe_health(host="::1")

    assert report["target"]["host"] == "::1"
    assert FakeConnection.hosts == ["[::1]", "[::1]"]
    assert report["state"] == "HEALTH_REACHABLE"


def test_refused_connection_is_reported_as_not_connected(monkeypatch):
    reset_fake()
    FakeConnection.outcomes = [
        ConnectionRefusedError("refused"),
        ConnectionRefusedError("refused"),
    ]
    monkeypatch.setattr(http.client, "HTTPConnection", FakeConnection)

    report = probe_health()

    assert report["state"] == "NOT_CONNECTED"
    assert all(item["state"] == "NOT_CONNECTED" for item in report["probes"])


def test_http_responses_without_success_are_not_reported_as_healthy(monkeypatch):
    reset_fake()
    FakeConnection.outcomes = [302, 503]
    monkeypatch.setattr(http.client, "HTTPConnection", FakeConnection)

    report = probe_health()

    assert report["state"] == "HTTP_REACHABLE_NO_HEALTH_SUCCESS"
    assert [item["http_status"] for item in report["probes"]] == [302, 503]
    assert len(FakeConnection.requests) == 2
