# OSINT Toolkit API reference (0.1.x)

This reference describes the current MVP surface. It is not a promise of long-term API stability before 1.0.

## `osint_toolkit.policy`

- `normalize_target(target: str) -> str`: normalize the host of a domain or valid HTTP(S) URL; reject empty inputs and invalid URL scheme/host combinations.
- `authorize(target, allowed) -> str`: requires a non-empty explicit allow-list and matches an exact host or a subdomain of a listed parent. Sibling domains are out of scope.
- `AuthorizationError`: fail-closed error for invalid or unauthorized scope.

## `osint_toolkit.models.Observation`

Fields: `source`, timezone-aware `timestamp`, `target`, `entity_type`, `value`, `confidence` in `[0,1]`, optional `evidence_url`, optional 64-character lowercase-hex SHA-256 `hash`, and `status` (`ok`, `error`, `skipped`). Unknown fields are forbidden.

## `osint_toolkit.evidence.store_evidence`

Takes raw bytes, a kind/name token, optional evidence URL and root directory; returns the full SHA-256, relative/actual path, and evidence URL. Do not treat the hash as proof of authenticity. A hardening follow-up proposes validating the kind and verifying the full digest when reusing a 12-character-prefix path.

## `osint_toolkit.pipeline.run`

`run(target, allowed_targets, out_path='observations.jsonl', evidence_root='evidence')` authorizes before collectors run, then appends normalized JSONL observations. The MVP is passive: DNS, one HTTP HEAD, robots.txt read and normal TLS handshake.

## `osint_toolkit.correlator`

- `load_observations(path)`: load and validate JSONL observations.
- `build_report(observations, risk_threshold=0.7)`: group by `(target, entity_type)`, summarize counts/confidence/risk/evidence refs, and set `human_review_required` plus `ai_authority='advisory_only'`.
- `write_report(...)`: write a derived report JSON file.

## Authority boundary

Collectors provide observations; the correlator summarizes the inputs. Neither AI nor derived risk values authorize collection or execution. Actual collection requires an explicit scope; non-trivial operational changes require human approval.
