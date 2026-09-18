#!/usr/bin/env python3
"""Choose the similarity cut by measurement, never by convention.

Two signals bound it. Cluster count saturates above some cut, so tighter buys
nothing. Separation between two mechanical compositions collapses below some
cut, because units too similar to each other land where retrieval saturates and
no arm can separate.

Input CSV: cut, n_clusters, and optionally separation.

    python tau.py --curve curve.csv
"""
import argparse, csv, json

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--curve", required=True)
    p.add_argument("--saturation", type=float, default=0.05,
                   help="fractional cluster gain below which tighter buys nothing")
    p.add_argument("--out")
    a = p.parse_args()

    rows = sorted((dict(r) for r in csv.DictReader(open(a.curve, newline=""))),
                  key=lambda r: float(r["cut"]))
    if len(rows) < 3: raise SystemExit("need at least three cuts to see a curve")
    cuts = [float(r["cut"]) for r in rows]
    nc = [float(r["n_clusters"]) for r in rows]
    sep = [float(r["separation"]) for r in rows] if "separation" in rows[0] else None

    gains = [(nc[i] - nc[i - 1]) / nc[i - 1] if nc[i - 1] else 0.0 for i in range(1, len(nc))]
    sat = next((cuts[i] for i, g in enumerate(gains, start=1) if g < a.saturation), None)

    collapse = None
    if sep:
        top = max(sep)
        collapse = next((cuts[i] for i in range(len(sep) - 1, -1, -1)
                         if sep[i] < 0.5 * top), None)

    print(f"{'cut':>8}{'clusters':>10}{'gain':>9}" + (f"{'separation':>12}" if sep else ""))
    for i, c in enumerate(cuts):
        g = f"{gains[i-1]:+.3f}" if i else "     -"
        s = f"{sep[i]:>12.4f}" if sep else ""
        print(f"{c:>8.3f}{nc[i]:>10.0f}{g:>9}{s}")

    print()
    print(f"saturation cut   {sat if sat is not None else 'not reached in this range'}")
    if sep:
        print(f"collapse cut     {collapse if collapse is not None else 'not reached in this range'}")

    chosen, why = None, None
    if sat is not None and collapse is not None and collapse < sat:
        chosen = sat
        why = (f"cluster gain falls below {a.saturation:.0%} at {sat}, and separation holds "
               f"above {collapse}, so {sat} is the loosest cut that buys units without "
               "entering the band where no arm can separate")
    elif sat is not None:
        chosen = sat
        why = f"cluster gain falls below {a.saturation:.0%} at {sat}; separation not supplied"
    if chosen is None:
        print("\nREFUSE. The curve does not bound a cut in this range. Widen the sweep.")
        return 2

    i = cuts.index(chosen)
    looser = cuts[i - 1] if i > 0 else None
    tighter = cuts[i + 1] if i + 1 < len(cuts) else None
    rec = {"chosen_cut": chosen, "justification": why,
           "sensitivity": {"looser": looser, "tighter": tighter},
           "saturation_cut": sat, "collapse_cut": collapse,
           "curve": [{"cut": c, "n_clusters": nc[j],
                      **({"separation": sep[j]} if sep else {})} for j, c in enumerate(cuts)],
           "chosen_to_increase_unit_count": False,
           "completeness": (f"swept {len(cuts)} cuts from {cuts[0]} to {cuts[-1]}, "
                            + ("separation measured at each" if sep else "separation not measured"))}
    print(f"\nCHOSEN {chosen}")
    print(f"  {why}")
    print(f"  report sensitivity at {looser} and {tighter}")
    if a.out: open(a.out, "w").write(json.dumps(rec, indent=2) + "\n")
    return 0

if __name__ == "__main__": raise SystemExit(main())
