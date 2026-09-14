# TUU Classical Proxy VQE — Boundary and Audit Specification

## Purpose

This document defines a reproducible classical VQE artifact that may be used to validate the **simulation infrastructure** before a TUU Hamiltonian exists.

It does **not** validate the TUU theory.

Until a public, explicit TUU Hamiltonian/Lagrangian is supplied and justified, every calculation in this track MUST be labeled `PROXY` and `SIMULATION`.

## Epistemic boundary

| Class | Meaning | Allowed claim |
|---|---|---|
| `INPUT` | Declared model, parameters, code/configuration | Defines the experiment/model; not a result |
| `ANALYTICAL` | Derivation from declared inputs | Mathematical consequence under stated assumptions |
| `SIMULATION` | Numerically executed classical simulation with preserved artifacts | Reproducible computational result |
| `EXPERIMENT` | Measurement from an identified physical backend | Hardware result, subject to provenance/statistics |
| `LLM_REASONING` | Number or statement produced only during language-model reasoning | Hypothesis/example only; never a simulation result |

Numbers generated without actually executing the simulator MUST NOT be described as `SIMULATION`.

## Proxy model

The initial proxy may use a small, established model such as a Kitaev toric-code instance or an Ising spin model with explicitly declared long-range couplings.

The proxy is an infrastructure test only. It must not be presented as evidence for:

- a TUU phase;
- topological protection of TUU;
- a TUU energy gap;
- a TUU correlation length;
- quantum advantage of TUU;
- experimental behavior of Reimei or any other QPU.

## Minimum reproducibility record

Every executed run MUST preserve:

- immutable source revision / commit;
- exact Hamiltonian definition and model parameters;
- qubit count;
- ansatz family, depth and parameter count;
- optimizer and all optimizer parameters;
- initial parameters and random seed, when applicable;
- convergence/stopping criteria;
- simulator backend and exact software versions;
- Python version and platform information;
- execution timestamp;
- full energy-vs-iteration trace;
- final parameters;
- observable definitions;
- statistical method and shots, if sampling is used;
- raw or lossless result artifacts;
- SHA-256 hashes of preserved artifacts.

## Required outputs

At minimum, an executed proxy run should produce:

```text
runs/<run_id>/
├── manifest.json
├── convergence.jsonl
├── observables.json
├── config.json
├── environment.json
└── artifacts.sha256
```

`manifest.json` MUST state `stage: "SIMULATION"` and `model_scope: "PROXY"`.

## Baseline discipline

The proxy must compare against a declared baseline before any claim of improvement. Examples include:

- exact diagonalization for a small instance;
- a different ansatz under the same Hamiltonian;
- a fixed optimizer budget;
- a classical reference solver appropriate to the model.

Speedup, residual error, fidelity, or convergence improvements MUST be reported together with the baseline definition and uncertainty/error information where applicable.

## Long-range correlation

A phrase such as "long-range entanglement correlation" is insufficient by itself. Before execution, define:

1. the operator or estimator;
2. the sites/qubit regions;
3. the separation metric;
4. normalization;
5. estimator and sampling procedure;
6. uncertainty calculation;
7. null/baseline model;
8. threshold or statistical decision rule.

If these are not frozen before execution, the result is exploratory and MUST NOT be used as a confirmatory claim.

## TUU gate

A proxy run does not unlock the TUU validation stage. The TUU stage remains blocked until the proponent supplies an explicit formal object, at minimum:

- Hamiltonian or Lagrangian;
- degrees of freedom;
- Hilbert/configuration space;
- coupling constants and units;
- symmetries/constraints;
- boundary conditions;
- mapping to qubits;
- target observables;
- quantitative predictions distinguishable from the chosen baseline.

Only after this gate can a simulation be labeled as a simulation **of the TUU model**, rather than a proxy demonstration.

## Hardware gate

No proxy result authorizes an `EXPERIMENT` claim. Hardware execution requires independent provenance for the actual backend, including backend identifier, timestamp, circuit revision, physical qubits used, compilation details, shots, calibration/noise context, raw measurements and hashes.

## Status

Current repository status:

```text
INFRASTRUCTURE: READY
PROXY SIMULATION: NOT YET EXECUTED
TUU HAMILTONIAN: MISSING
TUU SIMULATION: BLOCKED
HARDWARE EXPERIMENT: BLOCKED
```
