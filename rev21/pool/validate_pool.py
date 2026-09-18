"""Validate env/pool/episodes.jsonl and env/pool/plates/*.npz against rev21/pool/POOL_RULES.md.

Per episode: >=15 candidates (P-I4); one LED and one electrolyte (P-I2, single-valued fields);
cation fractions sum to 1 within 1e-3 and are >= 0 (P-I3); merit finite; nearest XRD within 0.05
(0.5*L1 over cation fractions), and it is the nearest one; plate npz exists with matching elements.
Also checks the ledger totals against the episode file. Prints PASS/FAIL per episode.

Usage: env/.venv/bin/python rev21/pool/validate_pool.py
"""
import json, math, os, sys
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EPS = os.path.join(ROOT, "env", "pool", "episodes.jsonl")
PLATES = os.path.join(ROOT, "env", "pool", "plates")
LEDGER = os.path.join(ROOT, "rev21", "pool", "pool_ledger.json")
KEYS = ["episode_id", "plate_id", "chem", "elements", "comp", "merit", "merit_name", "illum", "ph",
        "electrolyte", "nearest_xrd", "xrd_dist", "source_records"]

_npz = {}


def plate(pid):
    if pid not in _npz:
        p = os.path.join(PLATES, f"{pid}.npz")
        _npz[pid] = np.load(p, allow_pickle=False) if os.path.exists(p) else None
    return _npz[pid]


def check_plate(pid):
    z = plate(pid)
    if z is None:
        return ["plate npz missing"]
    errs = []
    for k in ("Q", "xrd", "xrd_comp", "elements", "substrate", "annealT_C"):
        if k not in z.files:
            errs.append(f"npz lacks {k}")
    if errs:
        return errs
    Q, X, C = z["Q"], z["xrd"], z["xrd_comp"]
    if Q.ndim != 1 or not np.all(np.diff(Q) > 0):
        errs.append("Q not 1D ascending")
    if X.ndim != 2 or X.shape[1] != len(Q) or X.shape[0] != C.shape[0] or X.shape[0] == 0:
        errs.append(f"xrd shape {X.shape} vs Q {Q.shape} / xrd_comp {C.shape}")
    if not np.isfinite(X).all():
        errs.append("xrd not finite")
    if C.shape[1] != len(z["elements"]):
        errs.append("xrd_comp width != len(elements)")
    if np.abs(C.sum(1) - 1).max() > 1e-3 or (C < -1e-9).any():
        errs.append("xrd_comp rows not fractions summing to 1")
    if list(z["elements"]) != sorted(z["elements"]):
        errs.append("npz elements not sorted")
    return errs


def check_episode(e, seen):
    errs = []
    for k in KEYS:
        if k not in e:
            errs.append(f"missing {k}")
    if errs:
        return errs
    if e["episode_id"] in seen:
        errs.append("duplicate episode_id")
    seen.add(e["episode_id"])
    if not e["episode_id"].startswith(f"{e['plate_id']}_"):
        errs.append("episode_id does not start with plate_id")
    el = e["elements"]
    if el != sorted(el) or e["chem"] != "-".join(sorted(el)):
        errs.append("elements not sorted or chem != '-'.join(sorted elements)")
    n = len(e["comp"])
    if not (len(e["merit"]) == len(e["nearest_xrd"]) == len(e["xrd_dist"]) == n):
        errs.append("per-candidate list lengths differ")
    if n < 15:
        errs.append(f"P-I4: {n} candidates < 15")
    if e["merit_name"] not in ("EQE_pct", "photocurrent_A"):
        errs.append(f"merit_name {e['merit_name']}")
    il = e["illum"]
    if not isinstance(il, dict) or not (("led_nm" in il) ^ ("led_eV" in il)):
        errs.append("P-I2: illum must hold exactly one of led_nm / led_eV")
    else:
        v = il.get("led_nm", il.get("led_eV"))
        if not isinstance(v, (int, float)) or not math.isfinite(v) or "," in str(v):
            errs.append("P-I2: LED value not a single finite number")
        if "source" not in il:
            errs.append("illum.source missing")
    if not isinstance(e["electrolyte"], str) or not e["electrolyte"].strip():
        errs.append("P-I2: electrolyte empty")
    if not isinstance(e["ph"], (int, float)) or not math.isfinite(e["ph"]):
        errs.append("P-I2: ph not a finite number")
    if "sample_no" in e and len(set(e["sample_no"])) != len(e["sample_no"]):
        errs.append("duplicate sample in episode")
    m = np.asarray(e["merit"], float)
    if not np.isfinite(m).all():
        errs.append("merit not finite")
    C = np.asarray(e["comp"], float)
    if C.ndim != 2 or C.shape[1] != len(el):
        errs.append("comp width != len(elements)")
        return errs
    if np.abs(C.sum(1) - 1).max() > 1e-3:
        errs.append(f"P-I3: comp sums off by {np.abs(C.sum(1)-1).max():.2e}")
    if (C < -1e-9).any():
        errs.append("P-I3: negative fraction")
    d = np.asarray(e["xrd_dist"], float)
    if (d > 0.05 + 1e-9).any():
        errs.append(f"P-I3: xrd_dist max {d.max():.4f} > 0.05")
    z = plate(e["plate_id"])
    if z is None:
        errs.append("plate npz missing")
        return errs
    if list(z["elements"]) != el:
        errs.append(f"npz elements {list(z['elements'])} != {el}")
        return errs
    XC = z["xrd_comp"]
    j = np.asarray(e["nearest_xrd"], int)
    if (j < 0).any() or (j >= len(XC)).any():
        errs.append("nearest_xrd out of range")
        return errs
    D = 0.5 * np.abs(C[:, None, :] - XC[None, :, :]).sum(-1)
    dj = D[np.arange(n), j]
    if np.abs(dj - d).max() > 1e-4:
        errs.append(f"xrd_dist != 0.5*L1(comp, xrd_comp[nearest]) (max diff {np.abs(dj-d).max():.2e})")
    if (dj - D.min(1) > 1e-4).any():
        errs.append("nearest_xrd is not the nearest XRD")
    return errs


def main():
    eps = [json.loads(l) for l in open(EPS)]
    seen, n_fail = set(), 0
    plate_err = {}
    for e in eps:
        pid = e.get("plate_id")
        if pid not in plate_err:
            plate_err[pid] = check_plate(pid)
        errs = plate_err[pid] + check_episode(e, seen)
        n_fail += bool(errs)
        print(f"{'FAIL' if errs else 'PASS'} {e.get('episode_id')} n={len(e.get('comp', []))} chem={e.get('chem')}"
              + (" :: " + "; ".join(errs) if errs else ""))
    # ledger consistency
    L = json.load(open(LEDGER))
    t = L["totals"]
    chems = {}
    for e in eps:
        chems[e["chem"]] = chems.get(e["chem"], 0) + 1
    led_errs = []
    if t["n_episodes"] != len(eps):
        led_errs.append(f"ledger n_episodes {t['n_episodes']} != {len(eps)}")
    if t["n_plates"] != len({e['plate_id'] for e in eps}):
        led_errs.append(f"ledger n_plates {t['n_plates']} != {len({e['plate_id'] for e in eps})}")
    if t["n_chemistries"] != len(chems) or t["chemistries"] != dict(sorted(chems.items())):
        led_errs.append("ledger chemistries differ from episode file")
    admitted = {p["plate_id"] for p in L["plates"] if p["status"] == "ADMITTED"}
    if admitted != {e["plate_id"] for e in eps}:
        led_errs.append("ledger ADMITTED plates != plates with episodes")
    npzs = {f[:-4] for f in os.listdir(PLATES) if f.endswith(".npz")}
    if npzs != admitted:
        led_errs.append(f"npz files {sorted(npzs ^ admitted)} do not match admitted plates")
    for m in led_errs:
        print("FAIL ledger ::", m)
    print(f"SUMMARY: {len(eps) - n_fail}/{len(eps)} episodes PASS, {n_fail} FAIL; ledger checks "
          f"{'PASS' if not led_errs else 'FAIL (' + str(len(led_errs)) + ')'}; plates {len(admitted)}, chemistries {len(chems)}")
    return 1 if (n_fail or led_errs) else 0


if __name__ == "__main__":
    sys.exit(main())
