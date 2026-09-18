"""I1 over the pooled corpus: the same four compositions as bench/floors.py, generalized to composition vectors.

Episodes: base antimonate episodes (bench/data.py, 2 cations: M, Sb) plus env/pool/episodes.jsonl.
Channels unchanged: GP-UCB (classical), XRD match vs MP phases (classical), MACE-MP-0 hull + MEGNet gap (FM),
from env/cache/fm_summary_general/<chem>.json. For 2-cation plates the candidate coordinate is the Sb (or second
cation) fraction and the XRD points are the run-1 linspace; for >= 3 cations XRD points are chosen by farthest-point
sampling from the composition centroid. Hyperparameters are run 1's, fixed a priori.
"""
from __future__ import annotations
import functools, json, math, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import data, classical, fm

ROOT = data.ROOT
B_EQE = int(os.environ.get("FMAB_B_EQE", "3")); B_XRD = int(os.environ.get("FMAB_B_XRD", "5"))
BETA, LENGTH, EHULL_T, BUMP_W = 2.0, 0.08, 0.05, 0.05
GEN = os.path.join(fm.CACHE, "fm_summary_general" + fm.MACE_TAG)


# ------------------------------------------------------------------ episodes, unified
@functools.lru_cache(maxsize=None)
def pooled_plates():
    out = {}
    d = os.path.join(ROOT, "env", "pool", "plates")
    if os.path.isdir(d):
        for f in os.listdir(d):
            z = np.load(os.path.join(d, f), allow_pickle=True)
            out[f[:-4]] = dict(Q=z["Q"], xrd=z["xrd"], xrd_comp=z["xrd_comp"], elements=[str(e) for e in z["elements"]])
    return out


@functools.lru_cache(maxsize=None)
def all_episodes():
    eps = []
    ex = {x["unit"] for x in json.load(open(os.path.join(ROOT, "discovery/corpus_ledger.json")))["exclusion_ledger"]}
    for e in data.episodes():
        if e["episode_id"] in ex: continue
        els = sorted([e["el"], "Sb"]); isb = els.index("Sb")
        comp = [[(s if i == isb else 1 - s) for i in range(2)] for s in e["sb"]]
        eps.append(dict(episode_id=e["episode_id"], source="base", plate_id=str(e["plate_id"]), chem="-".join(els),
                        elements=els, comp=comp, merit=e["eqe"], nearest_xrd=e["nearest_xrd"], led_eV=e["led_eV"]))
    p = os.path.join(ROOT, "env", "pool", "episodes.jsonl")
    if os.path.exists(p):
        for line in open(p):
            e = json.loads(line)
            ill = e.get("illum", {})
            led = ill.get("led_eV") or (1239.84 / ill["led_nm"] if ill.get("led_nm") else None)
            eps.append(dict(episode_id="P" + e["episode_id"], source="pool", plate_id=str(e["plate_id"]), chem=e["chem"],
                            elements=e["elements"], comp=e["comp"], merit=e["merit"], nearest_xrd=e["nearest_xrd"], led_eV=led))
    return eps


def plate_xrd(ep, j):
    if ep["source"] == "base":
        p = data.plates()[int(ep["plate_id"])]; return p["Q"], p["xrd"][j]
    p = pooled_plates()[ep["plate_id"]]; return p["Q"], p["xrd"][j]


def coords(ep):
    X = np.array(ep["comp"], float)
    return X[:, 1:2] if X.shape[1] == 2 else X      # 2 cations: 1D coordinate; else the vector


# ------------------------------------------------------------------ score, chance
def score(ep, measured):
    y = np.array(ep["merit"], float); best = max(0.0, max(y[list(measured)])) if measured else 0.0
    return best / max(y.max(), 1e-12)


def chance(ep, b=B_EQE):
    y = np.sort(np.clip(np.array(ep["merit"], float), 0, None))[::-1] / max(max(ep["merit"]), 1e-12)
    n = len(y); tot = math.comb(n, b)
    return float(sum(y[i] * math.comb(n - 1 - i, b - 1) / tot for i in range(n - b + 1)))


# ------------------------------------------------------------------ GP on composition vectors
def gp_post(Xo, yo, Xa, prior=None, length=LENGTH, noise=0.05):
    m_all = np.zeros(len(Xa)) if prior is None else np.asarray(prior, float)
    if len(Xo) == 0: return m_all, np.ones(len(Xa))
    scale = max(np.max(np.abs(yo)), 1e-9); yn = np.asarray(yo) / scale
    K = lambda A, B: np.exp(-0.5 * (((A[:, None, :] - B[None, :, :]) ** 2).sum(-1)) / length ** 2)
    idx_o = [int(np.argmin(((Xa - x) ** 2).sum(1))) for x in Xo]
    m_o = m_all[idx_o] if prior is not None else np.zeros(len(Xo))
    Koo = K(Xo, Xo) + noise * np.eye(len(Xo)); Kao = K(Xa, Xo)
    mu = m_all + Kao @ np.linalg.solve(Koo, yn - m_o)
    var = 1 - np.einsum("ij,ji->i", Kao, np.linalg.solve(Koo, Kao.T))
    return mu * scale, np.sqrt(np.clip(var, 1e-12, None)) * scale


def run_gp(ep, prior=None):
    X = coords(ep); y = np.clip(np.array(ep["merit"], float), 0, None); meas, obs = [], []
    for t in range(B_EQE):
        if t == 0:
            i = int(np.argmax(prior)) if prior is not None else (len(X) // 2 if X.shape[1] == 1 else int(np.argmin(((X - X.mean(0)) ** 2).sum(1))))
        else:
            mu, sd = gp_post(X[meas], obs, X, prior); s = mu + BETA * sd; s[meas] = -np.inf; i = int(np.argmax(s))
        meas.append(i); obs.append(y[i])
    return meas


def xrd_points(ep, k=B_XRD):
    X = coords(ep); n = len(X)
    if X.shape[1] == 1:
        order = np.argsort(X[:, 0])
        return sorted({int(order[int(round(i))]) for i in np.linspace(0, n - 1, k + 2)[1:-1]})
    sel = [int(np.argmin(((X - X.mean(0)) ** 2).sum(1)))]
    while len(sel) < k:
        d = np.min(((X[:, None, :] - X[sel][None, :, :]) ** 2).sum(-1), axis=1); sel.append(int(np.argmax(d)))
    return sorted(sel)


# ------------------------------------------------------------------ phases and FM rows
@functools.lru_cache(maxsize=None)
def fm_rows(chem):
    s = json.load(open(os.path.join(GEN, f"{chem}.json")))
    return {r["id"]: r for r in s["rows"] if "ehull_eV_atom" in r}


@functools.lru_cache(maxsize=None)
def phase_patterns(chem):
    """Classical: every MP phase in each cation subset + O, <= MAX_SITES (as run 1); independent of the FM cap."""
    import itertools
    cats = chem.split("-"); out = []
    for r_ in range(1, len(cats) + 1):
        for sub in itertools.combinations(cats, r_):
            for rec in fm.chemsys_structures(list(sub) + ["O"]):
                if rec["nsites"] > fm.MAX_SITES: continue
                out.append(dict(id=rec["id"], mixed=len(sub) >= 2, y=classical.simulate(fm.to_structure(rec), rec["id"])))
    return out


def phase_weight(chem, pid, led, use_mace=True, use_gap=True):
    r = fm_rows(chem).get(pid)
    if r is None: return 0.0
    w = math.exp(-r["ehull_eV_atom"] / EHULL_T) if use_mace else 1.0
    if use_gap and r.get("mixed") and led:
        g = r.get("megnet_gap_hse_eV", 0.0); w *= 1.0 if (0.5 <= g <= led + 0.3) else 0.3
    return w


def interp(X, xidx, v):
    if X.shape[1] == 1:
        o = np.argsort(X[xidx, 0]); return np.interp(X[:, 0], X[xidx, 0][o], np.asarray(v)[o])
    d = ((X[:, None, :] - X[xidx][None, :, :]) ** 2).sum(-1); w = 1 / (d + 1e-6); return (w @ np.asarray(v)) / w.sum(1)


def xrd_prior(ep, xidx, weights=None):
    pats = phase_patterns(ep["chem"]); ev = []
    for i in xidx:
        Q, I = plate_xrd(ep, ep["nearest_xrd"][i]); ym = classical.measured_on_grid(Q, I)
        t = [classical.match(ym, q["y"]) * (weights.get(q["id"], 0.0) if weights else 1.0) for q in pats if q["mixed"]]
        b = [classical.match(ym, q["y"]) for q in pats if not q["mixed"]]
        ev.append(max(t or [0]) - (0 if weights else 0.5 * max(b or [0])))
    ev = np.array(ev); ev = (ev - ev.min()) / (np.ptp(ev) or 1.0)
    return interp(coords(ep), xidx, ev)


def fm_prior(ep, use_mace=True, use_gap=True):
    X = coords(ep); pr = np.zeros(len(X))
    for pid, r in fm_rows(ep["chem"]).items():
        if not r.get("mixed"): continue
        v = np.array([r["frac"][e] for e in ep["elements"]])
        v = v[1:2] if len(v) == 2 else v            # same coordinate as coords(): run-1 1D bump on 2-cation plates
        w = phase_weight(ep["chem"], pid, ep["led_eV"], use_mace, use_gap)
        pr += w * np.exp(-0.5 * ((X - v) ** 2).sum(1) / BUMP_W ** 2)
    return pr / (pr.max() or 1.0)


def W(ep, **kw):
    return {pid: phase_weight(ep["chem"], pid, ep["led_eV"], **kw) for pid in fm_rows(ep["chem"])}


COMPOSITIONS = {
    "cls_gp": lambda ep: run_gp(ep),
    "cls_xrd": lambda ep: run_gp(ep, xrd_prior(ep, xrd_points(ep))),
    "fm_prior": lambda ep: run_gp(ep, fm_prior(ep)),
    "fm_xrd": lambda ep: run_gp(ep, xrd_prior(ep, xrd_points(ep), W(ep))),
    "fm_xrd_nogap": lambda ep: run_gp(ep, xrd_prior(ep, xrd_points(ep), W(ep, use_gap=False))),
    "fm_xrd_nomace": lambda ep: run_gp(ep, xrd_prior(ep, xrd_points(ep), W(ep, use_mace=False))),
}

if __name__ == "__main__":
    import csv
    out = os.environ.get("FMAB_FLOORS_OUT", os.path.join(ROOT, "rev21/pool/floors_pooled_B3.csv"))
    rows = []
    for ep in all_episodes():
        if not os.path.exists(os.path.join(GEN, f"{ep['chem']}.json")):
            print("skip (no FM summary)", ep["episode_id"], ep["chem"], flush=True); continue
        r = dict(episode_id=ep["episode_id"], source=ep["source"], chem=ep["chem"], plate=ep["plate_id"],
                 n_cand=len(ep["merit"]), dims=coords(ep).shape[1], max_merit=max(ep["merit"]), chance=round(chance(ep), 5))
        for k, f in COMPOSITIONS.items():
            r[k] = round(score(ep, f(ep)), 5)
        rows.append(r)
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    print("wrote", len(rows), "episodes to", out)
