#!/usr/bin/env python3
"""Read-only loopback health probe for the known Aurora MCP HTTP bridge.

This does not launch processes, send MCP tools/calls, follow redirects, read
credentials, or write files. It checks HTTP health paths only; stdio MCP
servers are not reachable through an HTTP health probe.
"""
from __future__ import annotations

import argparse
import http.client
import ipaddress
import json
import socket
import sys
from datetime import datetime, timezone
from typing import Any

HEALTH_PATHS = ("/healthz", "/health")
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787
DEFAULT_TIMEOUT = 2.0


def validate_target(host: str, port: int, timeout: float) -> None:
    """Restrict the probe to an explicit loopback target."""
    if not isinstance(host, str) or not host.strip():
        raise ValueError("host must be a non-empty loopback address")
    normalized = host.strip().lower()
    try:
        loopback = normalized == "localhost" or ipaddress.ip_address(normalized).is_loopback
    except ValueError:
        loopback = False
    if not loopback:
        raise ValueError("only loopback hosts are allowed; remote probing is disabled")
    if isinstance(port, bool) or not isinstance(port, int) or not 1 <= port <= 65535:
        raise ValueError("port must be an integer from 1 to 65535")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0.1 <= timeout <= 10:
        raise ValueError("timeout must be between 0.1 and 10 seconds")


def probe_health(host: str = DEFAULT_HOST, port: int = DEFAULT_PORT,
                 timeout: float = DEFAULT_TIMEOUT) -> dict[str, Any]:
    """Probe only /healthz and /health; never return response bodies or headers."""
    validate_target(host, port, timeout)
    results: list[dict[str, Any]] = []
    for path in HEALTH_PATHS:
        connection = http.client.HTTPConnection(host, port, timeout=timeout)
        try:
            connection.request(
                "GET",
                path,
                headers={"Accept": "application/json, text/plain", "Connection": "close"},
            )
            response = connection.getresponse()
            # Consume at most 1 KiB to keep the request bounded; never disclose the body.
            response.read(1024)
            results.append({"path": path, "http_status": response.status, "state": "HTTP_RESPONSE"})
        except (OSError, http.client.HTTPException, socket.timeout) as exc:
            results.append({"path": path, "http_status": None, "state": "NOT_CONNECTED",
                            "error_type": type(exc).__name__})
        finally:
            connection.close()

    statuses = [item["http_status"] for item in results if item["http_status"] is not None]
    if any(status is not None and 200 <= status < 300 for status in statuses):
        state = "HEALTH_REACHABLE"
    elif statuses:
        state = "HTTP_REACHABLE_NO_HEALTH_SUCCESS"
    else:
        state = "NOT_CONNECTED"
    return {
        "schema_version": "1.0",
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "target": {"host": host, "port": port},
        "state": state,
        "probes": results,
        "stdio_mcp": "NOT_TESTED_BY_HTTP_PROBE",
        "side_effects": "HTTP GET only; no files, process launch, credentials, or response bodies",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default=DEFAULT_HOST, help="loopback address only (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help="local HTTP bridge port (default: 8787)")
    parser.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT,
                        help="per-request timeout in seconds, 0.1..10 (default: 2)")
    args = parser.parse_args(argv)
    try:
        report = probe_health(args.host, args.port, args.timeout)
    except ValueError as exc:
        print(json.dumps({"state": "INVALID_TARGET", "error": str(exc)}, sort_keys=True))
        return 2
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["state"] == "HEALTH_REACHABLE" else 1


if __name__ == "__main__":
    raise SystemExit(main())
