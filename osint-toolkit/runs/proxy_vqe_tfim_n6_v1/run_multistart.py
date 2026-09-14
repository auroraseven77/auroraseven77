"""
Optimizer-independent expressivity probe for proxy_vqe_tfim_n6_v1.

This script runs repeated COBYLA optimizations from independent random
initializations against the reconstructed 2-layer Ry + linear-CZ ansatz.
It is intentionally separate from the original VQE run because the original
run.py/source revision is not yet available in the repository.

Classification: SIMULATION / PROXY.
No hardware execution and no TUU validation are implied.

Interpretation rule:
- n_hits_below_reference_-7.28084 == 0 is evidence that this reconstructed
  family did not beat the reported VQE energy under these optimizer settings;
  it is NOT proof of ansatz identity or a mathematical expressivity bound.
- Any hits below the reference show that the reconstructed family can contain
  states better than the reported single-run result, supporting an optimizer
  limitation hypothesis (still without proving provenance identity).
"""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import minimize

I2 = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)


def _kron(ops):
    out = np.array([[1]], dtype=complex)
    for op in ops:
        out = np.kron(out, op)
    return out


def _single(n, op, site):
    ops = [I2] * n
    ops[site] = op
    return _kron(ops)


def _pair(n, a, sa, b, sb):
    ops = [I2] * n
    ops[sa], ops[sb] = a, b
    return _kron(ops)


def tfim(n, J=1.0, h=1.0, periodic=True):
    H = np.zeros((2**n, 2**n), dtype=complex)
    for i in range(n):
        j = (i + 1) % n
        if not periodic and j == 0:
            continue
        H -= J * _pair(n, Z, i, Z, j)
    for i in range(n):
        H -= h * _single(n, X, i)
    return H


def _ry(t):
    c, s = np.cos(t / 2), np.sin(t / 2)
    return np.array([[c, -s], [s, c]], dtype=complex)


_CZ = np.diag([1, 1, 1, -1]).astype(complex)


def _apply_1q(state, gate, site, n):
    t = state.reshape([2] * n)
    t = np.moveaxis(t, site, 0)
    shape = t.shape
    t = (gate @ t.reshape(2, -1)).reshape(shape)
    return np.moveaxis(t, 0, site).reshape(-1)


def _apply_cz(state, a, b, n):
    t = state.reshape([2] * n)
    t = np.moveaxis(t, [a, b], [0, 1])
    shape = t.shape
    t = (_CZ @ t.reshape(4, -1)).reshape(shape)
    return np.moveaxis(t, [0, 1], [a, b]).reshape(-1)


def ansatz(params, n, layers, periodic_cz=False):
    psi = np.zeros(2**n, dtype=complex)
    psi[0] = 1.0
    idx = 0
    for _ in range(layers):
        for q in range(n):
            psi = _apply_1q(psi, _ry(params[idx]), q, n)
            idx += 1
        for q in range(n - 1):
            psi = _apply_cz(psi, q, q + 1, n)
        if periodic_cz:
            psi = _apply_cz(psi, n - 1, 0, n)
    return psi


def energy(theta, H, n, layers, periodic_cz=False):
    psi = ansatz(theta, n, layers, periodic_cz)
    return float(np.real(psi.conj() @ H @ psi))


N = 6
LAYERS = 2
N_RESTARTS = 200
MAXITER = 500
RHOBEG = 0.5
TOL = 1e-6
REFERENCE_VQE_E = -7.28084

H = tfim(N, J=1.0, h=1.0, periodic=True)
E_exact = float(np.linalg.eigvalsh(H)[0])

results = []
for seed in range(N_RESTARTS):
    rng = np.random.default_rng(seed)
    theta0 = rng.uniform(-np.pi, np.pi, size=LAYERS * N)
    res = minimize(
        lambda theta: energy(theta, H, N, LAYERS, periodic_cz=False),
        theta0,
        method="COBYLA",
        options={"maxiter": MAXITER, "rhobeg": RHOBEG, "tol": TOL},
    )
    results.append(
        {
            "seed": seed,
            "fun": float(res.fun),
            "success": bool(res.success),
            "message": str(res.message),
            "nfev": int(getattr(res, "nfev", -1)),
        }
    )

values = np.asarray([item["fun"] for item in results], dtype=float)
best_index = int(np.argmin(values))

out = {
    "stage": "SIMULATION",
    "model_scope": "PROXY",
    "method": "COBYLA_multistart",
    "N": N,
    "layers": LAYERS,
    "periodic_cz": False,
    "n_params": LAYERS * N,
    "n_restarts": N_RESTARTS,
    "seed_policy": "seed=restart_index_0_to_199",
    "maxiter": MAXITER,
    "rhobeg": RHOBEG,
    "tol": TOL,
    "E_exact": E_exact,
    "best": float(values[best_index]),
    "median": float(np.median(values)),
    "p10": float(np.percentile(values, 10)),
    "p90": float(np.percentile(values, 90)),
    "n_hits_below_reference_-7.28084": int(np.sum(values < REFERENCE_VQE_E)),
    "n_hits_below_-7.5": int(np.sum(values < -7.5)),
    "n_hits_within_0.01_of_reference": int(
        np.sum(np.abs(values - REFERENCE_VQE_E) < 0.01)
    ),
    "n_converged_success": int(sum(item["success"] for item in results)),
    "nfev_median": float(np.median([item["nfev"] for item in results])),
    "nfev_min": int(min(item["nfev"] for item in results)),
    "nfev_max": int(max(item["nfev"] for item in results)),
    "reference_VQE_E": REFERENCE_VQE_E,
    "comparison_status": "PROVENANCE_UNRESOLVED",
    "interpretation": (
        "This probes the reconstructed ansatz family with repeated COBYLA starts. "
        "It does not establish identity with the original VQE implementation or "
        "constitute a mathematical global expressivity bound."
    ),
    "results": results,
}

Path("multistart.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, indent=2))
