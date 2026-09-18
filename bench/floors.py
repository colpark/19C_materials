"""I1: fixed mechanical compositions (no agent). Hyperparameters were fixed a priori; none were tuned on outcomes.

Task: choose where to measure EQE on the composition line. Budget: B_EQE photoelectrochemistry
measurements and B_XRD diffraction measurements. Score = best EQE found / best EQE on the line,
clipped at 0. This is a graded realized value per episode, the intervene / choose-next-measurement readout.
"""
from __future__ import annotations
import functools, hashlib, inspect, json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import data, classical, fm

B_EQE = int(os.environ.get("FMAB_B_EQE", "5"))   # run 1: 5; rev2 amendment A-04: 3 (from seed S2, 11% of the line)
B_XRD = int(os.environ.get("FMAB_B_XRD", "5"))
BETA, LENGTH = 2.0, 0.08
EHULL_T, BUMP_W = 0.05, 0.05      # eV/atom stability temperature, Sb-fraction bump width


def score(ep, measured):
    y = np.array(ep["eqe"])
    best = max(0.0, max(y[list(measured)])) if measured else 0.0
    return best / max(y.max(), 1e-12)


def chance(ep, b=B_EQE):
    """Exact expected normalized best-of-b under uniform random allocation without replacement."""
    y = np.sort(np.clip(np.array(ep["eqe"]), 0, None))[::-1] / max(max(ep["eqe"]), 1e-12)
    n = len(y); tot = math.comb(n, b)
    # P(best is the i-th largest) = C(n-1-i, b-1)/C(n,b)
    return float(sum(y[i] * math.comb(n - 1 - i, b - 1) / tot for i in range(n - b + 1)))


def xrd_points(ep, k=B_XRD):
    """k evenly spaced XRD positions (by composition rank) along the line."""
    n = len(ep["sb"])
    return sorted({int(round(i)) for i in np.linspace(0, n - 1, k + 2)[1:-1]})


@functools.lru_cache(maxsize=None)
def phase_patterns(el):
    """Simulated patterns of every MP ternary and binary phase in el-Sb-O (<= MAX_SITES sites)."""
    out = []
    for sysl in ([el, "Sb", "O"], [el, "O"], ["Sb", "O"]):
        for r in fm.chemsys_structures(sysl):
            if r["nsites"] > fm.MAX_SITES: continue
            s = fm.to_structure(r)
            out.append(dict(id=r["id"], formula=r["formula"], ternary=len(sysl) == 3, y=classical.simulate(s, r["id"])))
    return out


def fm_rows(el):
    return {r["id"]: r for r in json.load(open(os.path.join(fm.CACHE, "fm_summary", f"{el}.json")))["rows"]
            if "ef_eV_atom" in r}


def phase_weight(el, pid, led_eV, use_mace=True, use_gap=True):
    r = fm_rows(el).get(pid)
    if r is None: return 0.0
    w = 1.0
    if use_mace: w *= math.exp(-r["ehull_eV_atom"] / EHULL_T)
    if use_gap and r.get("ternary"):
        g = r.get("megnet_gap_hse_eV", 0.0)
        w *= 1.0 if (0.5 <= g <= led_eV + 0.3) else 0.3
    return w


def xrd_prior(ep, xidx, weights=None):
    """Ternary-phase evidence along the line from XRD matching, interpolated between XRD points."""
    p = data.plates()[ep["plate_id"]]
    pats = phase_patterns(ep["el"])
    ev = []
    for i in xidx:
        ym = classical.measured_on_grid(p["Q"], p["xrd"][ep["nearest_xrd"][i]])
        t = [classical.match(ym, q["y"]) * (weights.get(q["id"], 0.0) if weights else 1.0) for q in pats if q["ternary"]]
        b = [classical.match(ym, q["y"]) for q in pats if not q["ternary"]]
        ev.append(max(t or [0]) - (0 if weights else 0.5 * max(b or [0])))
    ev = np.array(ev)
    ev = (ev - ev.min()) / (np.ptp(ev) or 1.0)
    sb = np.array(ep["sb"])
    return np.interp(sb, sb[xidx], ev)


def fm_prior(ep, use_mace=True, use_gap=True):
    sb = np.array(ep["sb"]); pr = np.zeros_like(sb)
    for pid, r in fm_rows(ep["el"]).items():
        if not r.get("ternary") or r.get("sb_frac") is None: continue
        w = phase_weight(ep["el"], pid, ep["led_eV"], use_mace, use_gap)
        pr += w * np.exp(-0.5 * ((sb - r["sb_frac"]) / BUMP_W) ** 2)
    return pr / (pr.max() or 1.0)


def run_gp(ep, prior=None):
    x = np.array(ep["sb"]); y = np.clip(np.array(ep["eqe"]), 0, None)
    measured, obs = [], []
    for t in range(B_EQE):
        if t == 0:
            i = int(np.argmax(prior)) if prior is not None else len(x) // 2
        else:
            i, _, _ = classical.ucb_next(x, measured, obs, beta=BETA, prior_mean=prior, length=LENGTH)
        measured.append(i); obs.append(y[i])
    return measured


COMPOSITIONS = {
    "cls_gp":      lambda ep: run_gp(ep),
    "cls_xrd":     lambda ep: run_gp(ep, xrd_prior(ep, xrd_points(ep))),
    "fm_prior":    lambda ep: run_gp(ep, fm_prior(ep)),
    "fm_xrd":      lambda ep: run_gp(ep, xrd_prior(ep, xrd_points(ep), {pid: phase_weight(ep["el"], pid, ep["led_eV"]) for pid in fm_rows(ep["el"])})),
    "fm_xrd_nogap": lambda ep: run_gp(ep, xrd_prior(ep, xrd_points(ep), {pid: phase_weight(ep["el"], pid, ep["led_eV"], use_gap=False) for pid in fm_rows(ep["el"])})),
    "fm_xrd_nomace": lambda ep: run_gp(ep, xrd_prior(ep, xrd_points(ep), {pid: phase_weight(ep["el"], pid, ep["led_eV"], use_mace=False) for pid in fm_rows(ep["el"])})),
}


def code_hash():
    src = "".join(inspect.getsource(m) for m in (classical, sys.modules[__name__]))
    return hashlib.sha256(src.encode()).hexdigest()[:16]


if __name__ == "__main__":
    import csv
    out = os.environ.get("FMAB_FLOORS_OUT", os.path.join(data.ROOT, "instrument", "floors.csv"))
    rows = []
    for ep in data.episodes():
        r = dict(episode_id=ep["episode_id"], el=ep["el"], plate=ep["plate_id"], led=ep["rtech"],
                 n_cand=len(ep["sb"]), max_eqe=round(max(ep["eqe"]), 5), chance=round(chance(ep), 5))
        for k, f in COMPOSITIONS.items():
            m = f(ep); r[k] = round(score(ep, m), 5); r[k + "_picks"] = " ".join(map(str, m))
        rows.append(r); print(r["episode_id"], {k: r[k] for k in ["chance"] + list(COMPOSITIONS)}, flush=True)
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print("code_hash", code_hash())
