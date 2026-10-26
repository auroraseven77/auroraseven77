# Aurora MCP connection preflight (read-only)

## Purpose

This preflight distinguishes **connector availability** from **device reachability**. The connected GitHub integration can access the repository, but that does not establish a route to the Android/Termux MCP server. A local 127.0.0.1 endpoint belongs to the device on which the client runs; a ChatGPT-hosted connector cannot treat the user's Android loopback address as its own.

## Run on Termux

From a clone of this repository, run:

    python3 scripts/aurora_mcp_preflight.py

The probe sends only bounded HTTP GET requests to http://127.0.0.1:8787/healthz and /health. It prints status codes and exception **types**, never response bodies or headers; it does not read tokens, launch processes, write files, follow redirects, or call MCP tools. It exits 0 only if at least one health path returns HTTP 2xx. A nonzero exit is diagnostic, not proof the stdio server is broken.

An alternate local loopback port may be supplied explicitly:

    python3 scripts/aurora_mcp_preflight.py --host 127.0.0.1 --port 8787 --timeout 2

The tool refuses non-loopback hosts by design. It does not scan ports or probe public hosts.

## Interpret results

- HEALTH_REACHABLE: a local HTTP health route returned 2xx. This is **not** an MCP initialize/tool-list handshake.
- HTTP_REACHABLE_NO_HEALTH_SUCCESS: a process answered HTTP but neither known path returned 2xx; inspect the configured route and transport.
- NOT_CONNECTED: neither health path returned an HTTP response. Check whether the intended HTTP bridge is running locally.
- NOT_TESTED_BY_HTTP_PROBE for stdio: expected. Stdio servers communicate over stdin/stdout and cannot be verified using HTTP GET.

## Separate MCP transport paths

1. **Local stdio** (for example, a node entry point): the MCP host must launch that exact command with a scoped working directory and environment. This preflight deliberately does not execute local server code. A host's initialize and tools/list results are needed before claiming the stdio server works.
2. **HTTP bridge**: first prove the local health route, then test the MCP protocol separately from a trusted client. ChatGPT access requires an explicitly configured, authorized reachable MCP endpoint supported by the active integration; a local port alone is not such a route.
3. **Remote tunnel**: do not expose an unauthenticated endpoint publicly. Require HTTPS, authentication, a narrow tool allowlist, bounded request sizes/timeouts, audit receipts, default-deny behavior, and human approval for writes. Do not paste tokens into chat or audit output.

## Current evidence boundary

A prior user-provided Termux transcript reported that 127.0.0.1:8787/healthz failed with connection refused and no listener was present at that time. This document does not claim that condition is still current. Re-run the probe on the device and share its sanitized JSON output to refresh the evidence.

## Acceptance tests

- Reject non-loopback host, invalid port, and unbounded timeout before networking.
- Issue only the two documented HTTP GET requests.
- Never disclose response bodies or request headers.
- Distinguish HTTP health from MCP handshake and from stdio reachability.
- No port scan, process launch, credentials access, persistence, or writes.
