# Aurora MCP SDK validation matrix

This directory contains an isolated compatibility and security validation harness for the recovered Aurora read-only MCP bridge v1.0.1. It does not replace the production bridge, change Android/Termux, expose the service beyond IPv4 loopback inside the CI runner, or require secrets.

## Version strategy

- `1.30.1` is retained as a compatibility comparison for the fixes released after `1.30.0`.
- `1.32.2` is the primary candidate in the maintained SDK 1.x line for this validation. This is not automatic production approval; the bridge's low-level `Server` usage and HTTP transport limits still require review.
- SDK 2.x is intentionally excluded because it is a separate package-family migration exercise.

## What CI checks

The workflow uses Ubuntu, Node.js 22 and the official npm registry. For each exact SDK version it:

1. records registry metadata (`dist.tarball` and `dist.integrity`);
2. installs the exact SDK with lifecycle scripts disabled;
3. removes `node_modules` and performs a clean `npm ci --ignore-scripts` from the generated lockfile;
4. checks the installed SDK and `zod` peer dependency;
5. runs real MCP Client/Server SDK integration against the SHA-256-pinned v1.0.1 STDIO server;
6. checks Bearer authentication, Host/Origin rejection, the exact two-tool allowlist, six synthetic project fixtures, evidence reading, sensitive-path denial, shell-tool denial, missing-file failure, unknown-session rejection, session release, upstream tool-removal fail-closed behavior and loopback-only binding;
7. sends an oversized chunked HTTP body and asserts it is rejected;
8. runs `npm audit signatures` and records hashes for the package manifest, lockfile, bridge sources and baseline server.

The six project directories and sample `CHANGELOG.md` are synthetic, created in the CI runner's temporary HOME. No real repository contents or user credentials are used.

## Run locally

On an isolated Linux host with Node.js 22, npm 10+ and access to `https://registry.npmjs.org/`:

```bash
AURORA_MATRIX_WORK="$PWD/.matrix-work" bash run-sdk-matrix.sh
```

The script writes logs and evidence under `.matrix-work/`. It does not use or modify the Android environment.

## Security posture

- CI token permissions: `contents: read` only.
- No GitHub secrets or npm credentials are required.
- `npm install` and `npm ci` both use `--ignore-scripts`.
- The HTTP test bridge binds exclusively to `127.0.0.1` with a random per-process Bearer token.
- The copied upstream server must match SHA-256 `f2468deedd188b6040801993963a48cc47a4fbaec05b89f56ef9a05a6af403c9` before tests start.
- SDK integration success is not equivalent to deployment approval; actual device/network operation remains a separate acceptance gate.
