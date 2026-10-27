# OSINT Toolkit roadmap and release policy proposal

**Current version:** `0.1.0` in `pyproject.toml`.

## Proposed semantic versioning

- `PATCH` (`0.1.x`): backward-compatible bug fixes, validation hardening and documentation clarification.
- `MINOR` (`0.x.0` while pre-1.0): additive CLI/schema behavior with migration notes; breaking changes can occur before 1.0.0 but must be documented.
- `MAJOR` (`1.0.0` and later): incompatible CLI, schema, evidence format or public Python API changes.
- Pin release artifacts and publish SHA-256 checksums and a machine-readable SBOM. Tags are immutable; never retag a published version.

## Days 0–30 — safety and reproducibility

- Harden content-addressed evidence path handling.
- Expand authorization/input edge tests and CI Python matrix.
- Publish installation/API documentation and repeatable wheel/sdist build.
- Make CI/local test commands deterministic and record outputs.

## Days 31–60 — packaging and observability

- Add opt-in structured local events under the observability contract.
- Keep telemetry local and secrets-redacted.
- Add SBOM, dependency audit and security review workflow.
- Prototype a ledger adapter against a disposable copy only; never target a live TUU database.

## Days 61–90 — review and release readiness

- Conduct human security review of collectors and persistence behavior.
- Verify container behavior in CI without publishing images by default.
- Publish an RC only after test, dependency, documentation and license decisions are approved.
- Gather maintainers' feedback and document policy before declaring 1.0.0 readiness.

## Release gate

No release is complete until the supported test matrix passes, package metadata installs from the built wheel, an sdist is available, SBOM/checksums accompany artifacts, vulnerability findings are triaged, scope/side effects are documented, and a human approves the release.

## Decisions not made here

- Project license: no license file was present in the current OSINT Toolkit folder; the repository owner must choose the actual license before distribution assumptions are made.
- Release channel/cadence: proposal only, not a schedule commitment.
- Container registry/publication: no registry or credentials are configured; CI only builds/smoke-tests locally.
