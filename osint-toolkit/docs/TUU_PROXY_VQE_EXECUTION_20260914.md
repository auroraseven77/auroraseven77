# TUU Proxy VQE — Execution Record (2026-09-14)

## Evidence classification

- `stage`: `SIMULATION`
- `model_scope`: `PROXY`
- `topology_tag`: `DECLARED_CONFIGURATION`
- TUU validation: **NO**
- Hardware experiment: **NO**
- Experimental evidence: **NO**

> This is a PROXY of infrastructure only. It does not constitute evidence or validation of TUU. No hardware was used. The classical baseline is used exclusively as a control.

## Declared run configuration

- Hamiltonian: 1D transverse-field Ising model, open boundary
- Qubits: 4
- `J = 1.0`
- `h = 0.5`
- Ansatz: `RealAmplitudes`, 4 qubits, 2 repetitions, linear entanglement
- Optimizer: COBYLA
- Maximum optimizer iterations: 100
- Seed: 42
- Estimator: `StatevectorEstimator`

## Reported execution results

The following values are recorded from the execution report supplied for this run:

| Quantity | Value |
|---|---:|
| Exact classical baseline | `-3.4270340889` |
| VQE optimum | `-3.3789120813` |
| Absolute error | approximately `4.81e-2` |
| Optimizer evaluations | `100` |
| Timestamp | `20260914T231532Z` |
| Report SHA-256 | `355a623b9fd76a89a64f5fc45f5c0375fce8810d142d0791b48efb954ac70c10` |

The numerical record above is intentionally preserved as an execution claim/report record rather than upgraded to independent experimental evidence.

## Expected artifacts

The execution report identifies the following artifacts:

```text
run_proxy_vqe.py
proxy_vqe_report_20260914T231532Z.json
proxy_vqe_report_20260914T231532Z.sha256
proxy_vqe_summary_20260914T231532Z.txt
device_topology_reimei_h2.json
```

The topology file is explicitly classified as `DECLARED_CONFIGURATION`; it must not be interpreted as a hardware measurement.

## Reproducibility boundary

The report states that all run parameters were fixed a priori, code and logs were retained, and hashes were generated. However, this repository commit records the **execution metadata supplied to the project**, not the raw execution directory itself. The raw files must be ingested before their contents, hashes, or byte-level provenance can be independently verified from Git history.

Therefore:

```text
INFRASTRUCTURE      : READY
PROXY SIMULATION    : REPORTED EXECUTED
TUU HAMILTONIAN     : MISSING
TUU SIMULATION      : BLOCKED
HARDWARE EXPERIMENT : BLOCKED
RAW ARTIFACT INGEST : PENDING
```

## Topology sanity checks

For a complete graph, the number of unordered qubit pairs is:

`n(n-1)/2`

Thus:

- `n = 56` → `1540` pairs
- `n = 20` → `190` pairs

These are mathematical consequences of the declared all-to-all topology and are not measurements of a physical device.

## Mock contract boundary

A mock/provider contract may validate interface invariants such as:

- `shots >= 1`;
- requested qubit count within the declared device limit;
- all distinct qubit pairs connected when all-to-all connectivity is declared;
- expected lifecycle methods such as `compile()`, `execute()`, and `cancel()` obey their software contract.

Passing such tests validates the mock/adapter contract only. It does not establish that a real backend supplied the same behavior.

## Simple gate-error illustration

For an intentionally simplified independent-error model,

`F_est ≈ (1 - p_2Q)^N_2Q`

For `N_2Q = 100`:

- `p_2Q = 1e-3` → approximately `90.5%`
- `p_2Q = 1.6e-3` → approximately `85.2%`

This is a sensitivity illustration, not a hardware fidelity measurement and not a complete noise model.

## Scientific gate

The next scientific gate is the formal TUU Hamiltonian/Lagrangian and its quantitative, falsifiable predictions. Until those are explicit, this proxy run cannot be promoted to TUU simulation or experiment.
