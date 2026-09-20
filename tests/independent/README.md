# TUU v2.1 — Independent Verification Suite

This directory is an adversarial verification layer for the v2.1 defensible contract. It is intentionally separate from production implementation and must not import production helpers for K_N, tie resolution, or ledger hashing.

## Baseline and scope

Reference baseline: `5d56b6eaff29d2bcb98efff6b7f1fad1f31ff6df`.

The baseline is not modified by this suite. The V0 test proves only that the reference commit remains an ancestor of the tested revision; Git content-addressing makes the referenced tree immutable.

The current PR branch is a structural v2.1 slice. The suite therefore distinguishes **implemented evidence** from **declared/specification-only behavior**. A failing independent test is a regression/blocker signal, not something to weaken by adapting the oracle to production output.

## Tests

| Test | Contract | PASS means | Current branch expectation |
|---|---|---|---|
| V0 | Baseline identity | Reference SHA exists and is an ancestor | PASS |
| V1 | Permutation invariance | Winner/state/metrics are unchanged as semantic values under arrival-order permutation | PASS |
| V2 | RAW K_N | Raw probabilities and raw H_N/K_N are exposed before presentation rounding and match an independent calculation | FAIL until raw values are exposed |
| V3 | Tie tolerance | ΔS < 1e-9 invokes SHA-256 tie-break; ΔS >= 1e-9 preserves the strict maximum | FAIL until production tie handling uses tolerance |
| V4 | Consensus vs authorization | Statistical consensus can be reached while downstream authorization still blocks execution | PASS |
| V5 | Ledger evidence | An executable attestation/hash-chain implementation exists and its evidence can be reconstructed independently | FAIL until an executable ledger is present |

## Independent mathematical oracle

For n >= 2:

`p_i = S_i / sum(S_j)`

`H_N = -sum(p_i log2(p_i)) / log2(n)`

`K_N = 1 - H_N`

The oracle uses its own arithmetic implementation. It does not call `compute_normalized_entropy`, `calculate_swarm_consensus`, `InvariantEngine`, or any production hash helper.

The known polarized vector `[0.88, 0.22, 0.12]` gives approximately:

- probabilities: 0.7213114754, 0.1803278689, 0.0983606557
- H_N: 0.7032949508
- K_N: 0.2967050492

The displayed six-decimal values are not treated as RAW evidence.

## Tie contract

The declared contract is strict:

`abs(S_i - S_max) < 1e-9`

Only candidates inside that open tolerance are a tie. At exactly `1e-9`, the candidate is **not** tied.

Within the tie set, the expected winner is the candidate whose UTF-8 intent has the lexicographically smallest lowercase SHA-256 hexadecimal digest.

## PASS / FAIL discipline

- **PASS**: the independent oracle and observable runtime agree on the stated contract.
- **FAIL**: required evidence is absent or runtime behavior contradicts the contract.
- **No PASS by rounding**: rounded presentation fields cannot establish a RAW invariant.
- **No PASS by specification**: documentation describing a ledger cannot substitute for executable ledger evidence.
- **No production-oracle contamination**: importing a production calculation merely to obtain the expected answer invalidates the independence property.

Run with:

```bash
pytest tests/independent/ -q
```
