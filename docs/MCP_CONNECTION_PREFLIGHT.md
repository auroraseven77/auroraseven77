# Aurora MCP connection preflight (read-only)

## Purpose

This preflight distinguishes **connector availability** from **device reachability**. The connected GitHub integration can access the repository, but that does not establish a route to the Android/Termux MCP server. A local 127.0.0.1 endpoint belongs to the device on which the client runs; a ChatGPT-hosted connector cannot treat the user's Android loopback address as its own.

## Run on Termux

From a clone of this repository, run:

    python3 scripts/aurora_mcp_preflight.py

The probe sends only bounded HTTP GET requests to http://127.0.0.1:8787/healthz and /health. It prints status codes and exception **types**, never response bodies or headers; it does not read tokens, launch processes, write files, follow redirects, or call MCP tools. It exits 0 only if at least one health path returns HTTP 2xx. A nonzero exit is diagnostic, not proof the stdio server is broken.

For a broader Android-compatible diagnostic of listeners, best-effort process names, and the known local directories, run:

    bash scripts/aurora_mcp_termux_diagnostic.sh

This script uses `ps -A` rather than GNU-specific `ps -o PID,COMM`, requires no `sed`, and does not install packages or start/stop services. It displays candidate file names only (not file contents) and performs the same bounded loopback HTTP GET checks. It captures listener-command exit/output and flags typical Android netlink/permission errors as `INCONCLUSIVE`. A header-only process table is also `INCONCLUSIVE`; a process list with no matching command names is explicitly not treated as proof of absence.

An alternate local loopback port may be supplied explicitly to the Python preflight:

    python3 scripts/aurora_mcp_preflight.py --host 127.0.0.1 --port 8787 --timeout 2

The tool refuses non-loopback hosts by design. It does not scan ports or probe public hosts. `localhost` is canonicalized to `127.0.0.1`. IPv6 loopback (for example, `::1`) is passed to Python's HTTP client as a raw socket address; the client formats the HTTP `Host` header with brackets as required. Brackets must not be injected into the socket hostname itself.

## Interpret results

- `HEALTH_REACHABLE`: a local HTTP health route returned 2xx. This is **not** MCP protocol-version negotiation, server discovery, or `tools/list` validation.
- `HTTP_REACHABLE_NO_HEALTH_SUCCESS`: a process answered HTTP but neither known path returned 2xx; inspect the configured route and transport.
- `NOT_CONNECTED`: neither health path returned an HTTP response. Check whether the intended HTTP bridge is running locally.
- `NOT_TESTED_BY_HTTP_PROBE` for stdio: expected. Stdio servers communicate over stdin/stdout and cannot be verified using HTTP GET.
- `listener_state=INCONCLUSIVE`: `ss` failed or the output indicated OS/socket permission restrictions. Empty rows after a netlink error must not be treated as proof that the device has no listener.
- `process_state=INCONCLUSIVE`: the process command failed or returned no visible data rows.
- `process_state=NO_RELEVANT_NAME_MATCH`: the command returned rows but no candidate names matched. This is not proof of absence because Android may restrict process visibility and a server may use an unexpected command name.

## Separate MCP transport paths

1. **Local stdio** (for example, a Node.js entry point): the configured MCP host must launch the exact, reviewed command with a scoped working directory and environment. Use a protocol-version-aware client: the current 2026-07-28 protocol uses `server/discover` and per-request `_meta`; legacy protocols through 2025-11-25 use `initialize` followed by `notifications/initialized`. A dual-era client should probe `server/discover` first, then follow the version-negotiation and legacy-fallback rules in the official specification. After protocol negotiation, validate `tools/list`, schemas, and one harmless allowlisted read-only call before claiming end-to-end connectivity. This preflight deliberately does not execute local server code.
2. **HTTP bridge**: first prove the local health route, then use a trusted client to negotiate the protocol era and validate `tools/list`. For modern Streamable HTTP requests, the protocol-version metadata and `MCP-Protocol-Version` header must agree. ChatGPT access requires an explicitly configured, authorized reachable MCP endpoint supported by the active integration; a local port alone is not such a route.
3. **Remote tunnel**: do not expose an unauthenticated endpoint publicly. Require HTTPS, authentication, a narrow tool allowlist, bounded request sizes/timeouts, audit receipts, default-deny behavior, and human approval for writes. Do not paste tokens into chat or audit output.

## Current evidence boundary

The Termux transcript at **2026-10-26 17:36:42–17:36:43 UTC** showed:

- `ss -ltn` printed `Cannot open netlink socket: Permission denied`, followed by a header but no listener rows. Listener visibility is therefore **INCONCLUSIVE**, not verified empty.
- `ps -A` displayed only its header. Process visibility is **INCONCLUSIVE**; no process-absence claim is justified.
- The two HTTP GETs to `127.0.0.1:8787/healthz` and `/health` both returned `ConnectionRefusedError`. That is direct evidence that the HTTP target refused connection at that timestamp.
- The diagnostic found both known source directories and listed filenames only. It did not read source or logs.

A refused HTTP connection does not rule out a stdio MCP server. No MCP version discovery, legacy initialization, `tools/list`, or read-only tool call was performed by this diagnostic. Follow the version-aware checklist in [MCP protocol-era readiness](MCP_PROTOCOL_ERA_READINESS.md) when the exact configured entry point has been reviewed.

## Acceptance tests

- Reject non-loopback host, invalid port, and unbounded timeout before networking.
- Canonicalize `localhost` to numeric IPv4 loopback and use raw IPv6 loopback for socket connections.
- Issue only the two documented HTTP GET requests.
- Bound response-body consumption and never disclose response bodies or request headers.
- Distinguish HTTP health from protocol-era negotiation, tool discovery, and stdio reachability.
- Interpret netlink/permission errors and header-only process output as inconclusive.
- Use test doubles for shell diagnostics; automated tests must not require an active HTTP server.
- No port scan, MCP tool invocation, server launch, credential access, persistence, or writes.
- Termux shell diagnostic remains compatible without `sed` and does not assume GNU-style `ps -o`.
