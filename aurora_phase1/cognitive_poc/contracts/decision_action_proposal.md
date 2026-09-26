# Block 6 — Decision / Action Proposal Contract

**Status:** DRAFT / AUDIT
**Version:** 0.1
**Scope:** Cognitive Core Block 6

## 0. Purpose

Block 6 defines the minimal, deterministic, immutable, and auditable representation of a decision assessment and an associated action proposal derived from explicitly supplied cognitive state and evidence.

Block 6 represents a proposed intervention or decision state.

It MUST NOT establish operational authority.

A decision assessment MUST NOT be treated as authorization.

An action proposal MUST NOT be treated as execution permission.

## 1. Epistemic and Operational Separation

The following concepts MUST remain distinct:

- OBSERVATION — externally obtained result;
- EVIDENCE — information used for assessment;
- HYPOTHESIS — explanatory proposition;
- PREDICTION — committed expected outcome;
- PREDICTION_ERROR — discrepancy represented by Block 3;
- ERROR_ATTRIBUTION — candidate-cause assessment represented by Block 4;
- BELIEF — epistemic state represented by Block 2;
- HYPOTHESIS_SET — competing hypotheses represented by Block 5;
- DECISION_ASSESSMENT — explicit assessment leading to a proposal;
- ACTION_PROPOSAL — proposed intervention;
- AUTHORIZATION — operational authority owned by TUU;
- EXECUTION — operational effect owned by HEPHAESTUS.

No one of these concepts MUST be silently substituted for another.

## 2. Canonical Relationship

A `PROPOSED` Decision Assessment represents a determinately represented candidate decision. It does not mean authorization and does not require that an Action Proposal already exists.

An `UNRESOLVED` or `NOT_YET_DECIDABLE` Decision Assessment MUST NOT be used to represent a determined action decision. An Action Proposal MAY be preserved as an explicitly unresolved proposal candidate, but MUST NOT be represented as a determined action decision or as authorization.

The canonical relationship is:

```text
explicit cognitive inputs
+
decision context
+
declared criteria
->
decision assessment
->
action proposal
```

The decision assessment and action proposal MUST remain separately representable.

A decision assessment MAY exist without an action proposal.

An action proposal MUST NOT imply authorization or execution.

## 3. Canonical Decision Assessment

The canonical Decision Assessment object is exactly:

```json
{
  "decision_id": "<string>",
  "decision_status": "PROPOSED | UNRESOLVED | NOT_YET_DECIDABLE",
  "rationale": "<json-value>",
  "timestamp_logical": "<integer>"
}
```

The canonical object MUST contain no authorization field, execution field, policy mutation field, or hidden operational authority.

`decision_id` MUST be a non-empty string and MUST identify one specific Decision Assessment state. Its identity MUST remain stable for that state. A changed assessment MUST produce a new `decision_id` and a new immutable object rather than modifying the prior assessment.

The `rationale` field MUST represent only the declared assessment rationale. It MUST NOT encode hidden authorization, undeclared evidence, undeclared criteria, or operational authority.

## 4. Canonical Action Proposal

The canonical Action Proposal object is exactly:

```json
{
  "action_id": "<string>",
  "action_type": "<string>",
  "parameters": "<json-value>",
  "preconditions": "<json-value>",
  "expected_effects": "<json-value>",
  "timestamp_logical": "<integer>"
}
```

The canonical object MUST contain no authorization field, execution field, approval field, policy mutation field, or operational authority.

`action_id` MUST be a non-empty string and MUST identify one specific Action Proposal state. Its identity MUST remain stable for that state. A changed proposal MUST produce a new `action_id` and a new immutable object rather than modifying the prior proposal.

## 5. Decision / Action Boundary

A decision assessment MAY exist without an action proposal.

An action proposal MAY exist without authorization, but MUST be associated with one explicitly identifiable Decision Assessment. The association MUST be represented through deterministic provenance reference to the `decision_id`; `decision_id` MUST NOT be added to the canonical Action Proposal object.

Multiple Action Proposals MAY be associated with the same Decision Assessment. Action Proposal identifiers MUST be unique within the represented proposal collection. For deterministic serialization, proposals MUST be ordered lexicographically by `action_id` using the same deterministic string ordering convention used by Block 5. This ordering is representational only and MUST NOT imply preference, ranking, probability, confidence, or authorization.

An Action Proposal MUST NOT be represented as a determined action when its associated Decision Assessment is `UNRESOLVED` or `NOT_YET_DECIDABLE`.

Authorization MUST be represented separately by the existing TUU authorization mechanism.

Execution MUST be represented separately by HEPHAESTUS.

## 6. Criteria

Decision criteria MUST be explicit, reproducible, and attributable through provenance.

Criteria MUST NOT be silently changed after the relevant evidence or cognitive state is known.

A new criterion MUST produce a new assessment rather than silently rewriting a prior assessment.

Criteria MUST NOT be constructed solely to force a preferred decision or action.

When a deterministic evaluator is used, its stable `evaluator_id` MUST be recorded in provenance. Evaluator identity is provenance metadata only and MUST NOT be part of the canonical Decision Assessment or Action Proposal object.

## 7. Evidence Boundary

Evidence MUST remain distinguishable from interpretation and rationale.

A decision assessment MUST NOT invent evidence absent from its declared inputs or provenance.

Expected effects in an Action Proposal MUST NOT be represented as observed facts.

Observed results MUST be represented separately when they become available.

## 8. Belief Boundary

Block 6 MUST NOT automatically modify Block 2 Belief State.

A belief value MUST NOT be interpreted as authorization.

A decision assessment MAY reference belief state as an input, but MUST NOT mutate the referenced belief object.

## 9. Prediction Error and Attribution Boundary

Block 6 MAY consume Prediction Error and Error Attribution as explicit inputs.

Prediction Error remains a discrepancy representation.

Error Attribution remains a candidate-cause assessment.

Neither object MUST be rewritten by Block 6.

Attribution status MUST NOT be interpreted as authorization.

## 10. Competing Hypotheses Boundary

Block 6 MAY consume a Competing Hypotheses representation as explicit input.

Hypothesis membership MUST NOT imply decision ranking, action ranking, probability, authorization, or execution permission.

Block 6 MUST NOT rewrite the referenced hypothesis set.

## 11. Action Scope

An Action Proposal MUST represent at least:

- action type;
- parameters;
- preconditions;
- expected effects.

Expected effects are anticipated consequences, not observed outcomes.

`expected_effects` are proposal-level expectations. They MUST NOT automatically create or imply a Block 1 Prediction Commitment. A formal prediction commitment requires a separate Block 1 artifact satisfying the Block 1 contract.

An Action Proposal MUST NOT claim that its expected effects have already occurred.

If an expected effect later becomes observable, the resulting observation MUST be represented as new evidence or observation rather than by mutating the proposal.

## 12. Provenance

Provenance MUST remain separate from the canonical Decision Assessment and Action Proposal objects.

Provenance SHOULD identify:

- decision context;
- evidence sources;
- referenced cognitive objects;
- declared criteria;
- evaluator identity;
- logical timestamp;
- external model involvement, if any;
- proposal source.

Provenance MUST NOT silently become part of canonical semantic state.

For deterministic cross-block traceability, provenance MAY contain explicit references to prior cognitive artifacts, including B1 Prediction Commitments, B2 Belief States, B3 Prediction Errors, B4 Attribution Assessments, and B5 Hypothesis Sets. Such references MUST remain provenance-only and MUST NOT copy prior canonical content into the B6 canonical objects.

## 13. Temporal Ordering

A Decision Assessment MUST NOT claim to have existed before its consumed inputs when those inputs are represented as temporal dependencies.

An Action Proposal MUST NOT have a logical timestamp earlier than its associated Decision Assessment. Equal timestamps MAY be valid when the logical clock does not distinguish the two artifacts and the explicit association remains deterministic.

Prior decision and proposal artifacts MUST NOT be retroactively rewritten.

## 14. Determinism

Given identical declared inputs, decision context, evidence, criteria, provenance, and logical timestamp, the canonical representation MUST be deterministic.

Block 6 MUST NOT depend on:

- wall-clock time;
- hidden mutable state;
- nondeterministic iteration;
- unstated randomness;
- unrecorded model output.

## 15. Immutability

Decision Assessment and Action Proposal objects MUST be immutable after creation.

A changed decision or proposal MUST produce a new object rather than mutate an existing object.

## 16. Unresolved States

`UNRESOLVED` means the available information does not establish a sufficiently determinate assessment.

`NOT_YET_DECIDABLE` means the required information or condition for determination is not yet available.

Neither state MUST be silently converted into certainty.

Insufficient information MUST NOT be converted into arbitrary action authorization.

## 17. External Model Boundary

An external model MAY provide an explicit input, rationale candidate, interpretation, or proposal candidate.

External model involvement MUST be represented in provenance when it contributes to the assessment.

An external model MUST NOT receive operational authority through Block 6.

## 18. Post-hoc Prevention

Block 6 MUST NOT rewrite prior cognitive blocks.

A rationale generated after an observation MUST NOT be represented as though it existed before that observation unless an earlier Decision Assessment artifact actually existed.

Expected effects MUST NOT be rewritten as observed outcomes after execution.

## 19. Authorization Boundary

Block 6 MUST NOT:

- authorize an action;
- execute an action;
- mutate authorization policy;
- mutate governance;
- write directly to the authoritative ledger;
- bypass TUU;
- invoke HEPHAESTUS as an authorization mechanism;
- interpret `decision_status` as authorization.

The invariant is:

```text
cognitive_state != authorization_state != execution_state
```

The operational boundary is:

```text
Cognitive Core
-> Decision / Action Proposal
-> TUU authorization gate
-> HEPHAESTUS execution
-> new observation / evidence
```

## 20. Non-Goals

Block 6 does NOT define:

- Bayesian posterior inference;
- automatic belief update;
- causal certainty;
- autonomous execution;
- authorization policy;
- governance mutation;
- direct authoritative-ledger writes;
- new cryptographic primitives;
- active inference;
- automatic experiment selection;
- LLM authority;
- quantum or hardware execution;
- modifications to TUU authorization semantics.

## 21. Required Verification

The implementation MUST verify at minimum:

1. valid decision identifier;
2. valid decision status;
3. valid action identifier;
4. valid action type;
5. canonical decision schema;
6. canonical action schema;
7. deterministic serialization;
8. deterministic ordering;
9. decision immutability;
10. action immutability;
11. decision/action separation;
12. explicit criteria;
13. provenance separation;
14. evidence separation;
15. belief separation;
16. Prediction Error separation;
17. Attribution separation;
18. Competing Hypotheses separation;
19. temporal ordering;
20. unresolved-state representation;
21. rejection of arbitrary action under insufficient information;
22. external-model provenance;
23. rejection of post-hoc rewriting;
24. rejection of authorization through decision status;
25. rejection of execution through Action Proposal;
26. rejection of direct TUU bypass;
27. expected-effects versus observed-results distinction;
28. no automatic belief update;
29. no mutation of prior cognitive blocks;
30. cognitive/authorization/execution separation;
31. stable Decision Assessment identity;
32. stable Action Proposal identity;
33. explicit Decision Assessment reference for every Action Proposal;
34. deterministic multi-proposal ordering by `action_id` without semantic ranking;
35. evaluator_id provenance when a deterministic evaluator is used;
36. rationale cannot encode hidden evidence, criteria, or authority;
37. expected effects do not automatically become B1 Prediction Commitments;
38. unresolved decisions cannot be represented as determined action decisions.

## 22. Boundary B1–B6–TUU–HEPHAESTUS

The intended cognitive sequence is:

```text
B1 Prediction Commitment
-> B2 Belief State
-> B3 Prediction Error
-> B4 Error Attribution
-> B5 Competing Hypotheses
-> B6 Decision / Action Proposal
-> TUU authorization gate
-> HEPHAESTUS execution
-> new observation / evidence
```

Block 6 consumes explicit cognitive state. It does not replace or mutate Blocks 1–5.

Authorization remains outside Cognitive Core.

Execution remains outside Cognitive Core.

## 23. Acceptance Criteria

Block 6 is acceptable only when:

- the canonical schemas are exact and deterministic;
- decision and action proposal remain separate objects;
- criteria are explicit and reproducible;
- provenance is separate from canonical state;
- prior cognitive blocks remain immutable;
- unresolved states are explicit;
- expected effects remain distinct from observations;
- external model involvement is attributable;
- no decision or proposal grants authorization;
- no Block 6 path performs execution;
- TUU remains the authorization boundary;
- HEPHAESTUS remains the execution boundary;
- all required verification cases pass.

## 24. Authority Statement

Block 6 is an epistemic and proposal layer only.

It may represent what the Cognitive Core assesses and what action it proposes.

It does not determine what the system is authorized to do.

It does not execute actions.

It does not mutate governance.

TUU remains the sole authorization boundary, and HEPHAESTUS remains the execution boundary.
