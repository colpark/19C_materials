"""Classical tools: XRD peak extraction, XRD forward simulation (pymatgen), pattern matching, GP-UCB.

No learned model sits in this module. Every function is deterministic.
"""
from __future__ import annotations
import functools
import numpy as np
from scipy.signal import find_peaks
from pymatgen.analysis.diffraction.xrd import XRDCalculator

Q_GRID = np.linspace(0.72, 5.5, 2400)   # 1/Angstrom; measured Q is nm^-1 / 10
SIGMA_Q = 0.012                          # 1/Angstrom Gaussian broadening, fixed a priori


def measured_on_grid(Q_nm, I):
    q = np.asarray(Q_nm) / 10.0
    y = np.interp(Q_GRID, q, np.asarray(I), left=0.0, right=0.0)
    y = y - np.percentile(y, 10)
    y[y < 0] = 0
    return y / (y.max() or 1.0)


def peaks(Q_nm, I, n=15):
    """Top-n peaks of a measured pattern: [(Q in 1/A, relative intensity 0-100)]."""
    y = measured_on_grid(Q_nm, I)
    idx, prop = find_peaks(y, prominence=0.04, distance=8)
    order = np.argsort(prop["prominences"])[::-1][:n]
    return sorted([(round(float(Q_GRID[i]), 3), round(float(100 * y[i]), 1)) for i in idx[order]])


@functools.lru_cache(maxsize=4096)
def _sim_cached(key, structure_json):
    from pymatgen.core import Structure
    s = Structure.from_str(structure_json, fmt="json")
    pat = XRDCalculator(wavelength="CuKa").get_pattern(s, two_theta_range=(10, 90))
    lam = 1.54184
    q = 4 * np.pi * np.sin(np.radians(np.asarray(pat.x) / 2)) / lam
    y = np.zeros_like(Q_GRID)
    for qi, yi in zip(q, pat.y):
        y += yi * np.exp(-0.5 * ((Q_GRID - qi) / SIGMA_Q) ** 2)
    return y / (y.max() or 1.0)


def simulate(structure, key=""):
    """Simulated powder pattern on Q_GRID for a pymatgen Structure (Cu K-alpha, 10-90 deg 2theta)."""
    return _sim_cached(key or str(hash(structure.to(fmt="json"))), structure.to(fmt="json"))


def sim_peaks(structure, key="", n=12):
    y = simulate(structure, key)
    idx, prop = find_peaks(y, prominence=0.03, distance=8)
    order = np.argsort(y[idx])[::-1][:n]
    return sorted([(round(float(Q_GRID[i]), 3), round(float(100 * y[i]), 1)) for i in idx[order]])


def match(y_meas, y_sim, max_shift=0.06):
    """Cosine similarity maximized over a rigid Q shift of up to +-max_shift (lattice strain / solid solution)."""
    best, step = -1.0, Q_GRID[1] - Q_GRID[0]
    k = int(max_shift / step)
    for s in range(-k, k + 1, 2):
        ys = np.roll(y_sim, s)
        c = float(np.dot(y_meas, ys) / (np.linalg.norm(y_meas) * np.linalg.norm(ys) + 1e-12))
        best = max(best, c)
    return round(best, 4)


# ------------------------------------------------------------------ GP-UCB over the composition line
def gp_posterior(x_obs, y_obs, x_all, length=0.08, noise=0.05, prior_mean=None):
    x_obs, y_obs, x_all = map(np.asarray, (x_obs, y_obs, x_all))
    m_all = np.zeros_like(x_all, dtype=float) if prior_mean is None else np.asarray(prior_mean, float)
    if len(x_obs) == 0:
        return m_all, np.ones_like(x_all, dtype=float)
    scale = max(np.max(np.abs(y_obs)), 1e-9)
    yn = np.asarray(y_obs) / scale
    m_obs = np.interp(x_obs, x_all, m_all) if prior_mean is not None else np.zeros_like(x_obs, float)
    K = lambda a, b: np.exp(-0.5 * ((a[:, None] - b[None, :]) / length) ** 2)
    Koo = K(x_obs, x_obs) + noise * np.eye(len(x_obs))
    Kao = K(x_all, x_obs)
    alpha = np.linalg.solve(Koo, yn - m_obs)
    mu = m_all + Kao @ alpha
    var = 1.0 - np.einsum("ij,ji->i", Kao, np.linalg.solve(Koo, Kao.T))
    return mu * scale, np.sqrt(np.clip(var, 1e-12, None)) * scale


def ucb_next(x_all, measured_idx, y_obs, beta=2.0, prior_mean=None, length=0.08):
    x_all = np.asarray(x_all)
    xo = x_all[list(measured_idx)]
    mu, sd = gp_posterior(xo, y_obs, x_all, length=length, prior_mean=prior_mean)
    score = mu + beta * sd
    score[list(measured_idx)] = -np.inf
    return int(np.argmax(score)), mu, sd
