# Observability contract (proposal; no runtime instrumentation added)

## Purpose

Define the minimum structured telemetry contract for the passive OSINT Toolkit without adding background telemetry, remote reporting, or network side effects.

## Event fields

Every future structured event should contain:

- `schema_version`: stable schema identifier such as `osint-toolkit-event/1.0`.
- `timestamp`: RFC 3339 timestamp with timezone.
- `event`: bounded event name, for example `collector.started`, `collector.completed`, `collector.failed`, `policy.denied`, `evidence.persisted`.
- `run_id`: local correlation identifier; never a credential.
- `collector`: allow-listed module name.
- `target_ref`: optional normalized target or a local redacted reference according to operator policy.
- `status`: `ok`, `error`, `skipped`, or `denied`.
- `duration_ms`: non-negative duration where measured.
- `evidence_sha256`: optional full digest, never raw evidence content.
- `error_code`: stable, non-sensitive classification; do not log arbitrary exception payloads by default.

## Privacy and writes

- Default output is local stderr or a caller-selected local destination.
- No remote telemetry, automatic upload, or analytics endpoint.
- Never log secrets, auth headers, cookies, request bodies, local home paths, or unredacted evidence.
- Logs alone are not proof of source truth.
- No persistent database or SQLite WAL changes under this contract.

## Acceptance criteria

1. Unit tests validate schema, timezone awareness, bounded event names, duration bounds, and redaction.
2. A failed collector emits a stable error code and preserves outcome semantics.
3. Run IDs correlate events without changing evidence identity.
4. CLI stays quiet unless requested; telemetry introduces no external requests.
5. Documentation remains marked as proposal until implementation and tests exist.

## Status

`PARTIAL / CONTRACT_ONLY`. This PR does not implement structured logging or runtime instrumentation.
