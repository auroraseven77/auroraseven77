# Block 5 — Competing Hypotheses Contract

**Status:** DRAFT / AUDIT

**Version:** 0.1

**Scope:** Cognitive Core Block 5

## 0. Purpose

Define the minimal, deterministic and auditable representation of multiple explanatory hypotheses considered concurrently by the Cognitive Core.

Block 5 represents competing hypotheses. It does not establish objective truth, causal certainty, probability, belief update, or action authority.

## 1. Epistemic Separation

The following concepts MUST remain distinct:

- OBSERVATION — externally obtained result or evidence-bearing observation.
- EVIDENCE — information used to evaluate hypotheses.
- HYPOTHESIS — explanatory proposition represented by the Cognitive Core.
- PREDICTION — committed expected consequence associated with a hypothesis.
- PREDICTION_ERROR — discrepancy represented by Block 3.
- ERROR_ATTRIBUTION — candidate-cause assessment represented by Block 4.
- BELIEF — epistemic confidence represented by Block 2.
- HYPOTHESIS_SET — explicit collection of hypotheses considered concurrently.
- ACTION_PROPOSAL — proposed intervention.
- AUTHORIZATION — execution authority owned by TUU.

A hypothesis MUST NOT be treated as a fact merely because it belongs to a hypothesis set.

A competing-hypothesis set MUST NOT be treated as a probability distribution or ranking.

## 2. Canonical Relationship

The conceptual relationship is:

`hypothesis_inputs + comparison_context -> competing_hypothesis_state`

Block 5 MAY consume information from prior cognitive blocks, including predictions, prediction errors, attribution assessments, evidence and beliefs.

Prior committed objects MUST remain immutable.

Block 5 MUST NOT redefine the prediction comparison performed by Block 3 or the attribution assessment performed by Block 4.

## 3. Canonical Hypothesis Object

Each hypothesis in a competing set MUST have a canonical representation:

```json
{
  "hypothesis_id": "<string>",
  "proposition": "<json-value>"
}
```

## 4. Canonical Competing Hypothesis Set

The canonical competing-hypothesis representation MUST contain:

```json
{
  "hypotheses": [
    {
      "hypothesis_id": "<string>",
      "proposition": "<json-value>"
    }
  ],
  "timestamp_logical": "<integer>"
}
```

The canonical object contains exactly:

1. hypotheses
2. timestamp_logical

The hypothesis collection MUST contain at least two distinct hypotheses when represented as a competing set.

Each `hypothesis_id` MUST be unique within a competing-hypothesis set.

Hypothesis ordering MUST be deterministic for canonical serialization.

Ordering MUST NOT imply preference, probability, causal priority, confidence, or ranking.

## 5. Competition Semantics

Competing hypotheses are hypotheses that are concurrently considered as alternative explanatory propositions for a declared cognitive question or context.

Competition MUST NOT mean that exactly one hypothesis is correct.

Multiple hypotheses MAY remain viable under the available evidence.

Block 5 MUST preserve explicit ambiguity when available information does not discriminate between hypotheses.

## 6. Hypothesis Identity

`hypothesis_id` identifies the hypothesis proposition.

The identifier MUST remain stable for the same proposition within the declared hypothesis lineage.

Changing the proposition MUST NOT silently mutate an established hypothesis.

A materially different proposition MUST receive a distinct hypothesis identity.

## 7. Belief Separation

Belief values belong to Block 2.

The competing-hypothesis canonical object MUST NOT contain belief values in this version.

Block 5 MUST NOT automatically update Belief State.

`BELIEF_UNRESOLVED` MUST remain an explicit epistemic state and MUST NOT be converted into a numeric value by Block 5.

## 8. Evidence and Prediction Error Separation

Evidence used to compare hypotheses MUST remain provenance or input context separate from the canonical hypothesis objects.

A Prediction Error MAY motivate consideration of competing hypotheses.

A Prediction Error MUST NOT be rewritten by Block 5 to favor one hypothesis.

An attribution assessment MAY provide candidate explanatory information, but Block 5 MUST NOT silently convert attribution status into hypothesis truth.

## 9. Attribution Separation

A candidate cause in an Attribution Assessment MAY correspond to a hypothesis only when that mapping is explicit in the supplied inputs or provenance.

Block 5 MUST NOT automatically equate a supported attribution candidate with a true hypothesis.

Attribution status MUST remain distinct from hypothesis status.

## 10. Hypothesis Set Immutability

Once a competing-hypothesis state is represented, its canonical content MUST be immutable.

Adding a hypothesis MUST produce a new hypothesis-set state.

Removing a hypothesis MUST produce a new hypothesis-set state.

Replacing or modifying a hypothesis proposition MUST produce a new hypothesis-set state and MUST NOT mutate the prior state.

Prior hypothesis-set states MUST remain available through their external provenance or audit record when persistence is provided by the surrounding architecture.

## 11. Temporal Ordering

The `timestamp_logical` of a competing-hypothesis state MUST identify its logical position in the cognitive sequence.

A derived comparison or assessment MUST NOT be represented with a logical timestamp earlier than an input state it claims to consume.

Block 5 MUST NOT retroactively alter an earlier hypothesis-set state.

## 12. Provenance

The canonical competing-hypothesis object MUST remain separate from provenance metadata.

Provenance SHOULD identify, when applicable:

- the cognitive question or comparison context;
- hypothesis inputs and their source;
- referenced prediction commitments;
- referenced prediction errors;
- referenced attribution assessments;
- evidence used for comparison;
- comparison criteria;
- evaluator identity;
- logical timestamp;
- external model involvement, if any.

For deterministic cross-block traceability, provenance MAY contain the following optional reference collections:

- `prediction_commitment_refs`: zero or more B1 `prediction_hash` values;
- `prediction_error_refs`: zero or more pairs `(prediction_hash, timestamp_logical)` identifying B3 Prediction Errors;
- `attribution_assessment_refs`: zero or more pairs `(prediction_hash, prediction_error_timestamp_logical)` identifying B4 Attribution Assessments.

Reference collections MUST remain provenance-only and MUST NOT be inserted into the canonical hypothesis-set object.

When present, reference collections MUST have deterministic ordering and MUST identify prior artifacts without copying their canonical content.

Missing references MUST NOT be silently replaced with inferred facts.

Provenance metadata MUST NOT be inserted into the canonical hypothesis-set object in a way that changes its defined schema.

## 13. Explicit Comparison Criteria

Any comparison, assessment, compatibility determination, or exclusion statement between hypotheses MUST use explicitly declared criteria.

Criteria MUST define what is being evaluated and MUST be identifiable and reproducible from provenance.

Criteria MUST NOT be changed silently after evidence or prediction error is known.

A new criterion MUST produce a new assessment rather than rewriting a prior assessment.

Criteria MUST NOT encode a preferred hypothesis merely to force a resolution.

A comparison result MUST NOT be interpreted as probability, belief, truth, or authorization unless a later block explicitly defines such a distinct representation.

## 14. Unknown and Not-Yet-Decidable

When available information does not discriminate between competing hypotheses, Block 5 MUST preserve the unresolved state explicitly.

UNKNOWN or NOT_YET_DECIDABLE MAY be represented in external assessment or provenance when appropriate.

An unresolved comparison MUST NOT fabricate a preferred hypothesis.

An unresolved comparison MUST NOT be converted into a numeric belief value.

Lack of discrimination between hypotheses MUST remain distinguishable from evidence that a hypothesis is false.

## 15. No Forced Elimination

Block 5 MUST NOT eliminate a hypothesis solely because another hypothesis is present.

Block 5 MUST NOT eliminate a hypothesis solely because another hypothesis has higher belief in Block 2.

Block 5 MUST NOT eliminate a hypothesis solely because an attribution candidate is marked SUPPORTED in Block 4.

Block 5 MUST NOT eliminate a hypothesis solely because evidence is incomplete.

Deterministic serialization order MUST NOT be used as an elimination criterion.

Any exclusion MUST be supported by an explicit criterion and a reconstructible assessment.

Exclusion under one declared context MUST NOT be interpreted as universal falsity of the hypothesis.

## 16. Determinism

Given identical hypothesis inputs, comparison context, criteria, provenance and logical timestamp, Block 5 MUST produce the same canonical representation.

Block 5 MUST NOT depend on randomness, wall-clock time, hidden global state, or nondeterministic iteration.

Canonical hypothesis ordering MUST be explicitly defined and reproducible.

Canonical ordering MUST have no semantic meaning of preference, probability, causal priority, confidence, or ranking.

## 17. No Automatic Hypothesis Generation

Block 5 represents hypotheses supplied through explicit cognitive inputs.

Automatic hypothesis generation MUST NOT occur implicitly through randomness, hidden state, or an unrecorded external mechanism.

A hypothesis proposed by an external model MAY be supplied as an explicit input only when its provenance is preserved.

External model output MUST NOT receive causal or epistemic authority merely because the external model proposed it.

Any later transformation of an externally proposed hypothesis MUST remain explicit and auditable.

## 18. No Automatic Belief Update

Block 5 MUST NOT modify Belief State automatically.

Membership in a competing hypothesis set MUST NOT itself change belief.

Comparison, compatibility, or exclusion results MUST NOT be silently converted into belief updates.

Any future belief update MUST occur through a distinct explicitly defined mechanism.

## 19. No Post-Hoc Rationalization

Block 5 MUST NOT rewrite a prior prediction, observation, prediction error, attribution assessment, or previously represented hypothesis-set state.

A hypothesis introduced after an observation or Prediction Error MAY be included in a new hypothesis-set state, but its provenance MUST preserve that it was introduced later.

Historical availability of evidence MUST NOT be retroactively altered.

Post-observation hypothesis consideration MUST NOT be represented as though the hypothesis had been committed before the observation unless that prior commitment actually existed.

## 20. Cognitive and Authorization Separation

Block 5 is an epistemic representation mechanism only.

Block 5 MUST NOT execute actions.

Block 5 MUST NOT authorize actions.

Block 5 MUST NOT modify governance or policy.

Block 5 MUST NOT write directly to the authoritative ledger.

Block 5 MUST NOT bypass TUU as the action and authorization gate.

A hypothesis, hypothesis-set membership, comparison result, or exclusion result MUST NOT be interpreted as permission to execute.

Block 5 MAY provide information to a later ACTION_PROPOSAL mechanism, while authorization remains outside the Cognitive Core.

## 21. Non-Goals

This block does NOT define:

- Bayesian inference, likelihoods, posteriors, or causal probabilities;
- automatic belief updates;
- autonomous action selection or execution;
- authorization or policy mutation;
- LLM causal or epistemic authority;
- hidden or unrecorded hypothesis generation;
- active inference or experiment selection;
- new cryptographic primitives;
- new persistence or ledger mechanisms;
- modifications to TUU governance.

## 22. Required Verification

An implementation claiming conformance to Block 5 MUST verify at minimum:

1. valid hypothesis representation;
2. stable hypothesis identity;
3. competing set requires at least two distinct hypotheses;
4. unique hypothesis identifiers within a set;
5. deterministic canonical representation;
6. deterministic ordering without semantic ranking;
7. hypothesis-set immutability;
8. adding a hypothesis creates a new state;
9. removing a hypothesis creates a new state;
10. replacing a proposition creates a new state;
11. valid temporal ordering;
12. explicit provenance;
13. explicit comparison criteria;
14. preservation of multiple viable hypotheses;
15. explicit unresolved or not-yet-decidable state;
16. rejection of forced elimination;
17. separation from Belief State;
18. separation from Prediction Error;
19. separation from Error Attribution;
20. rejection of post-hoc rewriting;
21. rejection of implicit hypothesis generation;
22. rejection of automatic belief update;
23. separation from authorization and execution.

## 23. Cognitive Core Boundary

The Cognitive Core sequence is:

B1 Prediction Commitment -> B2 Belief State -> B3 Prediction Error -> B4 Error Attribution -> B5 Competing Hypotheses -> B6 Decision / Action Proposal.

Block 5 consumes explicit hypotheses and relevant cognitive evidence.

Block 5 does not perform the responsibilities of B2, B3, B4, or B6.

## 24. Acceptance Criteria

Block 5 is acceptable only if its implementation:

- represents competing hypotheses explicitly;
- preserves deterministic canonical serialization;
- preserves hypothesis identity and historical immutability;
- preserves ambiguity when evidence does not discriminate;
- separates hypotheses from belief, prediction error, and attribution;
- records sufficient provenance for reproducibility;
- prevents post-hoc rewriting;
- prevents implicit generation and automatic belief update;
- contains no execution or authorization path.

## 25. Authority Statement

Block 5 represents epistemic state only.

It has no authority to execute actions, authorize actions, mutate governance, mutate prior cognitive objects, or bypass TUU.

The intended flow remains:

`Cognitive Core -> Competing Hypotheses -> future reasoning / Decision Proposal -> TUU gate -> HEPHAESTUS`

No hypothesis, comparison result, membership state, or exclusion result may bypass the TUU authorization boundary.
