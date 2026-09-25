# Aurora Cognitive Core — Block 0

## Purpose

Establish the architectural boundary between the Cognitive Core
and the existing Aurora Phase 1 governance system.

The Cognitive Core is an epistemic component. It may observe,
form hypotheses, form predictions, maintain beliefs, attribute
uncertainty, and propose actions.

It does not possess execution or authorization authority.

## Authority Boundary

The Cognitive Core MUST NOT:

- execute commands;
- authorize actions;
- modify governance contracts;
- write directly to the audit ledger;
- bypass TUU;
- mutate committed predictions;
- convert belief into authorization.

Authorization remains exclusively under the existing TUU gate.

## Existing Components Reused

The Cognitive Core is designed to compose with:

- `aurora_phase1.core.crypto`
- `aurora_phase1.core.ledger`
- `aurora_phase1.core.tuu`
- `aurora_phase1.core.executor`
- `aurora_phase1.core.reconstruct`
- `aurora_phase1.core.agent`

No duplicate governance or ledger implementation is permitted.

## Epistemic Scope

Future blocks may introduce:

- prediction commitments;
- belief state;
- provenance;
- error attribution;
- competing hypotheses;
- experiment selection;
- uncertainty states.

Block 0 intentionally implements none of these mechanisms.

Its purpose is to establish the boundary before behavior is added.

## Non-Goals

This block does not implement:

- LLM integration;
- Bayesian inference;
- active inference;
- experiment planning;
- quantum integration;
- hardware execution;
- autonomous execution;
- external data providers.

## Principle

Cognitive state and authorization state are separate domains.

A belief, hypothesis, prediction, or proposed action does not
constitute authorization to execute that action.
