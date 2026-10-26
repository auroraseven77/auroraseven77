# Aurora/TUU Evidence Ledger adapter — integration contract only

**Status:** `DESIGN_ONLY`; no production database, user device, Snowflake, or live ledger was accessed.

## Boundary

The OSINT Toolkit may offer a future export adapter from normalized `Observation` records to the Aurora Evidence Ledger. The adapter must be append-only, offline by default, and must not grant authorization to collect or execute commands.

## Proposed mapping

| OSINT concept | Ledger concept | Rule |
|---|---|---|
| Collection request accepted by explicit allow-list | `DECLARADO` claim + execution receipt | Record scope and policy version; no secret values |
| Collector process run | `EXECUTADO` receipt | Record run ID, bounded operation/test ID, timestamps, exit code |
| Observation plus retained source artifact | `OBSERVADO` evidence | Hash the sanitized artifact and preserve its source reference |
| Correlation/risk report | `AVALIADO` assessment | Explicitly label risk as heuristic; does not prove source truth |
| Distinct source | additional evidence reference | Distinct IDs alone do not prove real-world source independence |

## Required safeguards

1. Validate schema and ledger version before opening files.
2. Verify existing ledgers read-only; only append with the approved writer.
3. Never rewrite or rehash historical events to repair an old artifact mismatch.
4. Validate every source artifact SHA-256 before recording its reference.
5. Fail closed for malformed destination, unknown fields, duplicate event IDs, or broken chain.
6. Never point at `~/tuu/data/tuu.db` or a live ledger until a separate integration gate, backup/recovery plan, and copy-based test are reviewed.
7. No network connector, webhook, database writes, or Snowflake query is part of this proposal.

## Acceptance criteria before implementation

- A schema-level mapping test with only synthetic observations.
- Round-trip verification on a disposable ledger copy.
- Failure tests for tampered artifacts, malformed observation, broken chain, and duplicate IDs.
- Reproducible evidence manifests and hashes.
- Rollback is limited to deleting a disposable test directory, never modifying source evidence.

This document is a contract proposal, not an implemented integration.
