# Aurora/TUU Portfolio Index — TELOS snapshot

**Snapshot date:** 2026-10-26  
**Repository base observed:** `main` at `465a2a51592c146cde6f133e5c871ec808014736`.

This page is a navigation and scope index. It is not a scientific proof, release statement, or assertion that every historic artifact has been recovered.

## Core documentation

- [Project status matrix](PROJECT_TRIAGE.md)
- [Evidence Ledger artifact state](LEDGER-STATUS.md)
- [Repository component status](../audits/COMPONENT-STATUS.md)
- [Evidence index and provenance gaps](../audits/EVIDENCE-INDEX.md)
- [Reproducibility protocol and limitations](../audits/REPRODUCIBILITY.md)
- [Repository-level state snapshot](../../STATUS.md)

## Project map

| Project | Repository path / source | Current evidence status | Next gate |
|---|---|---|---|
| Aurora Evidence Ledger 0.1.0 | Delivered TELOS package; source branch/history recorded separately | 16/16 prototype tests passed in isolated test suite; H1 Termux transcript reports 16/16 and example `valid:true` | Review schema/threat model; only later test SQLite against disposable copy |
| TUU Core / Pydantic ARMv7 | `TUU/` | Current `main` Core/Integration CI green; ARMv7 wheel candidate found from public release metadata, install not yet observed | Run hash-pinned disposable Termux venv and paste sanitized receipt |
| Aurora Cognitive Core B7/B8 | `aurora_phase1/cognitive_poc/` | Current Phase 1 CI green on Python 3.11 and 3.12 | Reproduce target test suite at exact commit; preserve temporal/provenance identity contract |
| B1/MPS/B1.2 | `b1_motor/` | Current B1.2 CI green on Python 3.11 and 3.12 | Keep protected motor unchanged; reproduce only within approved test scope |
| B1.3 energy validation | Historical branch `feat/b1.3-energy-validation-harness`; PR #7 is closed unmerged | 34 tests were reported historically; old Core/Integration workflows failed on old branch; static review found two weak assertions | Exact-commit test run and hardened non-tautological assertions |
| B1-GEN-01A | `docs/audits/issue-drafts/B1-GEN-01A.md` | Blocked: original target manifest, checksum file and isolated suite absent in accessible tree | Recover original bytes/commit/seed/budget; never synthesize to match historical hashes |
| AC4-R2 | `docs/audits/issue-drafts/AC4-R2.md` | Blocked: historical v0–v08 raw artifacts not confirmed in accessible tree | Find original archive/ledger and establish chain of custody |
| B11 / P14–P19 | `docs/audits/issue-drafts/B11.md` | Provenance unresolved; no global Navier–Stokes proof confirmed | Locate original text and audit mathematical dependencies, assumptions, and gaps |
| RCS Nighthawk | `docs/audits/issue-drafts/RCS-Nighthawk.md` | Historical job IDs/logs and exact QPY/QASM sources not confirmed | Recover original inputs/outputs/seeds/toolchain and reproduce discrepancy |
| AEGIS | No authoritative path/commit located in accessible tree | Source identity unknown; do not mark permanently irrecoverable | Supply the original repository/archive locator and scope |
| OSINT Toolkit | `osint-toolkit/` | Ten D1–D10 draft proposals created in separate branches; applicable CI observed individually | Human review; merge decisions remain with repo owner; no release or external collection implied |

## Expansion proposals

- [D1 — installation/API docs](https://github.com/auroraseven77/auroraseven77/pull/33)
- [D2 — test boundaries and root OSINT test workflow](https://github.com/auroraseven77/auroraseven77/pull/34)
- [D3 — Python matrix and quality reporting](https://github.com/auroraseven77/auroraseven77/pull/35)
- [D4 — optional test extra and wheel/sdist CI](https://github.com/auroraseven77/auroraseven77/pull/39)
- [D5 — non-root, no-publish container smoke path](https://github.com/auroraseven77/auroraseven77/pull/36)
- [D6 — evidence-store hardening and security/SBOM workflow](https://github.com/auroraseven77/auroraseven77/pull/37)
- [D7 — local observability contract](https://github.com/auroraseven77/auroraseven77/pull/38)
- [D8 — offline TUU Evidence Ledger adapter contract](https://github.com/auroraseven77/auroraseven77/pull/40)
- [D9 — community/security/issue-template controls](https://github.com/auroraseven77/auroraseven77/pull/41)
- [D10 — SemVer/release gate/30-60-90 roadmap](https://github.com/auroraseven77/auroraseven77/pull/42)

All links above are proposals and must be rechecked for state before use. Draft status is intentional until a human review approves the contents.

## Trust boundaries

- `main` is not modified by this index branch.
- CI success is bound to the exact commit/workflow and is not proof of historical provenance or scientific claims.
- SHA-256 helps detect byte changes relative to a known digest; it does not independently establish historical authenticity.
- Absence from the current accessible tree is scoped absence, not global irrecoverability.
- No user-device, Snowflake, admin-console, secret, live TUU SQLite/WAL, or external target operation is performed by this documentation.

## Legacy TUU PR blockers — observed 2026-10-26

This section records CI findings tied to the exact historical PR head commits below. They are not evidence that the current `main` commit is failing; the branches were created against older base commits and must be revalidated before any promotion.

| PR | Tested head | Observed CI evidence | Disposition |
|---|---|---|---|
| [#1 — v2.1 invariant engine](https://github.com/auroraseven77/auroraseven77/pull/1) | `c321ba579efbc7966f0b336a0c30a9fde21f6d98` | Runs [35418397303](https://github.com/auroraseven77/auroraseven77/actions/runs/35418397303) and [35418397220](https://github.com/auroraseven77/auroraseven77/actions/runs/35418397220) failed. Logs show 10 failed / 34 passed in the integration job, including lifecycle-state mismatches, missing required `AgentMetricOutput` fields, and calls passing `auth_context` to a function accepting `authorization_context`. | Not merge-ready on this evidence; fix failures and rerun against updated `main`. |
| [#2 — package foundation](https://github.com/auroraseven77/auroraseven77/pull/2) | `a2eea9abfc2a1ffe530d3538d84286e852f55bd0` | Runs [35406375611](https://github.com/auroraseven77/auroraseven77/actions/runs/35406375611) and [35406375534](https://github.com/auroraseven77/auroraseven77/actions/runs/35406375534) failed during pytest collection. Logs report `RecursionError` across five test modules before the suite could execute. | Package/install step alone is insufficient; repair the model/type recursion and rerun collection plus tests. |
| [#3 — immutable MPS swarm contracts](https://github.com/auroraseven77/auroraseven77/pull/3) | `be0144ca23bd7ebd0033bc635bdab8edf9228227` | Runs [35547224344](https://github.com/auroraseven77/auroraseven77/actions/runs/35547224344) and [35547224416](https://github.com/auroraseven77/auroraseven77/actions/runs/35547224416) failed. Integration collection could not import `TUUCore`; core CI also reported immutability-test failure, required-field validation errors, lifecycle API keyword mismatch, and lifecycle-state mismatch. | Must reconcile the test surface/API and restore the intended immutability guarantee before review. |
| [#30 — lifecycle fixture](https://github.com/auroraseven77/auroraseven77/pull/30) | `954640cad7cfef5952895e23860cb2d27078859b` | Core CI run [35549915344](https://github.com/auroraseven77/auroraseven77/actions/runs/35549915344) passed, but integration run [35549915359](https://github.com/auroraseven77/auroraseven77/actions/runs/35549915359) failed at collection because `TUUCore` could not be imported by two integration test modules. | Mixed result; do not treat core workflow success as full integration success. |

### Required gate before any of these PRs is promoted

1. Update each candidate against the current base in an isolated branch; do not rewrite `main`.
2. Fix source/API/validation defects rather than weakening tests to match implementation.
3. Run the full currently applicable workflow matrix and inspect the exact head SHA, run IDs, failing step, and test summary.
4. Verify authorization-denial and no-side-effect paths; verify deep immutability with adversarial nested inputs.
5. Keep the PR open and unmerged until human review. These historical runs are diagnostic evidence, not proof of a present-day failure or of scientific validity.
