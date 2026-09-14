"""
Optimizer-independent expressivity probe for proxy_vqe_tfim_n6_v1.

This script is intentionally self-contained. It uses the declared 1D TFIM
Hamiltonian and the stated 2-layer Ry + linear-CZ ansatz, but it does NOT
assume that this reconstruction is identical to the original VQE run.

Classification: SIMULATION / PROXY.
No hardware execution and no TUU validation are implied.
"""
import hashlib
import json
from pathlib import Path

import numpy as np

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
N_SAMPLES = 10_000
SEED = 42

H = tfim(N, J=1.0, h=1.0, periodic=True)
E_exact = float(np.linalg.eigvalsh(H)[0])

rng = np.random.default_rng(SEED)
best_E = np.inf
best_theta = None
samples = []

for _ in range(N_SAMPLES):
    theta = rng.uniform(-np.pi, np.pi, size=LAYERS * N)
    e = energy(theta, H, N, LAYERS, periodic_cz=False)
    samples.append(e)
    if e < best_E:
        best_E = e
        best_theta = theta.copy()

samples = np.asarray(samples)

out = {
    "stage": "SIMULATION",
    "model_scope": "PROXY",
    "method": "random_sampling_no_optimizer",
    "N": N,
    "layers": LAYERS,
    "periodic_cz": False,
    "n_params": LAYERS * N,
    "n_samples": N_SAMPLES,
    "seed": SEED,
    "E_exact": E_exact,
    "E_best_random": float(best_E),
    "E_mean_random": float(samples.mean()),
    "E_std_random": float(samples.std()),
    "E_minus_2sigma": float(best_E - 2 * samples.std()),
    "reference_VQE_E": -7.28084,
    "best_theta_sha256": hashlib.sha256(
        np.round(best_theta, 12).tobytes()
    ).hexdigest(),
    "comparison_status": "PROVENANCE_UNRESOLVED",
    "comparison_note": (
        "The random probe uses the reconstructed ansatz stated in the run manifest. "
        "Its result cannot by itself prove identity with the original VQE implementation; "
        "the original run.py/source revision must be inspected."
    ),
}

Path("random_sampling.json").write_text(json.dumps(out, indent=2) + "\n")
print(json.dumps(out, indent=2))
