"""Replay environment data: 22 X-Sb-O combinatorial plates (CaltechDATA 42gwd-8wg77, CC0).

One episode = (plate, electrolyte run `anals`, LED). The full EQE map along the plate's composition
line is recorded, and so is an XRD pattern at every XRD point. That makes the outcome of the action
not taken observable: this is the replayable environment that shape.md requires for the intervene root.
"""
from __future__ import annotations
import functools, hashlib, json, os
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(ROOT, "env", "raw", "antimonate", "source_data_v2")
LED_EV = {"CA1": 3.2, "CA2": 2.7, "CA3": 2.4, "CA4": 2.1}   # from the LED_eV column of the source file


def parse_udi(path):
    meta, arrays = {}, {}
    for line in open(path):
        line = line.strip()
        if not line or line.startswith("//") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if "," in v or k in ("Q",) or k.startswith("I"):
            try:
                arrays[k] = np.array([float(x) for x in v.split(",")])
                continue
            except ValueError:
                arrays[k] = v.split(",")
                continue
        meta[k] = v
    return meta, arrays


@functools.lru_cache(maxsize=None)
def plates():
    info = pd.read_csv(os.path.join(RAW, "XSbO_plates_xrd_udi.csv"))
    out = {}
    for _, r in info.iterrows():
        meta, arr = parse_udi(os.path.join(RAW, "XRD_udi_22plates", r["xrd udi file name"]))
        el = r["el"]
        n = int(meta["N"])
        sb = arr["Sb"][:n]
        pats = np.stack([arr[f"I{i+1}"] for i in range(n)])
        order = np.argsort(sb)
        out[int(r["plate_id"])] = dict(
            plate_id=int(r["plate_id"]), el=el, substrate=r["substrate"], annealT_C=int(r["annealT_C"]),
            Q=arr["Q"], xrd_sb=sb[order], xrd=pats[order],
            xrd_sample=[int(float(s)) for s in np.array(arr["sample_no"])[order]])
    return out


@functools.lru_cache(maxsize=None)
def eqe_table():
    e = pd.read_csv(os.path.join(RAW, "Fig1c_ allEQE_withcriteria.csv"))
    return e


@functools.lru_cache(maxsize=None)
def episodes():
    """Every (plate, anals, LED) with its full EQE map. Frozen, deterministic order."""
    e = eqe_table()
    P = plates()
    eps = []
    for (pid, anals, rtech), g in e.groupby(["plate_id", "anals", "rtech"], sort=True):
        g = g.drop_duplicates("Sample").sort_values("Sb.L.AtFrac")
        p = P[int(pid)]
        sb = g["Sb.L.AtFrac"].to_numpy()
        eqe = g["EQE_pct"].to_numpy()
        # nearest XRD point per EQE sample, by Sb fraction
        nearest = np.abs(sb[:, None] - p["xrd_sb"][None, :]).argmin(1)
        eid = f"{pid}_{anals}_{rtech}"
        eps.append(dict(
            episode_id=eid, plate_id=int(pid), el=p["el"], anals=str(anals), rtech=rtech,
            led_eV=LED_EV[rtech], ph=float(g["ph"].iloc[0]), electrolyte=g["electrolyte"].iloc[0],
            substrate=p["substrate"], annealT_C=p["annealT_C"],
            sample=g["Sample"].astype(int).tolist(), sb=sb.round(4).tolist(), eqe=eqe.tolist(),
            nearest_xrd=nearest.tolist()))
    return eps


def episode(eid):
    return next(x for x in episodes() if x["episode_id"] == eid)


def data_hash():
    h = hashlib.sha256()
    for f in sorted(os.listdir(os.path.join(RAW, "XRD_udi_22plates"))) + ["Fig1c_ allEQE_withcriteria.csv"]:
        p = os.path.join(RAW, "XRD_udi_22plates", f) if f.endswith(".udi") else os.path.join(RAW, f)
        h.update(open(p, "rb").read())
    return h.hexdigest()


if __name__ == "__main__":
    eps = episodes()
    print(len(eps), "episodes over", len({e["plate_id"] for e in eps}), "plates,",
          len({e["el"] for e in eps}), "elements")
    df = pd.DataFrame([dict(eid=e["episode_id"], el=e["el"], led=e["rtech"], n=len(e["eqe"]),
                            mx=max(e["eqe"]), top_frac=np.mean(np.array(e["eqe"]) >= 0.9 * max(e["eqe"])))
                       for e in eps])
    print(df.groupby("led").agg(n_ep=("eid", "count"), med_n=("n", "median"), med_max=("mx", "median"),
                                med_topfrac=("top_frac", "median")))
    print("data sha256", data_hash())
