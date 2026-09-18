#!/usr/bin/env python3
"""Price the resolution before any agent runs, in two passes.

Pass 1, provisional, from the free paired difference between the two I1
compositions. Rows are items; --cluster names the independent unit.

    python power.py --scores floors.csv --col-a fm_prior --col-b cls_gp --cluster el \\
                    --k 5 --candidates-per-item 29 --delta 0.17 \\
                    --scope provisional --out power_record_provisional.json

Pass 2, final, from the paired arm differences in the R3 pilot cohort (at least
10 items outside the arm cohort, every arm). The pilot prices the item-level arm
variance, which the free pass cannot see. That variance is projected onto the
arm cohort's own cluster structure:

    var_cluster = var_between(free) + var_item(pilot) * mean over cohort clusters of 1/m_c
    MDE_point   = z * sqrt(var_cluster) / sqrt(k_cohort)

    python power.py --scores pilot.csv --col-a fm --col-b classical --cluster el \\
                    --k 5 --candidates-per-item 29 --delta 0.17 \\
                    --scope final --provisional power_record_provisional.json \\
                    --cohort-clusters cohort.csv --cohort-cluster-col el

Final rulings
    RESOLVABLE             point MDE at or below delta. R5 may arm.
    ESCALATE_ENLARGE_PILOT point MDE above delta on a pilot below 20 items. Enlarge to 20, re-run once.
    RUN_AT_LIMIT           pilot at 20 or more, point MDE above delta, 80% lower bound of the arm
                           variance prices it at or below delta. The run proceeds and reports at
                           its resolution limit. Claims still need |effect| > point MDE.
    CLOSE_UNRESOLVABLE     the lower bound itself sits above delta. Close before any scored cell.
    UNDEMONSTRATED         pilot below 10 items. Scope stays provisional.

What the second pass prices: the agent's own within-item noise. What it does not
price: between-cluster heterogeneity of the agent effect, which a pilot with about
one item per cluster cannot separate from noise. A4 reports the observed MDE for
exactly that reason. In the materials instance the free MDE read 0.089, the arm
MDE read 0.225 against a delta of 0.17, and the gap was learned after 300 cells.
"""
import argparse, collections, csv, json, math, sys
Z  = {0.10: 1.6449, 0.05: 1.9600, 0.01: 2.5758}
ZP = {0.80: 0.8416, 0.90: 1.2816, 0.95: 1.6449}
LB_Z = 0.8416   # one-sided 80% lower bound on the pilot variance


def chi2_q(df, z):
    """Wilson-Hilferty approximation of the chi-square quantile at standard-normal z."""
    return df * (1 - 2 / (9 * df) + z * math.sqrt(2 / (9 * df))) ** 3


def rows_of(path):
    rows = list(csv.DictReader(open(path, newline="")))
    if not rows: raise SystemExit(f"{path} is empty")
    return rows


def col(rows, name, path):
    if name not in rows[0]: raise SystemExit(f"column {name!r} not in {list(rows[0])} ({path})")
    out = []
    for i, r in enumerate(rows):
        v = r[name].strip()
        if v == "": raise SystemExit(f"row {i} empty in {name!r}. Missing is not zero")
        out.append(float(v))
    return out


def sd(xs):
    m = sum(xs) / len(xs)
    return math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) if len(xs) > 1 else float("nan")


def cluster_means(d, labels):
    g = collections.defaultdict(list)
    for x, l in zip(d, labels): g[l].append(x)
    return [sum(v) / len(v) for v in g.values()], [len(v) for v in g.values()]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scores", required=True); p.add_argument("--col-a", required=True)
    p.add_argument("--col-b", required=True);  p.add_argument("--k", type=int, required=True)
    p.add_argument("--candidates-per-item", type=float, required=True)
    p.add_argument("--delta", type=float, required=True)
    p.add_argument("--alpha", type=float, default=0.05, choices=sorted(Z))
    p.add_argument("--power", type=float, default=0.80, choices=sorted(ZP))
    p.add_argument("--cluster", help="column naming the independent unit; rows are items. Omit if rows are already units")
    p.add_argument("--stratum", help="optional column of stratum labels; reported per stratum")
    p.add_argument("--scope", default="provisional", choices=["provisional", "final"])
    p.add_argument("--provisional", help="the provisional record, required for --scope final")
    p.add_argument("--cohort-clusters", help="CSV with one row per arm-cohort item, required for --scope final")
    p.add_argument("--cohort-cluster-col", help="cluster column in --cohort-clusters; defaults to --cluster")
    p.add_argument("--out")
    a = p.parse_args()
    z = Z[a.alpha] + ZP[a.power]

    rows = rows_of(a.scores)
    A, B = col(rows, a.col_a, a.scores), col(rows, a.col_b, a.scores)
    if len(A) != len(B): raise SystemExit("columns differ in length. Paired means paired")
    if len(A) < 2: raise SystemExit("need at least two units for a standard deviation")
    d = [x - y for x, y in zip(A, B)]
    labels = [r[a.cluster] for r in rows] if a.cluster else list(range(len(d)))
    means, sizes = cluster_means(d, labels)
    inv_m = sum(1.0 / m for m in sizes) / len(sizes)

    rec = {"k": a.k, "candidates_per_item": a.candidates_per_item,
           "chance": round(a.k / a.candidates_per_item, 6), "delta": a.delta,
           "alpha": a.alpha, "power": a.power, "scope": a.scope,
           "n_items": len(d), "n": len(means), "unit": a.cluster or "row",
           "mean_paired_difference": round(sum(means) / len(means), 6),
           "sigma_item": round(sd(d), 6), "inv_m": round(inv_m, 6)}

    if a.scope == "provisional":
        s_cl = sd(means)
        rec.update({"sigma_d": round(s_cl, 6), "sigma_d_source": "free_compositions",
                    "mde": round(z * s_cl / math.sqrt(len(means)), 6),
                    "n_min": math.ceil((z ** 2) * s_cl ** 2 / a.delta ** 2),
                    "var_between_free": round(max(0.0, s_cl ** 2 - sd(d) ** 2 * inv_m), 8),
                    "licenses": "I2 to R4 only. R5 arms nothing on this record"})
        rec["ruling"] = "RESOLVABLE" if rec["mde"] <= a.delta else "CLOSE_UNRESOLVABLE"
    else:
        if not (a.provisional and a.cohort_clusters):
            raise SystemExit("--scope final needs --provisional <record> and --cohort-clusters <csv>")
        prov = json.load(open(a.provisional))
        ccol = a.cohort_cluster_col or a.cluster
        if not ccol: raise SystemExit("--scope final needs a cluster column for the cohort")
        crow = rows_of(a.cohort_clusters)
        if ccol not in crow[0]: raise SystemExit(f"column {ccol!r} not in {a.cohort_clusters}")
        csizes = collections.Counter(r[ccol] for r in crow)
        k_cohort = len(csizes); inv_m_cohort = sum(1.0 / v for v in csizes.values()) / k_cohort
        var_item = sd(d) ** 2; df = len(d) - 1
        vb = prov.get("var_between_free", 0.0)
        def mde_at(v): return z * math.sqrt(vb + v * inv_m_cohort) / math.sqrt(k_cohort)
        mde_point = max(prov["mde"], mde_at(var_item))
        mde_lower = max(prov["mde"], mde_at(var_item * df / chi2_q(df, LB_Z)))
        rec.update({"sigma_d_source": "pilot_arms", "n_pilot": len(d), "sigma_d_pilot": round(sd(d), 6),
                    "k_cohort": k_cohort, "inv_m_cohort": round(inv_m_cohort, 6),
                    "var_between_free": vb, "mde_provisional": prov["mde"], "sigma_d_provisional": prov.get("sigma_d"),
                    "sigma_d": round(math.sqrt(vb + var_item * inv_m_cohort), 6),
                    "mde_pilot": round(mde_at(var_item), 6), "mde": round(mde_point, 6),
                    "mde_lower": round(mde_lower, 6),
                    "n_min": max(prov.get("n_min", 0), math.ceil((z ** 2) * (vb + var_item * inv_m_cohort) / a.delta ** 2))})
        if len(d) < 10:
            rec["ruling"] = "UNDEMONSTRATED"; rec["scope"] = "provisional"
            rec["licenses"] = "nothing new. Pilot below 10 items, run at least 10 outside the arm cohort"
        elif mde_point <= a.delta:
            rec["ruling"] = "RESOLVABLE"; rec["licenses"] = "R5 and every scored cell"
        elif len(d) < 20:
            rec["ruling"] = "ESCALATE_ENLARGE_PILOT"; rec["scope"] = "provisional"
            rec["licenses"] = "nothing new. Enlarge the pilot to 20 items and re-run this pass once"
        elif mde_lower <= a.delta:
            rec["ruling"] = "RUN_AT_LIMIT"
            rec["licenses"] = ("R5 and every scored cell, reported at the resolution limit: point MDE above delta, "
                               "80% lower bound at or below it")
        else:
            rec["ruling"] = "CLOSE_UNRESOLVABLE"; rec["licenses"] = "nothing. Close before any scored cell"
        rec["not_priced"] = ("between-cluster heterogeneity of the agent effect; a pilot with about one item per "
                             "cluster cannot separate it from noise. A4 reports the observed MDE")

    if a.stratum:
        slabels = [r[a.stratum] for r in rows]
        strata = {}
        for lab in sorted(set(slabels)):
            idx = [i for i, l in enumerate(slabels) if l == lab]
            if len(idx) > 1:
                dd = [d[i] for i in idx]; mm, _ = cluster_means(dd, [labels[i] for i in idx])
                s_cl = sd(mm) if len(mm) > 1 else float("nan")
                strata[lab] = {"n_items": len(dd), "n": len(mm), "mean_paired_difference": round(sum(dd) / len(dd), 6),
                               "sigma_d": round(s_cl, 6) if s_cl == s_cl else None,
                               "mde": round(z * s_cl / math.sqrt(len(mm)), 6) if s_cl == s_cl else None}
        rec["strata"] = strata
        rec["note"] = "Strata are reported, never filtered. Removing items where the compositions do not separate selects on the outcome variable."

    rec["completeness"] = (f"chance, sigma_d, MDE and N_min over {rec['n']} clustered units from {rec['n_items']} items "
                           f"at alpha {a.alpha}, power {a.power}, scope {rec['scope']}, variance from {rec['sigma_d_source']}"
                           + (f", across {len(rec.get('strata', {}))} strata" if a.stratum else ""))
    txt = json.dumps(rec, indent=2)
    if a.out: open(a.out, "w").write(txt + "\n")
    print(txt)
    if rec["ruling"] == "CLOSE_UNRESOLVABLE":
        print(f"\nCLOSE. MDE {rec['mde']} exceeds delta {a.delta}"
              + (f" and so does its lower bound {rec['mde_lower']}" if "mde_lower" in rec else "")
              + ". The cohort cannot resolve the declared effect. Close here, not after the run.", file=sys.stderr)
        return 2
    if rec["ruling"] in ("ESCALATE_ENLARGE_PILOT", "UNDEMONSTRATED"):
        print(f"\n{rec['ruling']}. {rec['licenses']}", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__": raise SystemExit(main())
