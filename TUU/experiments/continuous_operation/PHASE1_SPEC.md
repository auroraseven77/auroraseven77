# TUU Continuous-Operation Prototype — Phase 1

Status: IMPLEMENTATION PLAN / NOT YET EXECUTED
Branch: feat/tuu-continuity-prototype
Scope: isolated persistence, provenance, recovery, and feedback evaluation.
Non-goals: changing B1 execution semantics, claiming autonomy/consciousness, or making claims about Navier–Stokes proof status.

## Existing components inspected
- `TUU/tuu_core.py`: orchestration and intent lifecycle.
- `TUU/authorization.py`: immutable authorization context/decision and policy evaluation.
- `TUU/execution.py`: restricted command execution.
- `tests/test_tuu_lifecycle.py`: lifecycle integration tests.
- `aurora_phase1/cognitive_poc/belief_state.py`: immutable belief-state primitives.
- `aurora_phase1/cognitive_poc/belief_update.py`: belief transitions and provenance-related primitives.

These components exist in the inspected default-branch files; their end-to-end integration with cross-session persistence has not yet been demonstrated.

## Safety and change policy
1. Keep the prototype isolated from production execution and the B1 motor's normal path.
2. Do not persist credentials, environment secrets, or arbitrary command payloads.
3. Use a dedicated temporary directory/database in tests.
4. Fail closed on malformed records, hash mismatches, schema-version mismatches, or missing predecessor records.
5. Do not replay external side effects during recovery.
6. Do not change existing core behavior until prototype tests pass and a separate review approves integration.
7. Preserve the baseline and record commit SHAs for all test runs.

## Proposed record model
Each event is append-only and contains:
- schema_version
- event_id
- session_id
- sequence_number
- event_type
- timestamp_utc
- payload (allow-listed, JSON-compatible data only)
- previous_event_hash
- event_hash

The hash is computed over a canonical serialization of all defined fields except event_hash. Sequence numbers must be monotonic per stream. The first event uses an explicit genesis predecessor. Hash chaining detects accidental or unauthorized alteration; it does not by itself authenticate the writer or prove that the underlying claim is true.

## Minimal API to prototype
- append_event(record) -> immutable event reference
- verify_stream(stream) -> structured verification result
- load_latest_state(stream) -> state plus provenance and any detected gaps
- checkpoint_state(state, provenance) -> checkpoint reference
- restore_checkpoint(reference) -> restored state, without replaying external actions

The implementation should reuse existing primitives only after their serialization and compatibility contracts are verified. Avoid coupling to belief-update internals until their public interfaces are inspected.

## Experiment conditions
A. No persistent memory: fresh process, only task input.
B. Persistence only: same task with prior allow-listed records restored, no adaptive feedback.
C. Persistence + feedback: same persistence as B, plus a recorded correction rule or feedback item.
D. Persistence + feedback + explicit state reconstruction: C plus reconstruction of dependencies and uncertainty markers.

Keep task set, model/software versions, initial information, tool permissions, and evaluation rubric fixed. Record resource budgets and any unavoidable differences.

## Required tests
1. Append and reload an event across separate processes.
2. Reconstruct the same canonical state after restart.
3. Detect a modified payload or broken hash chain.
4. Detect missing sequence numbers and missing predecessor records.
5. Reject unsupported schema versions and malformed records.
6. Preserve contradiction/uncertainty markers rather than silently choosing one claim.
7. Confirm recovery does not execute or replay commands.
8. Confirm revoked permissions and secrets are not restored from old state.
9. Demonstrate that feedback changes a subsequent decision only through an explicit, recorded update.
10. Compare A/B/C/D using held-out tasks and predeclared scoring.

## Metrics
- factual recovery accuracy
- provenance completeness and correctness
- state reconstruction exact-match rate
- contradiction and gap detection recall
- invalid-record detection rate
- post-feedback error correction rate
- held-out task accuracy
- latency, storage growth, and failure recovery time

Report sample sizes, confidence intervals or uncertainty estimates, excluded runs, software versions, and limitations. Do not set universal pass thresholds until baseline variance and practical effect sizes are measured.

## Acceptance gates
Gate 1 — Persistence: events survive process restart and state reconstructs deterministically.
Gate 2 — Integrity: tampering, gaps, and schema violations are detected.
Gate 3 — Provenance: recovered claims link to source event IDs and uncertainty is preserved.
Gate 4 — Safe recovery: no external side effects are replayed and permissions are re-evaluated.
Gate 5 — Feedback: improvement is measured against B on held-out tasks, not inferred from examples.
Gate 6 — Integration: only after Gates 1–5 pass may a separate change propose connecting the prototype to the core lifecycle.

## Current limitations
This file is a protocol and implementation plan, not evidence that persistence or feedback has been implemented or tested. The next code change should be a small isolated event-store module plus unit tests, after checking project dependency and test conventions.
