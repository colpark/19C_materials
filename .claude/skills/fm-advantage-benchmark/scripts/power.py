#!/usr/bin/env python3
"""Price the resolution before any agent runs. The variance estimate is free:
it is the per-item paired difference between two mechanical compositions, which
exist before any arm runs. In the source record both numbers were computable on
day one and neither was computed for fourteen stages.

    python power.py --scores floors.csv --col-a classical --col-b instrument \\
                    --k 10 --candidates-per-item 100 --delta 0.05
"""
import argparse, csv, json, math, sys
Z  = {0.10: 1.6449, 0.05: 1.9600, 0.01: 2.5758}
ZP = {0.80: 0.8416, 0.90: 1.2816, 0.95: 1.6449}

def col(path, name):
    rows = list(csv.DictReader(open(path, newline="")))
    if not rows: raise SystemExit(f"{path} is empty")
    if name not in rows[0]: raise SystemExit(f"column {name!r} not in {list(rows[0])}")
    out = []
    for i, r in enumerate(rows):
        v = r[name].strip()
        if v == "": raise SystemExit(f"row {i} empty in {name!r}. Missing is not zero")
        out.append(float(v))
    return out

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scores", required=True); p.add_argument("--col-a", required=True)
    p.add_argument("--col-b", required=True);  p.add_argument("--k", type=int, required=True)
    p.add_argument("--candidates-per-item", type=float, required=True)
    p.add_argument("--delta", type=float, required=True)
    p.add_argument("--alpha", type=float, default=0.05, choices=sorted(Z))
    p.add_argument("--power", type=float, default=0.80, choices=sorted(ZP))
    p.add_argument("--stratum", help="optional column of stratum labels; reported per stratum")
    p.add_argument("--out")
    a = p.parse_args()

    A, B = col(a.scores, a.col_a), col(a.scores, a.col_b)
    if len(A) != len(B): raise SystemExit("columns differ in length. Paired means paired")
    if len(A) < 2: raise SystemExit("need at least two units for a standard deviation")
    z = Z[a.alpha] + ZP[a.power]

    def stats(xa, xb):
        d = [x - y for x, y in zip(xa, xb)]
        m = sum(d) / len(d)
        sd = math.sqrt(sum((x - m) ** 2 for x in d) / (len(d) - 1)) if len(d) > 1 else float("nan")
        return {"n": len(d), "mean_paired_difference": round(m, 6), "sigma_d": round(sd, 6),
                "mde": round(z * sd / math.sqrt(len(d)), 6),
                "n_min": math.ceil((z ** 2) * sd ** 2 / a.delta ** 2)}

    rec = {"k": a.k, "candidates_per_item": a.candidates_per_item,
           "chance": round(a.k / a.candidates_per_item, 6), "delta": a.delta,
           "alpha": a.alpha, "power": a.power}
    rec.update(stats(A, B))

    if a.stratum:
        labels = [r[a.stratum] for r in csv.DictReader(open(a.scores, newline=""))]
        strata = {}
        for lab in sorted(set(labels)):
            idx = [i for i, l in enumerate(labels) if l == lab]
            if len(idx) > 1:
                strata[lab] = stats([A[i] for i in idx], [B[i] for i in idx])
        rec["strata"] = strata
        rec["note"] = ("Strata are reported, never filtered. Removing items where the "
                       "compositions do not separate selects on the outcome variable.")

    rec["ruling"] = "RESOLVABLE" if rec["mde"] <= a.delta else "CLOSE_UNRESOLVABLE"
    rec["completeness"] = (f"chance, sigma_d, MDE and N_min over {rec['n']} clustered units "
                           f"at alpha {a.alpha}, power {a.power}"
                           + (f", across {len(rec.get('strata', {}))} strata" if a.stratum else ""))
    txt = json.dumps(rec, indent=2)
    if a.out: open(a.out, "w").write(txt + "\n")
    print(txt)
    if rec["ruling"] == "CLOSE_UNRESOLVABLE":
        print(f"\nCLOSE. MDE {rec['mde']} exceeds delta {a.delta}. The cohort cannot "
              "resolve the declared effect. Close here, not after the run.", file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__": raise SystemExit(main())
