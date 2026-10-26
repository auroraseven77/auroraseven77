# Aurora MCP protocol-era readiness audit

**Reference checked:** 2026-10-26  
**Purpose:** plan a valid, bounded MCP protocol test without launching an unknown local server or treating an HTTP health response as a protocol result.

## Why the test is version-aware

The official MCP specification currently identifies **2026-07-28** as its current protocol version. It introduces a modern, stateless request model. The legacy protocol family comprises revisions through **2025-11-25**, which use the initialization handshake. Implementations may support either family or both.

A client that assumes every server requires `initialize` can misclassify a modern server. Conversely, a modern-only request sent to a legacy implementation may fail. The transport (stdio vs. Streamable HTTP) does not, by itself, identify the protocol era.

## Modern protocol — 2026-07-28

- Use `server/discover` to retrieve `supportedVersions`, server capabilities, and identity before issuing other requests when performing explicit compatibility discovery. Servers MUST implement this method; clients MAY call it but can also negotiate inline by handling an `UnsupportedProtocolVersionError`.
- Choose a protocol version the server supports. Modern requests carry `_meta.io.modelcontextprotocol/protocolVersion` and `_meta.io.modelcontextprotocol/clientCapabilities`; clients SHOULD also identify themselves through `_meta.io.modelcontextprotocol/clientInfo`.
- After discovery, call `tools/list` with the same required modern metadata and validate the response against the modern schema. Do not assume the legacy response schema or an `initialize` result.
- In Streamable HTTP, the `MCP-Protocol-Version` header must match the protocol version in request `_meta`.

## Legacy protocol — 2025-11-25 and earlier

- The client sends `initialize` with the desired protocol version, client capabilities, and client information.
- The client validates the negotiated server result, then sends `notifications/initialized`.
- The client can then call `tools/list` and validate tool names and input schemas using the schema for that legacy revision.

## Dual-era clients

For a client that supports both protocol families:

1. Send a bounded `server/discover` request first, using the modern metadata envelope.
2. If a valid discovery result is returned, select a mutually supported version and continue with modern per-request metadata.
3. If the server returns a recognized modern `UnsupportedProtocolVersionError`, select a version from its supported list or report an incompatibility. Do **not** switch to `initialize` merely because a modern server does not support the client's preferred version.
4. If the probe returns another error or times out, follow the official backward-compatibility rules to determine whether the implementation is legacy; only then use the legacy initialization flow. Do not key the fallback solely to one error code.

See the official [version negotiation and backward-compatibility rules](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/basic/versioning.mdx).

## Stdio wire integrity

MCP stdio uses one newline-delimited JSON-RPC message per line. The server MUST send only valid MCP messages on stdout; logging may go to stderr. Extra banners, debug output, or ordinary application logs on stdout can corrupt protocol framing.

Reference: [official stdio transport specification](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/basic/transports/stdio.mdx).

## Acceptance states — do not collapse them

- `DISCOVERED`: a local file/configuration or server candidate is listed.
- `HTTP_REACHABLE`: the HTTP transport answers.
- `HEALTH_REACHABLE`: a documented health route returns success.
- `PROTOCOL_VERSION_DISCOVERED`: `server/discover` returned a valid modern discovery result.
- `LEGACY_INITIALIZED`: the legacy initialize exchange and `notifications/initialized` completed.
- `TOOLS_DISCOVERED`: `tools/list` returned a valid response under the negotiated protocol era.
- `READ_ONLY_CALL_VERIFIED`: a known, allowlisted read-only tool was called through the authorized client and the result was checked.
- `NOT_TESTED`, `INCONCLUSIVE`, `BLOCKED`, or `NOT_CONNECTED`: no end-to-end result has been established.

A health endpoint or open port is not an MCP protocol check. A successful discovery or tools list is not proof that a tool call is authorized or side-effect-free. A tool description or annotation is untrusted data until the implementation and policy are reviewed.

## Safe application to Aurora/Termux

The current device transcripts establish refused HTTP connections for the two known loopback health routes and inconclusive listener visibility due to Android netlink permissions. They do **not** establish whether any stdio MCP entry point is active. The current inventory lists several candidate files but does not establish which one is the configured and authorized server entry point.

Therefore this audit does not run any candidate file or install dependencies. Before an actual protocol test:

- identify the exact MCP host configuration and entry-point command, without printing environment values or credentials;
- review the entry point and tool allowlist; do not choose a file simply because its name contains `mcp` or `readonly`;
- use an explicitly configured client with finite timeouts, bounded output, and stdout/stderr separation;
- enumerate the exposed tool names and schemas before any call; choose only an understood, harmless read-only operation for an end-to-end test;
- require human approval for writes, execution, service changes, public exposure, or configuration changes.

## Official references

- [MCP current versioning specification — 2026-07-28](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/basic/versioning.mdx)
- [MCP server discovery — 2026-07-28](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/server/discover.mdx)
- [MCP tools — 2026-07-28](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/server/tools.mdx)
- [MCP stdio transport — 2026-07-28](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/basic/transports/stdio.mdx)
- [MCP version changelog](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/docs/specification/2026-07-28/changelog.mdx)
