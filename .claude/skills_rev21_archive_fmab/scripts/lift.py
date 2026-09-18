#!/usr/bin/env python3
"""I2: the channel count as a number with an interval, and its disposition.

    python lift.py --scores floors.csv --col-cminus1 cls_xrd --col-c fm_xrd \\
                   --delta 0.17 --role fixed_input --channel fm_xrd

Reads the per-item value of the composition at C-1 channels and at C, both from
I1 and both computed with no agent in the loop. Prints the paired mean lift, its
95% interval from the I1 per-item variance, and one of three rulings.

    ADVANCE  the interval clears zero or its upper bound reaches delta
    CLOSE    interval covers zero, upper bound below delta, channel scores a fixed input
    LIFT     same interval, but the channel scores an input the agent constructs

A closed channel never reaches an unlifted agent arm. In the materials instance
the lifts read +0.003 and -0.004 over 189 items against a delta of 0.17; this
script would have closed both FM channels before the first scored cell.
"""
import argparse, csv, json, math, sys
Z = {0.10: 1.6449, 0.05: 1.9600, 0.01: 2.5758}

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
    p.add_argument("--scores", required=True)
    p.add_argument("--col-cminus1", required=True, help="composition at C-1 channels")
    p.add_argument("--col-c", required=True, help="composition at C channels")
    p.add_argument("--delta", type=float, required=True, help="manifest delta")
    p.add_argument("--role", required=True, choices=["fixed_input", "agent_input"],
                   help="fixed_input: the channel scores or predicts on a fixed input. "
                        "agent_input: it scores or simulates an input the agent constructs")
    p.add_argument("--channel", default="", help="name of the channel under test, for the record")
    p.add_argument("--alpha", type=float, default=0.05, choices=sorted(Z))
    p.add_argument("--out")
    a = p.parse_args()

    A, B = col(a.scores, a.col_cminus1), col(a.scores, a.col_c)
    if len(A) != len(B): raise SystemExit("columns differ in length. Paired means paired")
    if len(A) < 2: raise SystemExit("need at least two units for an interval")
    d = [c - m for c, m in zip(B, A)]
    n = len(d); mean = sum(d) / n
    sd = math.sqrt(sum((x - mean) ** 2 for x in d) / (n - 1))
    se = sd / math.sqrt(n); z = Z[a.alpha]
    lo, hi = mean - z * se, mean + z * se
    covers_zero = lo <= 0 <= hi
    upper_below_delta = hi < a.delta
    dead = (covers_zero and upper_below_delta) or hi < 0
    ruling = "ADVANCE" if not dead else ("LIFT" if a.role == "agent_input" else "CLOSE")

    rec = {"channel": a.channel, "n": n, "mean_lift": round(mean, 6), "sigma_d": round(sd, 6),
           "ci95": [round(lo, 6), round(hi, 6)], "delta": a.delta, "alpha": a.alpha,
           "covers_zero": covers_zero, "upper_below_delta": upper_below_delta,
           "role": a.role, "ruling": ruling,
           "completeness": (f"paired lift of {a.col_c} over {a.col_cminus1} across {n} units, "
                            f"interval from the I1 per-item variance at alpha {a.alpha}, "
                            f"ruled against delta {a.delta} with role {a.role}")}
    if ruling == "LIFT":
        rec["next"] = ("Gate 1 fourth lift: required consultation with a written verdict. "
                       "I1 rebuilds the floor against the lifted task before any arm runs")
    elif ruling == "CLOSE":
        rec["next"] = ("record the null at instrument cost. No agent arm runs to confirm it. "
                       "The channel enters the axis ledger as channel_lift with status CLOSED")
    txt = json.dumps(rec, indent=2)
    if a.out: open(a.out, "w").write(txt + "\n")
    print(txt)
    if ruling != "ADVANCE":
        print(f"\n{ruling}. The interval [{lo:.4f}, {hi:.4f}] covers zero and sits below delta {a.delta}. "
              "The mechanical count has already stated the null.", file=sys.stderr)
        return 2
    return 0

if __name__ == "__main__": raise SystemExit(main())
