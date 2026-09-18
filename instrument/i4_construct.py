"""I4 construct validity: do the FM channels measure something tied to the scored quantity (EQE-best composition)?

Checks (validation uses S1's annotated top-EQE phases from Fig3 csv; they are never scored):
  (a) MACE: is each observed photoactive ternary phase within 50 meV/atom of the MACE hull?
  (b) MEGNet: is its predicted HSE gap <= the photon energy under which it was top-EQE (absorption is necessary)?
  (c) location: |argmax FM prior - true best Sb fraction| vs the same for a uniform guess, over all episodes.
"""
import json, os, sys, collections
import numpy as np, pandas as pd
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "bench"))
import data, floors
from pymatgen.core import Composition

f3 = pd.read_csv(os.path.join(data.RAW, "Fig3_topEQE_Phasevs_LED_pH_annealT.csv"))
res = dict(a=[], b=[])
for (el, formula, led), g in f3.groupby(["el", "formula", "LED_eV"]):
    fstr = formula.lstrip("*")
    if fstr.startswith("am-"):
        res["a"].append(dict(el=el, phase=formula, result="amorphous: no crystal to test")); continue
    try:
        red = Composition(fstr).reduced_composition
    except Exception:
        res["a"].append(dict(el=el, phase=formula, result="unparseable")); continue
    rows = [r for r in floors.fm_rows(el).values() if Composition(r["formula"]).reduced_composition.almost_equals(red, rtol=0.02)]
    if not rows:
        res["a"].append(dict(el=el, phase=formula, led=led, result="not in MP system (no structure to evaluate)")); continue
    best = min(rows, key=lambda r: r["ehull_eV_atom"])
    res["a"].append(dict(el=el, phase=formula, led=led, mp=best["id"], ehull=best["ehull_eV_atom"], on_hull_50meV=best["ehull_eV_atom"] <= 0.05))
    ev = float(str(led).split()[0])
    g_hse = best.get("megnet_gap_hse_eV")
    res["b"].append(dict(el=el, phase=formula, led_eV=ev, mp=best["id"], gap_hse=g_hse, absorbs=(g_hse is not None and g_hse <= ev)))

loc = []
for ep in data.episodes():
    pr = floors.fm_prior(ep)
    sb = np.array(ep["sb"]); tb = sb[int(np.argmax(ep["eqe"]))]
    loc.append(dict(el=ep["el"], err_fm=abs(sb[int(np.argmax(pr))] - tb), err_uniform=float(np.mean(np.abs(sb - tb)))))
L = pd.DataFrame(loc)
a = [x for x in res["a"] if "on_hull_50meV" in x]; b = res["b"]
summary = dict(
    mace_on_hull=f"{sum(x['on_hull_50meV'] for x in a)} of {len(a)} observed top-EQE crystalline phases (with an MP structure) within 50 meV/atom of the MACE hull",
    mace_untestable=len(res["a"]) - len(a),
    megnet_absorbs=f"{sum(x['absorbs'] for x in b)} of {len(b)} have MEGNet HSE gap <= the photon energy at which they were top-EQE",
    location=dict(mean_abs_err_fm_prior=round(L.err_fm.mean(), 4), mean_abs_err_uniform=round(L.err_uniform.mean(), 4)),
    ruling=None)
ok_mace = sum(x["on_hull_50meV"] for x in a) >= 0.5 * max(len(a), 1)
ok_loc = L.err_fm.mean() < L.err_uniform.mean()
summary["ruling"] = dict(mace_stability="PASS" if ok_mace else "FAIL", megnet_bandgap="PASS" if sum(x["absorbs"] for x in b) >= 0.5 * max(len(b), 1) else "FAIL",
                         fm_prior_location="PASS" if ok_loc else "FAIL",
                         note="construct validity on a proxy: stability/gap are necessary conditions for photoactivity, not EQE itself")
json.dump(dict(details=res, summary=summary, completeness=f"{len(res['a'])} annotated (element, phase, LED) rows tested for MACE, {len(b)} for MEGNet, {len(L)} episodes for location."),
          open(os.path.join(ROOT, "instrument/i4_construct.json"), "w"), indent=1, default=str)
print(json.dumps(summary, indent=1, default=str))
