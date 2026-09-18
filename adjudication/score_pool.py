"""A2-A3 for the rev 2.3 pass. blind: write and hash per-arm blind files from cells (no labels). score: verify hashes, then open labels.

    python adjudication/score_pool.py blind --tag rev23_main
    python adjudication/score_pool.py score --tag rev23_main
"""
import argparse, collections, hashlib, json, math, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
ARMS = ("bare", "classical", "fm_forced")
FM = {"mace_stability", "megnet_bandgap"}; CLS = {"list_phases", "substitute_structure", "simulate_xrd", "match_xrd", "gp_suggest"}
OUT = ROOT / "rev23/adjudication"


def cohort():
    return json.loads((ROOT / "rev21/pool/split.json").read_text())["cohort"]


def blind(tag):
    OUT.mkdir(parents=True, exist_ok=True); H = {}
    for arm in ARMS:
        p = OUT / f"blind_{tag}_{arm}.jsonl"
        with open(p, "w") as f:
            for e in cohort():
                d = ROOT / "runtime/cells" / tag / f"{e}__{arm}"; rec = dict(episode=e, arm=arm, ran=d.exists())
                if (d / "env.json").exists():
                    s = json.loads((d / "env.json").read_text())
                    rec.update(measured=sorted(int(k) for k in s["eqe"]), xrd=s["xrd"], submitted=s["submitted"], n_calls=s["n_calls"],
                               n_consultations=len(s.get("consultations", [])))
                calls = [json.loads(l)["tool"] for l in (d / "calls.jsonl").read_text().splitlines()] if (d / "calls.jsonl").exists() else []
                rec["tool_counts"] = dict(collections.Counter(calls))
                if (d / "meta.json").exists():
                    m = json.loads((d / "meta.json").read_text()); rec.update(timed_out=m["timed_out"], result_subtype=m["result_subtype"], cost_usd=m["cost_usd"])
                f.write(json.dumps(rec, sort_keys=True) + "\n")
        H[arm] = hashlib.sha256(p.read_bytes()).hexdigest()
    (OUT / f"blind_{tag}_hashes.json").write_text(json.dumps(dict(hashes=H, labels_opened=False), indent=1))
    print(json.dumps(H, indent=1))


def paired(rows, a, b, cl="cluster"):
    pr = [(r[a], r[b], r[cl]) for r in rows if r.get(a) is not None and r.get(b) is not None]
    if len(pr) < 3: return dict(a=a, b=b, n_paired=len(pr), note="too few pairs")
    d = np.array([x - y for x, y, _ in pr]); g = collections.defaultdict(list)
    for x, y, c in pr: g[c].append(x - y)
    cm = np.array([np.mean(v) for v in g.values()]); from scipy import stats
    se = cm.std(ddof=1) / math.sqrt(len(cm)) if len(cm) > 1 else float("nan"); t = stats.t.ppf(0.975, len(cm) - 1) if len(cm) > 1 else float("nan")
    return dict(a=a, b=b, n_paired=len(pr), coverage_lost=len(rows) - len(pr), mean_a=float(np.mean([x for x, _, _ in pr])), mean_b=float(np.mean([y for _, y, _ in pr])),
                episode_mean_diff=float(d.mean()), n_clusters=len(cm), cluster_mean_diff=float(cm.mean()), se_cluster=float(se),
                ci95_cluster=[float(cm.mean() - t * se), float(cm.mean() + t * se)],
                p_cluster=float(2 * stats.t.sf(abs(cm.mean() / se), len(cm) - 1)) if se and se > 0 else None,
                sigma_cluster=float(cm.std(ddof=1)) if len(cm) > 1 else None,
                wins_ties_losses=[int((d > 1e-9).sum()), int((abs(d) <= 1e-9).sum()), int((d < -1e-9).sum())])


def score(tag):
    H = json.loads((OUT / f"blind_{tag}_hashes.json").read_text())["hashes"]; B = {}
    for arm in ARMS:
        p = OUT / f"blind_{tag}_{arm}.jsonl"
        if hashlib.sha256(p.read_bytes()).hexdigest() != H[arm]: raise SystemExit(f"blind file {p} changed after hashing")
        B[arm] = {r["episode"]: r for r in map(json.loads, p.read_text().splitlines())}
    sys.path.insert(0, str(ROOT / "bench")); import pool_floors as P, pandas as pd     # labels open here
    E = {e["episode_id"]: e for e in P.all_episodes()}
    items = pd.read_csv(ROOT / "rev23/supply/pooled_items.csv").set_index("episode_id")
    rows = []
    for e in cohort():
        ep = E[e]; it = items.loc[e]
        r = dict(episode=e, cluster=it["cluster"], chem=it["chem"], source=it["source"], geometry=it["geometry"], low_signal=it["low_signal_flag"],
                 led=round(ep["led_eV"], 2) if ep.get("led_eV") else None, chance=float(it["chance"]), cls_gp=float(it["cls_gp"]), cls_xrd=float(it["cls_xrd"]),
                 fm_xrd=float(it["fm_xrd"]))
        for arm in ARMS:
            b = B[arm][e]; ok = b.get("ran") and b.get("measured")
            r[arm] = P.score(ep, b["measured"]) if ok else None
            tc = b.get("tool_counts", {})
            r[arm + "_fm_calls"] = sum(v for k, v in tc.items() if k in FM); r[arm + "_cls_calls"] = sum(v for k, v in tc.items() if k in CLS)
            r[arm + "_n_xrd"] = len(b.get("xrd") or []); r[arm + "_consultations"] = b.get("n_consultations", 0)
            r[arm + "_rejections"] = len((b.get("submitted") or {}).get("rejected") or []); r[arm + "_cost"] = b.get("cost_usd")
        rows.append(r)
    json.dump(rows, open(OUT / f"scores_{tag}.json", "w"), indent=1, default=float)
    comps = [("fm_forced", "classical")] + [(a, f) for a in ARMS for f in ("cls_xrd", "cls_gp", "chance")] + [("fm_forced", "bare"), ("classical", "bare")]
    res = {"all": [paired(rows, a, b) for a, b in comps]}
    for s in ("geometry", "low_signal", "source", "led"):
        for v in sorted({str(r[s]) for r in rows}):
            sub = [r for r in rows if str(r[s]) == v]
            res[f"{s}={v}"] = [paired(sub, "fm_forced", "classical")]
    json.dump(res, open(OUT / f"paired_{tag}.json", "w"), indent=1, default=float)
    for k, v in res.items():
        for p in v:
            if "cluster_mean_diff" in p:
                print(f"{k:>22} {p['a']:>9}-{p['b']:<10} n={p['n_paired']:3d} ep={p['episode_mean_diff']:+.3f} cl={p['cluster_mean_diff']:+.3f} CI[{p['ci95_cluster'][0]:+.3f},{p['ci95_cluster'][1]:+.3f}] k={p['n_clusters']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("--tag", required=True); a = ap.parse_args()
    blind(a.tag) if a.cmd == "blind" else score(a.tag)
