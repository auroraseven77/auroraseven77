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

## Lifecycle and non-automatic transitions

Epistemic status MUST advance only when the corresponding evidence is produced. There is no automatic transition between stages:

```text
DECLARED_CONFIGURATION
        ↓
      MOCK
        ↓
   SIMULATION
        ↓
   EXPERIMENT
```

A declared topology is not hardware evidence. A mock result is not a simulation result. A simulation result is not an experiment. An `LLM_REASONING` result never enters this chain merely because it contains numerical values.

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

The proxy must compare against a declared baseline before any claim of improvement. For a small proxy, an exact classical reference is expected and is a correctness/reproducibility control, not something that must be outperformed to justify running the test. Suitable baselines include:

- exact diagonalization for a small instance;
- a different ansatz under the same Hamiltonian;
- a fixed optimizer budget;
- a classical reference solver appropriate to the model.

The purpose of the first proxy stage is to establish correctness, convergence and reproducibility. It MUST NOT require an alleged quantum advantage as a prerequisite. Any claim of speedup, residual-error improvement, fidelity improvement or other performance gain requires a declared baseline and uncertainty/error information where applicable. A statement that a VQE result is “not classically achievable” is not a general acceptance criterion for this proxy stage.

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

## Backend contract testing

The mock Device Gateway path MUST be tested through explicit contract invariants before any real-backend integration is attempted. At minimum:

- `shots` is an integer satisfying the backend's declared domain (for a sampling execution, normally `shots >= 0` or a stricter documented lower bound);
- `1 <= n_qubits <= max_qubits` for every submitted circuit;
- when topology is declared `all-to-all`, every distinct pair `(i,j)` satisfies `connected(i,j) == True` **within the declared topology model**;
- virtual-to-physical mapping is a bijection for the qubits actually used;
- compilation rejects unsupported gates or malformed OpenQASM rather than silently accepting them;
- execution returns a stable job identifier/handle and a schema-valid result;
- result metadata explicitly identifies `MOCK` when mock execution is used;
- no mock result contains metadata implying hardware execution or calibration provenance;
- error states are deterministic and machine-checkable.

The lifecycle MUST define job states explicitly, for example:

```text
CREATED → RUNNING → COMPLETED
                   ↘ FAILED
CREATED/RUNNING → CANCELLED
```

`cancel_job`/`cancel()` behavior for terminal states MUST be specified by contract. Cancelling an already `COMPLETED` job MUST NOT be assumed to be valid: the implementation may define it as a no-op, a controlled error, or another explicit terminal-state response. Likewise, `get_result()` on a non-terminal job must have a defined behavior.

## pytket / Quantinuum compatibility boundary

Similarity of method names is **not** evidence of compatibility with `pytket-quantinuum` or another Quantinuum SDK.

Compatibility MUST be demonstrated against a pinned, explicitly identified SDK/framework version and its actual contracts, including where applicable:

- circuit compilation and supported operations;
- backend capability predicates;
- submission/process semantics;
- job handle type and lifecycle;
- result retrieval format;
- cancellation semantics;
- backend/device metadata;
- error and retry behavior.

Until those tests are executed against the target version, the repository MUST describe the adapter as **interface-shaped / intended integration**, not as proven SDK compatibility.

## Declared topology boundary

A JSON topology describing a complete graph is a mathematical model of the declared configuration. For `n` qubits, the number of unordered edges is:

\[
E = \binom{n}{2} = \frac{n(n-1)}{2}.
\]

Thus a declared 56-node complete graph contains 1540 unordered edges, while a declared 20-node complete graph contains 190. This verifies the internal graph arithmetic only.

All-to-all connectivity, if independently verified for the actual backend, can eliminate connectivity-driven SWAP routing for pairs that are simultaneously addressable. It does **not** by itself establish that arbitrary OpenQASM3 is directly executable: native-gate decomposition, compilation, scheduling, transport/motion constraints, calibration, parallelism and backend-specific predicates still apply.

`identity mapping` is therefore valid as a graph-theoretic bijection under a declared complete graph, but its operational validity MUST be verified against the actual backend/compiler contract.

## Fidelity/error model boundary

For exploratory sensitivity analysis under independent identical two-qubit error probability `p` across `N` gates, the simple model

\[
F_{est} \approx (1-p)^N
\]

may be used as an **analytical model only**. It is not a hardware fidelity measurement and MUST NOT be substituted for measured circuit fidelity.

Real execution may involve correlated errors, SPAM/readout error, decoherence, crosstalk, transport/motion effects, compilation changes, leakage and other mechanisms. Per-gate averages cannot be extrapolated to a deep VQE circuit without an explicit model and uncertainty analysis.

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
