# Block 3 — Prediction Error Contract

**Status:** DRAFT / AUDIT
**Version:** 0.1
**Scope:** Cognitive Core Block 3

## 0. Purpose

Define the minimal, deterministic and auditable representation of prediction error after a committed prediction is compared with an observed result.

This block detects discrepancy. It does not explain its cause.

## 1. Epistemic Separation

The following concepts MUST remain distinct:

- PREDICTION — committed expectation from Block 1.
- OBSERVATION — externally obtained result or evidence-bearing observation.
- PREDICTION_ERROR — discrepancy between the committed prediction and the observed result.
- ERROR_ATTRIBUTION — causal explanation of the discrepancy; defined only in Block 4.
- BELIEF — epistemic confidence maintained by Block 2.
- ACTION_PROPOSAL — proposed intervention; defined later.
- AUTHORIZATION — execution authority owned by TUU, not Cognitive Core.

Prediction Error MUST NOT be treated as proof that a hypothesis is false, proof that an observation is correct, or proof of causal attribution.

## 2. Canonical Relationship

The conceptual relationship is:

`committed_prediction + comparable_observation -> prediction_error`

The original committed prediction MUST remain immutable.

## 3. Canonical Error Object

The minimum resolved representation MUST contain:

```json
{
  "prediction_hash": "<string>",
  "observed_value": "<json-value>",
  "outcome": "MATCH | MISMATCH | NOT_COMPARABLE",
  "error": "<json-value>",
  "timestamp_logical": "<integer>"
}
```

The exact error representation MUST be deterministic for a given prediction, observation and comparison rule.

## 4. Comparison Rule

A Prediction Error MUST NOT be calculated using an unstated comparison rule.

The comparison rule MUST be explicit and associated with the error event.

The rule MAY be exact equality, numeric difference, absolute error, relative error, categorical mismatch, or another formally defined comparator.

The comparator MUST NOT be silently changed after the result is known.

## 4.1 Comparison Outcome

Every comparison MUST produce one explicit outcome:

- `MATCH` — the observed result satisfies the committed prediction according to the declared comparison rule.
- `MISMATCH` — the observed result does not satisfy the committed prediction according to the declared comparison rule.
- `NOT_COMPARABLE` — the prediction and observation cannot be validly compared under the declared rule.

`MISMATCH` MUST NOT be interpreted as proof that the hypothesis is false or that any specific cause produced the discrepancy.

The meaning and representation of the `error` field MUST be determined by the declared comparison rule. The implementation MUST NOT silently change the meaning of `error` between comparison rules.

The comparison outcome and error representation MUST be derived from the prediction, observation and declared comparison rule without causal attribution.

## 5. Unknown and Not-Yet-Decidable

A prediction comparison MAY be unresolved when:

- the observation is missing;
- the observation is malformed;
- the prediction and observation are not comparable;
- the comparison rule is undefined;
- required provenance is unavailable.

In these cases the system MUST NOT fabricate a numeric error.

`MATCH`, `MISMATCH` and `NOT_COMPARABLE` are comparison outcomes. `UNKNOWN` and `NOT_YET_DECIDABLE` are unresolved epistemic statuses and MUST NOT be encoded as comparison outcomes. When resolution is impossible, the system MUST preserve that unresolved status without fabricating a resolved error.

## 6. Provenance

The error event MUST preserve provenance sufficient to reconstruct:

- which committed prediction was evaluated;
- which observation/result was used;
- which comparison rule was applied;
- when the comparison occurred;
- the source or origin of the observation.

Provenance MUST NOT mutate the original Prediction Commitment.

## 7. Temporal Invariant

A Prediction Error MUST reference a prediction that was committed before the observation/comparison event.

An observation MUST NOT retroactively modify the committed prediction.

Logical timestamps MUST preserve event ordering.

## 8. No Post-Hoc Rationalization

The system MUST NOT modify the prediction, conditions, or prediction hash to reduce or eliminate an observed error.

A mismatch between prediction and result is evidence of discrepancy, not permission to rewrite the prediction.

## 9. Attribution Boundary

Block 3 MUST detect and represent discrepancy only.

It MUST NOT determine whether the discrepancy was caused by:

- sensor failure;
- execution failure;
- environmental change;
- model failure;
- hypothesis failure;
- data corruption;
- another cause.

Those questions belong to Block 4 — Error Attribution.

## 10. Cognitive / Authorization Separation

Prediction Error belongs to Cognitive Core.

Prediction Error MUST NOT:

- EXECUTE;
- AUTHORIZE;
- MODIFY_CONTRACT;
- WRITE_LEDGER_DIRECTLY;
- BYPASS_TUU;
- MODIFY_EXECUTION_POLICY.

`cognitive_state != authorization_state` MUST remain invariant.

## 11. Determinism

Given identical committed prediction, observation, comparison rule and relevant logical timestamp, the resolved Prediction Error representation MUST be deterministic.

No external LLM, random source, or mutable global state may be required to calculate the canonical error.

## 12. Immutability

A resolved Prediction Error is an event/result representation and MUST NOT mutate the committed prediction or previous belief state.

A later correction MUST create a new event rather than rewriting historical state.

## 13. Non-Goals

Block 3 does NOT implement:

- causal error attribution;
- Bayesian inference;
- likelihood estimation;
- belief updating;
- competing hypotheses;
- active inference;
- action authorization;
- execution;
- LLM integration;
- quantum integration;
- new cryptographic primitives;
- changes to TUU or Ledger architecture.

## 14. Required Verification

Before implementation is considered complete, tests MUST verify at minimum:

1. valid prediction/result comparison;
2. deterministic error representation;
3. explicit comparison rule;
4. missing observation handling;
5. incomparable values handling;
6. UNKNOWN / NOT_YET_DECIDABLE handling;
7. temporal ordering;
8. prediction immutability;
9. resistance to post-hoc prediction mutation;
10. provenance preservation;
11. separation from Error Attribution;
12. separation from authorization and execution.

## 15. Block Boundary

```text
Block 1
Prediction Commitment
        |
        v
Block 2
Belief State
        |
        v
Block 3
Prediction Error
        |
        v
Block 4
Error Attribution
```

Block 3 answers: **"Did the observed result differ from the committed prediction, according to an explicit comparison rule?"**

Block 4 answers the separate question: **"What may have caused the discrepancy?"**
