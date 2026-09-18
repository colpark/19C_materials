"""A2-A3: hash blind files, then score once, paired.

Blind file per arm = adjudication/blind/<tag>_<arm>.jsonl with {episode, measured_indices, submitted, n_calls}
(no labels). Labels (full EQE maps) are opened only after all blind hashes are recorded.

    python adjudication/score.py blind --tag main --arms bare classical fm
    python adjudication/score.py score --tag main --arms bare classical fm
"""
import argparse, collections, hashlib, json, math, sys
from pathlib import Path
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bench"))
FM_TOOLS = {"mace_stability", "megnet_bandgap"}
CLS_TOOLS = {"list_phases", "substitute_structure", "simulate_xrd", "match_xrd", "gp_suggest"}


def cell_dir(tag, e, arm): return ROOT / "runtime/cells" / tag / f"{e}__{arm}"


def blind(tag, arms):
    cohort = json.loads((ROOT / "discovery/corpus_ledger.json").read_text())["corpus"]["arm_cohort"]
    out = {}
    (ROOT / "adjudication/blind").mkdir(parents=True, exist_ok=True)
    for arm in arms:
        p = ROOT / f"adjudication/blind/{tag}_{arm}.jsonl"
        with open(p, "w") as f:
            for e in cohort:
                d = cell_dir(tag, e, arm)
                envf, meta = d / "env.json", d / "meta.json"
                rec = dict(episode=e, arm=arm, ran=d.exists())
                if envf.exists():
                    s = json.loads(envf.read_text())
                    rec.update(measured=sorted(int(k) for k in s["eqe"]), xrd=s["xrd"], submitted=s["submitted"], n_calls=s["n_calls"])
                calls = []
                if (d / "calls.jsonl").exists():
                    calls = [json.loads(l)["tool"] for l in (d / "calls.jsonl").read_text().splitlines()]
                rec["tool_counts"] = dict(collections.Counter(calls))
                if meta.exists():
                    m = json.loads(meta.read_text()); rec.update(timed_out=m["timed_out"], result_subtype=m["result_subtype"], cost_usd=m["cost_usd"])
                f.write(json.dumps(rec, sort_keys=True) + "\n")
        out[arm] = hashlib.sha256(p.read_bytes()).hexdigest()
    hp = ROOT / f"adjudication/blind/{tag}_hashes.json"
    hp.write_text(json.dumps(dict(hashes=out, labels_opened=False), indent=1))
    print(json.dumps(out, indent=1))


def load_blind(tag, arm, check):
    p = ROOT / f"adjudication/blind/{tag}_{arm}.jsonl"
    if hashlib.sha256(p.read_bytes()).hexdigest() != check[arm]:
        raise SystemExit(f"blind file {p} changed after hashing")
    return {r["episode"]: r for r in map(json.loads, p.read_text().splitlines())}


def score(tag, arms):
    H = json.loads((ROOT / f"adjudication/blind/{tag}_hashes.json").read_text())["hashes"]
    B = {arm: load_blind(tag, arm, H) for arm in arms}
    import data, floors, csv   # labels open here
    fl = {r["episode_id"]: r for r in csv.DictReader(open(ROOT / "instrument/floors.csv"))}
    rows = []
    for e in B[arms[0]]:
        ep = data.episode(e)
        r = dict(episode=e, el=ep["el"], led=ep["rtech"], chance=floors.chance(ep),
                 low_signal=max(ep["eqe"]) < 0.01)
        for k in floors.COMPOSITIONS: r["floor_" + k] = float(fl[e][k])
        for arm in arms:
            b = B[arm][e]
            covered = b.get("ran") and b.get("measured") is not None and len(b.get("measured", [])) > 0
            r[arm] = floors.score(ep, b["measured"]) if covered else None
            tc = b.get("tool_counts", {})
            r[arm + "_n_eqe"] = len(b.get("measured") or []); r[arm + "_n_xrd"] = len(b.get("xrd") or [])
            r[arm + "_fm_calls"] = sum(v for k, v in tc.items() if k in FM_TOOLS)
            r[arm + "_cls_calls"] = sum(v for k, v in tc.items() if k in CLS_TOOLS)
            r[arm + "_eval_categories"] = len({k for k in tc if k in FM_TOOLS | CLS_TOOLS} | ({"xrd"} if r[arm + "_n_xrd"] else set()))
            sub = b.get("submitted") or {}
            r[arm + "_rejections"] = len(sub.get("rejected") or [])
            r[arm + "_submitted"] = bool(sub)
            r[arm + "_cost"] = b.get("cost_usd")
        rows.append(r)
    json.dump(rows, open(ROOT / f"adjudication/scores_{tag}.json", "w"), indent=1)
    return rows


def paired(rows, a, b, cluster="el"):
    pr = [(r[a], r[b], r[cluster]) for r in rows if r.get(a) is not None and r.get(b) is not None]
    d = np.array([x - y for x, y, _ in pr])
    n = len(d)
    out = dict(a=a, b=b, n_paired=n, coverage_lost=len(rows) - n, mean_a=float(np.mean([x for x, _, _ in pr])),
               mean_b=float(np.mean([y for _, y, _ in pr])), mean_diff=float(d.mean()), sd_diff=float(d.std(ddof=1)))
    out["se_naive"] = out["sd_diff"] / math.sqrt(n)
    cl = collections.defaultdict(list)
    for (x, y, c) in pr: cl[c].append(x - y)
    cm = np.array([np.mean(v) for v in cl.values()])
    out.update(n_clusters=len(cm), cluster_mean_diff=float(cm.mean()), se_cluster=float(cm.std(ddof=1) / math.sqrt(len(cm))))
    # t critical for cluster-level test
    from scipy import stats
    tcrit = stats.t.ppf(0.975, len(cm) - 1)
    out["ci95_cluster"] = [out["cluster_mean_diff"] - tcrit * out["se_cluster"], out["cluster_mean_diff"] + tcrit * out["se_cluster"]]
    out["p_cluster"] = float(2 * stats.t.sf(abs(out["cluster_mean_diff"] / out["se_cluster"]), len(cm) - 1)) if out["se_cluster"] > 0 else None
    out["wins_ties_losses"] = [int((d > 1e-9).sum()), int((abs(d) <= 1e-9).sum()), int((d < -1e-9).sum())]
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd"); ap.add_argument("--tag", required=True); ap.add_argument("--arms", nargs="+", required=True)
    a = ap.parse_args()
    if a.cmd == "blind": blind(a.tag, a.arms)
    else:
        rows = score(a.tag, a.arms)
        comps = [("fm", "classical"), ("fm", "bare"), ("classical", "bare"), ("fm", "floor_fm_xrd"), ("fm", "floor_cls_gp"),
                 ("classical", "floor_cls_gp"), ("fm", "chance"), ("classical", "chance"), ("bare", "chance")]
        res = [paired(rows, x, y) for x, y in comps if all(x in r or x.startswith("floor") for r in rows[:1])]
        json.dump(res, open(ROOT / f"adjudication/paired_{a.tag}.json", "w"), indent=1)
        for r in res: print(f"{r['a']:>10} vs {r['b']:<16} n={r['n_paired']:3d} diff={r['mean_diff']:+.3f} cl={r['cluster_mean_diff']:+.3f} CI{np.round(r['ci95_cluster'],3)} p={r['p_cluster']} W/T/L={r['wins_ties_losses']}")
