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

For a bounded, read-only inventory of the known local source folders, run:

    bash scripts/aurora_mcp_source_inventory.sh

The inventory hashes only top-level regular `.js`, `.cjs`, `.mjs`, and `.py` files plus the bounded `package.json` manifest, with a 4 MiB per-file and 64-file per-root limit. For code files it also reports counts and up to eight line numbers per category for fixed heuristic markers covering process execution, network clients/listeners, filesystem mutation, environment/credential access, dynamic code, MCP protocol/tool registration, and authorization/approval. A `manual_review_suggested` flag highlights selected categories for human inspection, but is not a vulnerability verdict, proof of runtime behavior, or an execution decision. Line-number arrays are truncated when a category matches more than eight lines. Source files are read for hashing and heuristic matching but their contents are never printed. `package.json` is read within the size limit to compute its digest and parse an allowlist of metadata/script names; package script command values are never emitted or executed. The tool does not read logs, `.env` files, backups, lockfiles, or JSONL ledgers, does not access the network or write files, and does not start or stop project/service processes. It reports names, sizes, SHA-256 digests, heuristic marker counts/locations, an allowlist of manifest metadata, and its limits. Share the output only after reviewing it for local path/file-name sensitivity.

An alternate local loopback port may be supplied explicitly to the Python preflight:

    python3 scripts/aurora_mcp_preflight.py --host 127.0.0.1 --port 8787 --timeout 2

The tool refuses non-loopback hosts by design. It does not scan ports or probe public hosts. `localhost` is canonicalized to `127.0.0.1`. IPv6 loopback (for example, `::1`) is passed to Python's HTTP client as a raw socket address; the client formats the HTTP `Host` header with brackets as required. Brackets must not be injected into the socket hostname itself.

## Interpret results

- `HEALTH_REACHABLE`: a local HTTP health route returned 2xx. This is **not** an MCP initialize/tool-list handshake.
- `HTTP_REACHABLE_NO_HEALTH_SUCCESS`: a process answered HTTP but neither known path returned 2xx; inspect the configured route and transport.
- `NOT_CONNECTED`: neither health path returned an HTTP response. Check whether the intended HTTP bridge is running locally.
- `NOT_TESTED_BY_HTTP_PROBE` for stdio: expected. Stdio servers communicate over stdin/stdout and cannot be verified using HTTP GET.
- `listener_state=INCONCLUSIVE`: `ss` failed or the output indicated OS/socket permission restrictions. Empty rows after a netlink error must not be treated as proof that the device has no listener.
- `process_state=INCONCLUSIVE`: the process command failed or returned no visible data rows.
- `process_state=NO_RELEVANT_NAME_MATCH`: the command returned rows but no candidate names matched. This is not proof of absence because Android may restrict process visibility and a server may use an unexpected command name.

## Separate MCP transport paths

1. **Local stdio** (for example, a node entry point): the MCP host must launch that exact command with a scoped working directory and environment. This preflight deliberately does not execute local server code. A host's initialize and tools/list results are needed before claiming the stdio server works.
2. **HTTP bridge**: first prove the local health route, then test the MCP protocol separately from a trusted client. ChatGPT access requires an explicitly configured, authorized reachable MCP endpoint supported by the active integration; a local port alone is not such a route.
3. **Remote tunnel**: do not expose an unauthenticated endpoint publicly. Require HTTPS, authentication, a narrow tool allowlist, bounded request sizes/timeouts, audit receipts, default-deny behavior, and human approval for writes. Do not paste tokens into chat or audit output.

## Current evidence boundary

Two Termux transcripts were supplied on **2026-10-26**:

- **17:36:42–17:36:43 UTC:** `ss -ltn` printed `Cannot open netlink socket: Permission denied`, followed by a header but no listener rows. Listener visibility was **INCONCLUSIVE**, not verified empty. `ps -A` displayed only its header in that run, so process visibility was **INCONCLUSIVE**.
- **17:52:20–17:52:21 UTC:** `ss -ltn` again reported a netlink permission error, so listener visibility remained **INCONCLUSIVE**. The script emitted `NO_RELEVANT_NAME_MATCH`; by its logic, that means at least one visible data row was parsed but none matched the candidate names `node|python|mcp|aurora`. The script did not print unrelated process rows; this is not proof that the MCP process is absent.
- Both runs reported `ConnectionRefusedError` for `127.0.0.1:8787/healthz` and `/health`. The later result is timestamped `2026-10-26T17:52:21.356942+00:00`. This is direct evidence that those HTTP connections were refused at that time, not evidence about stdio transport.
- The runs listed filenames in the two known directories but did not read source files or logs. The latest inventory shows `mcp-aurora` and `mcp-aurora-server` are not detected as Git worktrees by that check; no claim is made about their provenance.

A refused HTTP connection does not rule out a stdio MCP server. No MCP initialize/tools/list handshake was performed. The separate source inventory tool hashes a bounded allowlist of top-level code files and prints only digests and selected package metadata; it does not establish server execution or MCP compatibility.

## Acceptance tests

- Reject non-loopback host, invalid port, and unbounded timeout before networking.
- Canonicalize `localhost` to numeric IPv4 loopback and use raw IPv6 loopback for socket connections.
- Issue only the two documented HTTP GET requests.
- Bound response-body consumption and never disclose response bodies or request headers.
- Distinguish HTTP health from MCP handshake and from stdio reachability.
- Interpret netlink/permission errors and header-only process output as inconclusive.
- Use test doubles for shell diagnostics; automated tests must not require an active HTTP server.
- No port scan, MCP tool invocation, server launch, credential access, persistence, or writes.
- Termux shell diagnostic remains compatible without `sed` and does not assume GNU-style `ps -o`.
