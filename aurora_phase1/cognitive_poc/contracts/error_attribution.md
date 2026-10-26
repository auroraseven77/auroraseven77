# Block 4 — Error Attribution Contract

**Status:** DRAFT / AUDIT

**Version:** 0.1

**Scope:** Cognitive Core Block 4

## 0. Purpose

Define the minimal, deterministic and auditable representation of candidate causes associated with a previously represented Prediction Error.

Block 4 evaluates attribution candidates. It does not transform a prediction mismatch into proof of a specific cause.

## 1. Epistemic Separation

The following concepts MUST remain distinct:

- PREDICTION — committed expectation from Block 1.
- OBSERVATION — externally obtained result or evidence-bearing observation.
- PREDICTION_ERROR — discrepancy represented by Block 3.
- ERROR_ATTRIBUTION — structured assessment of causes that may explain the discrepancy.
- HYPOTHESIS — explanatory proposition represented by the Cognitive Core.
- BELIEF — epistemic confidence maintained by Block 2.
- ACTION_PROPOSAL — proposed intervention.
- AUTHORIZATION — execution authority owned by TUU.

A Prediction Error MUST NOT be treated as proof of a particular causal attribution.

An attribution candidate MUST NOT be treated as an established cause merely because it is plausible or because it was selected by the Cognitive Core.

## 2. Canonical Relationship

The conceptual relationship is:

`prediction_error + attribution_evidence -> attribution_state`

The original Prediction Commitment and Prediction Error MUST remain immutable.

Block 4 MUST consume the discrepancy represented by Block 3 rather than redefining the comparison performed by Block 3.

## 3. Canonical Attribution Object

The canonical attribution representation MUST contain:

```json
{
  "prediction_hash": "<string>",
  "prediction_error_timestamp_logical": "<integer>",
  "candidate_causes": [
    {
      "cause_id": "<string>",
      "status": "SUPPORTED | PLAUSIBLE | INCONSISTENT | INSUFFICIENT_EVIDENCE"
    }
  ],
  "attribution_status": "RESOLVED | MULTIPLE_COMPATIBLE | ATTRIBUTION_UNRESOLVED",
  "timestamp_logical": "<integer>"
}
```

The canonical object represents an attribution assessment, not a statement of objective causal truth.

`prediction_hash` and `prediction_error_timestamp_logical` identify the referenced Block 3 Prediction Error.

`candidate_causes` MUST preserve explicit cause identities and their attribution status.

Multiple candidate causes MAY remain simultaneously compatible with the available evidence.

## 4. Prediction Error Reference Boundary

`prediction_hash` and `prediction_error_timestamp_logical` MUST identify the specific Prediction Error being assessed.

The reference MUST resolve deterministically to the existing Block 3 Prediction Error using its `prediction_hash` and `timestamp_logical` fields.

Block 4 MUST NOT modify the canonical Prediction Error object to introduce an attribution-specific field.

The canonical attribution object MUST use `prediction_hash` as the Prediction Error reference and `prediction_error_timestamp_logical` as the referenced Prediction Error timestamp.

The implementation MUST NOT invent a separate Prediction Error identity that cannot be deterministically resolved to the existing Block 3 object.

If the existing system cannot resolve the referenced Prediction Error deterministically, the implementation MUST preserve that limitation rather than fabricate an identity.

## 5. Candidate Cause Status

The following candidate statuses are defined:

- `SUPPORTED` — available evidence supports the candidate under the declared attribution criteria.
- `PLAUSIBLE` — the candidate is compatible with the evidence but support is insufficient for a stronger status.
- `INCONSISTENT` — available evidence conflicts with the candidate under the declared attribution criteria.
- `INSUFFICIENT_EVIDENCE` — available evidence is insufficient to evaluate the candidate.

`SUPPORTED` MUST NOT mean mathematically proven, objectively certain, or exclusively causal.

`PLAUSIBLE` MUST NOT be silently promoted to `SUPPORTED`.

`INCONSISTENT` MUST NOT be interpreted as proof that every alternative cause is correct.

`INSUFFICIENT_EVIDENCE` MUST remain explicit and MUST NOT be converted into a forced attribution.

## 6. Attribution Status

The attribution state MUST explicitly distinguish:

- `RESOLVED` — attribution criteria identify a supported candidate without unresolved competing candidates under the declared criteria.
- `MULTIPLE_COMPATIBLE` — two or more candidates remain compatible with the available evidence.
- `ATTRIBUTION_UNRESOLVED` — available information does not permit a resolved attribution.

`ATTRIBUTION_UNRESOLVED` is a valid epistemic state.

It MUST NOT be encoded as a fabricated cause, empty certainty, numeric zero, or numeric one.

## 7. Attribution Criteria

Every attribution assessment MUST use explicit attribution criteria.

The criteria MUST define how available evidence is evaluated against each candidate cause.

The criteria MUST be identifiable and reproducible from the attribution provenance.

The evaluator applied to candidate causes MUST have a stable `evaluator_id` recorded in attribution provenance.
The evaluator identity is provenance metadata only and MUST NOT be part of the canonical attribution object.

Attribution criteria MUST NOT be silently changed after the evidence or prediction error is known.

If a new attribution criterion is introduced, it MUST produce a new attribution assessment rather than retroactively altering the previous assessment.

The criteria MUST NOT encode a preferred cause merely to force a resolved attribution.

## 8. Attribution Provenance

Every attribution assessment MUST have sufficient provenance to reconstruct the basis of the assessment.

Provenance MUST identify, directly or through deterministic references:

- the Prediction Error being assessed;
- the candidate causes evaluated;
- the evidence or observations used in the assessment;
- the attribution criteria applied;
- the stable identity (`evaluator_id`) of the deterministic evaluator applied to the candidate causes;
- the logical time of the assessment;
- the source or origin of attribution-relevant evidence.

Provenance MUST remain separate from the canonical attribution object.

Missing or non-reconstructible provenance MUST prevent the system from presenting the attribution as fully resolved.

## 9. Temporal Ordering

An attribution assessment MUST reference an already established Prediction Error.

The attribution timestamp MUST be strictly later than the logical timestamp of the referenced Prediction Error.

Attribution assessment MUST NOT modify or retroactively alter the Prediction Commitment or Prediction Error.

A later attribution assessment MUST be represented as a new immutable assessment.

Logical timestamps MUST preserve the causal ordering between prediction commitment, observation, prediction error and attribution assessment.

## 10. Multiple Compatible Causes

Multiple candidate causes MAY remain simultaneously compatible with the available evidence.

A `SUPPORTED` candidate MUST NOT automatically invalidate another candidate that remains `PLAUSIBLE` or `SUPPORTED` under the same attribution criteria.

The implementation MUST NOT collapse multiple compatible candidates into a single cause without an explicit attribution criterion that justifies the reduction.

When multiple candidates remain compatible and no declared criterion resolves the ambiguity, the attribution state MUST remain `MULTIPLE_COMPATIBLE`.

Candidate ordering MUST NOT imply causal priority, preference, probability, or ranking unless such semantics are explicitly defined by a separate contract.

## 11. Unknown and Not-Yet-Decidable Attribution

Attribution MUST support an explicit unresolved state when the available evidence is insufficient for a defensible attribution.

`UNKNOWN` and `NOT_YET_DECIDABLE` MAY be used as external epistemic statuses for unresolved attribution assessments.

These statuses MUST NOT be confused with candidate cause statuses such as `INSUFFICIENT_EVIDENCE` or `INCONSISTENT`.

The system MUST NOT fabricate a cause when evidence is missing, contradictory, unavailable, or non-reconstructible.

An unresolved attribution MUST remain explicitly unresolved until additional admissible evidence or a declared new criterion permits reassessment.

Additional evidence MUST produce a new attribution assessment and MUST NOT rewrite the previous unresolved assessment.

## 12. Attribution Is Not Belief Update

An attribution assessment MUST NOT automatically modify the Belief State defined by Block 2.

The attribution result MAY provide information for a future belief transition, but that transition MUST be represented separately.

A `SUPPORTED`, `PLAUSIBLE`, `INCONSISTENT`, or `INSUFFICIENT_EVIDENCE` attribution status MUST NOT itself encode a belief value.

No attribution assessment MAY directly convert its status into increased or decreased belief without an explicit and separately defined belief-update mechanism.

If a belief update occurs, it MUST preserve the existing Block 2 temporal, provenance, immutability, and validation requirements.

## 13. No Post-Hoc Rationalization

An attribution assessment MUST NOT alter the interpretation of the original prediction or prediction error merely to make the observed result appear consistent with the prediction.

A candidate cause discovered only after a Prediction Error MAY be evaluated as a new explanatory candidate, but the assessment MUST preserve the fact that the candidate was introduced after the result was observed.

The system MUST NOT rewrite a committed prediction, its conditions, the observed result, or the Prediction Error to support a preferred attribution.

Attribution criteria MUST be declared explicitly and MUST be applied consistently to the candidate set under assessment.

A later attribution assessment MUST remain a new epistemic state and MUST NOT be represented as if it were part of the original prediction commitment.

## 14. Determinism

For identical Prediction Error input, candidate causes, attribution evidence, attribution criteria, and logical timestamp, the canonical attribution representation MUST be deterministic.

The implementation MUST NOT depend on randomness, wall-clock time, process state, hidden global state, or nondeterministic candidate ordering.

Equivalent inputs MUST produce equivalent canonical attribution objects.

If deterministic ordering is required for serialization or comparison, the ordering rule MUST be explicit and MUST NOT imply causal priority, preference, probability, or ranking.

Any nondeterministic external process MUST be represented as an input or provenance source rather than hidden inside the attribution result.

## 15. Cognitive and Authorization Separation

Error Attribution is an epistemic operation and MUST NOT grant operational authority.

The Cognitive Core MUST NOT use an attribution assessment to execute an action, authorize an action, modify governance contracts, write directly to the Ledger, or bypass TUU.

An attribution result MAY inform an ACTION_PROPOSAL, but any proposed action MUST remain subject to the existing TUU authorization gate.

Cognitive state, attribution state, and authorization state MUST remain distinct.

No attribution status MUST be interpreted as implicit authorization, execution permission, or policy approval.

## 16. Immutability

An attribution assessment MUST be immutable after it has been established.

A later assessment MUST be represented as a new attribution state and MUST NOT overwrite the previous assessment.

No attribution assessment MAY retroactively modify the referenced Prediction Error, Prediction Commitment, observation, attribution evidence, or attribution criteria.

If additional evidence becomes available, the system MUST create a new assessment that preserves the previous assessment as historical state.

Any canonical attribution object used for verification MUST remain unchanged after commitment.

## 17. Non-Goals

Block 4 MUST NOT implement or implicitly introduce:

- Bayesian inference, likelihood estimation, or causal probability.
- Automatic Belief State updates.
- Automatic competing-hypothesis generation.
- Active inference or experiment selection.
- Autonomous action selection or execution.
- Action authorization or policy mutation.
- LLM integration as a source of causal authority.
- Quantum or hardware integration.
- New cryptographic primitives.
- New persistence or Ledger architecture.
- Changes to the existing TUU authorization architecture.

These capabilities MAY be addressed by later contracts, but MUST remain outside the Block 4 attribution primitive.

## 18. Required Verification

The Block 4 implementation MUST provide verification for at least the following:

1. Valid attribution assessment.
2. Explicit candidate cause identities.
3. Valid candidate cause statuses.
4. Explicit unresolved attribution.
5. Multiple compatible causes.
6. Insufficient evidence without forced attribution.
7. Explicit attribution criteria.
8. Reconstructible attribution provenance.
9. Valid temporal ordering.
10. Attribution immutability.
11. Rejection of Prediction Error mutation.
12. Rejection of Prediction Commitment mutation.
13. Separation from automatic belief update.
14. Rejection of post-hoc rationalization.
15. Deterministic canonical representation.
16. Separation between attribution and authorization or execution.

## 19. Block Boundary

The Cognitive Core epistemic sequence is:

Block 1 — Prediction Commitment.
Block 2 — Belief State.
Block 3 — Prediction Error.
Block 4 — Error Attribution.
Block 5 — Competing Hypotheses.

Block 3 determines whether an observed result matches, mismatches, or cannot be compared with a committed prediction under an explicit comparison rule.

Block 4 evaluates candidate causes for an established Prediction Error using explicit attribution evidence and attribution criteria.

Block 4 MUST NOT perform the function of Block 3 by redefining whether the prediction matched the observation.

Block 4 MUST NOT perform the function of Block 5 by automatically generating or selecting competing hypotheses.

The transition from Prediction Error to Error Attribution MUST preserve the distinction between discrepancy detection and causal explanation.

## 20. Acceptance Criteria

The Block 4 contract is considered structurally complete only if the implementation can demonstrate:

- A deterministic canonical attribution object.
- Explicit candidate cause identities and statuses.
- Explicit distinction between RESOLVED, MULTIPLE_COMPATIBLE, and ATTRIBUTION_UNRESOLVED.
- Explicit attribution criteria that are reproducible from provenance.
- Sufficient provenance to reconstruct the attribution assessment.
- Strict temporal ordering after the referenced Prediction Error.
- Immutability of established attribution assessments.
- Preservation of the original Prediction Commitment and Prediction Error.
- Explicit handling of UNKNOWN and NOT_YET_DECIDABLE epistemic states.
- No automatic Belief State modification.
- No post-hoc rewriting of prediction, observation, or Prediction Error.
- No implicit authorization or execution authority.
- No dependence on randomness, wall-clock time, hidden state, or nondeterministic ordering.
- Compatibility with later competing-hypothesis reasoning without implementing it in Block 4.

## 21. Authority Statement

Error Attribution is an epistemic assessment only.

It does not grant execution authority, authorization authority, contract mutation authority, or direct Ledger write authority.

The intended flow is:

Cognitive Core
→ Error Attribution
→ information for future reasoning
→ TUU authorization gate
→ HEPHAESTUS execution

No attribution status can bypass this boundary.
