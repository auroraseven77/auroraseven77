# TUU v2.1 — DEFENSIBLE_CONTRACT

## Status

This document defines the regression contract for the v2.1 invariant layer.
It is an engineering contract, not a claim of mathematical proof of the
entire implementation.

## 1. Input contract

The lifecycle receives immutable candidate metrics. Candidate scores are
computed deterministically by compute_candidate_evaluation().

## 2. Normalization contract

For n >= 2:

p_i = S_i / sum(S_j)

If all effective scores are zero, the entropy path is treated as a
degenerate resolving condition.

## 3. H_N contract

For n >= 2:

H_N = -sum(p_i log2(p_i)) / log2(n)

For n=1, the entropy calculation is isolated from the Shannon divisor;
the lifecycle may apply its explicit single-candidate policy directly.

H_N is descriptive and is not itself a decision threshold.

## 4. K_N contract

K_N = 1 - H_N

The invariant is evaluated before presentation rounding wherever raw values are
available. Rounded values are display/serialization values only.

## 5. Threshold contract

Consensus requires both inclusive conditions:

K_N >= tau_K, and S_i* >= S_min

with v2.1 defaults:

- tau_K = 0.25
- S_min = 0.50

A boundary value exactly equal to either threshold therefore passes that
individual condition.

## 6. Tie-break contract

When multiple maximum scores are equivalent within the declared tolerance
(delta < 1e-9), select the candidate with the lexicographically smallest
SHA-256(intent) hexadecimal digest.

The physical arrival order is not a semantic tie-break key.

## 7. InvariantEngine boundary

InvariantEngine is a pure observer:
- no authorization;
- no command execution;
- no lifecycle mutation;
- no candidate selection outside validation.

A violation raises InvariantViolationError.

## 8. Execution boundary

Authorization and secure execution remain downstream responsibilities.
The invariant layer does not replace policy enforcement.

## 9. Regression requirement

Every future consensus primitive or policy extension must preserve:

1. K_N = 1 - H_N;
2. no direct H_N thresholding;
3. deterministic SHA-256 tie resolution;
4. inclusive threshold semantics;
5. explicit handling of n=1.
