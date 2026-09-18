#!/usr/bin/env python3
"""Derive the queue size from observed yield. Never assume it.

The source record's end-to-end yield was 1 of 6, whose exact 95% interval runs
from 0.004 to 0.641. That licenses a queue anywhere from 2 to unbounded, so a
queue planned from six candidates is planned against noise. Re-derive after
every batch. Counting is free.

Four escapes, printed explicitly:
  ESCAPE target        survivor count reached S
  ESCAPE supply        optimistic yield on remaining supply cannot reach S
  PROJECTION           how many more to count before it settles, and whether that
                       spends the pool. The caller weighs it against the budget.
  PROVISIONAL          spread too wide to commit paid-tier effort, with a sized next batch

The queue is never capped at a declared number of batches. A cap stops on a
counter rather than on a threat, and a null reached under a small cap licenses
nothing: zero of twenty excludes almost no yield at all. The stop is derived
from the pool instead. Batch size is sized here and chosen by the caller.

Usage
-----
    python queue.py --counted 40 --passed 13 --survivors 7 --target 10 --remaining 200
"""
import argparse, math

def beta_inv(p, a, b, steps=3000):
    def ibeta(m):
        s = sum(((i + .5) * m / steps) ** (a - 1) * (1 - (i + .5) * m / steps) ** (b - 1)
                for i in range(steps)) * m / steps
        t = sum(((i + .5) / steps) ** (a - 1) * (1 - (i + .5) / steps) ** (b - 1)
                for i in range(steps)) / steps
        return s / t
    lo, hi = 0.0, 1.0
    for _ in range(60):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if ibeta(m) < p else (lo, m)
    return (lo + hi) / 2

def clopper(k, n, alpha=0.05):
    return (0.0 if k == 0 else beta_inv(alpha / 2, k, n - k + 1),
            1.0 if k == n else beta_inv(1 - alpha / 2, k + 1, n - k))

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--counted", type=int, required=True)
    p.add_argument("--passed", type=int, required=True)
    p.add_argument("--survivors", type=int, required=True)
    p.add_argument("--target", type=int, required=True)
    p.add_argument("--remaining", type=int, default=None)
    p.add_argument("--spread-limit", type=float, default=10.0)
    a = p.parse_args()

    if not (a.survivors <= a.passed <= a.counted):
        raise SystemExit("counts must nest: survivors <= passed <= counted")

    lo, hi = clopper(a.survivors, a.counted)
    point = a.survivors / a.counted
    print(f"observed      {a.survivors}/{a.counted} = {point:.3f}")
    print(f"95% interval  [{lo:.3f}, {hi:.3f}]")

    need = a.target - a.survivors
    if need <= 0:
        print(f"\nESCAPE target. S={a.target} reached. Stop enumerating.")
        return 0
    # how much more counting would settle this, and does settling cost the pool?
    if a.remaining is not None:
        total = a.counted + a.remaining
        how, at = "exhaustion", total
        for m in range(a.counted + 1, total + 1):
            k_m = point * m
            if k_m >= a.target:
                how, at = "reaching S", m; break
            hi_m = clopper(int(round(k_m)), m)[1]
            if hi_m * (total - m) < (a.target - k_m):
                how, at = "supply closure", m; break
        more = max(0, at - a.counted)
        print(f"\nprojected to settle by {how} at about {at} counted, {more} more")
        if more > 0.8 * a.remaining:
            print("WARNING settling consumes most of the pool. Weigh it against the budget.")
            print("Recording UNDEMONSTRATED with the bound is the cheaper honest outcome.")

    if point == 0:
        print(f"\nPROVISIONAL. Zero survivors so far, no point estimate exists.")
        print(f"Upper 95% bound on yield is {hi:.3f}. A null here is a bound, never a zero.")
        print(f"Next batch: {max(20, math.ceil(need / hi) - a.counted)}. Then re-derive.")
        return 1

    q_opt, q_pt = math.ceil(need / hi), math.ceil(need / point)
    q_pess = math.ceil(need / lo) if lo > 0 else None
    print(f"\nqueue for {need} more survivor(s)")
    print(f"  optimistic    {q_opt}")
    print(f"  point         {q_pt}")
    print(f"  pessimistic   {q_pess if q_pess else 'unbounded, zero yield not excluded'}")

    if a.remaining is not None:
        best = a.remaining * hi
        print(f"\nsupply remaining {a.remaining}, optimistic yield {best:.1f}")
        if best < need:
            print(f"ESCAPE supply. Even optimistically the pool cannot reach S={a.target}.")
            print("Close the domain and write the finding.")
            return 3

    spread = (q_pess / q_pt) if q_pess else float("inf")
    if spread > a.spread_limit:
        s = f"{spread:.0f}x" if q_pess else "unbounded"
        print(f"\nPROVISIONAL. Pessimistic queue is {s} the point estimate.")
        w_target = 0.15
        n_want = math.ceil((1.96 ** 2) * point * (1 - point) / (w_target ** 2))
        nxt = max(20, n_want - a.counted)
        if a.remaining is not None:
            nxt = min(nxt, a.remaining)
        print(f"Next batch: {nxt}, sized to bring the interval near {w_target:.2f} wide.")
        print(f"Point-estimate queue for reference: {q_pt}. Re-derive after the batch.")
        print("Do not commit paid-tier effort on this number.")
        return 1
    print(f"\nLICENSED. Spread {spread:.1f}x. Plan against the point estimate.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
