#!/usr/bin/env python3
"""Stress the revision 2 gates on synthetic benchmark instances.

    python simulate_rev2.py --n 1000 --seed 1 --pilot 5 --pilot-rule escalate

Each instance draws a plausible setting (item count, cluster count, floor level,
per-item variance, agent variance multiplier, true mechanical lift, true agent-only
lift, uptake, delta, headroom and noise fractions) and runs the same data through
two pipelines:

    original   I2 reports only, P7 one pass from the free variance, grant ruled as use
    revision2  I2 rules CLOSE / LIFT / ADVANCE, P7 two passes with the R3 pilot,
               R8 uptake row, P2 per-item headroom stratum

Reported per pipeline: where each run stopped, cells spent, claims against truth,
premature stops (a stop before scored cells while the original would have made a
correct claim), and termination (every run must exit inside a transition budget).
"""
import argparse, collections, math, sys
import numpy as np

Z95, Z80 = 1.9600, 0.8416
COST_PER_CELL = 0.14
MAX_TRANSITIONS = 60


def chi2_q(df, z):
    """Wilson-Hilferty approximation of the chi-square quantile at standard-normal z."""
    return df * (1 - 2 / (9 * df) + z * math.sqrt(2 / (9 * df))) ** 3


def t_crit(df):
    # two-sided 95% t critical value, small-df aware
    table = {1: 12.71, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306,
             9: 2.262, 10: 2.228, 12: 2.179, 14: 2.145, 16: 2.120, 20: 2.086, 25: 2.060, 30: 2.042, 40: 2.021}
    ks = sorted(table)
    for k in ks:
        if df <= k: return table[k]
    return 1.96


def draw_setting(rng, stress=False):
    if stress:   # edges of plausibility: tiny supply, tiny clusters, noisy agents, saturated or empty libraries
        role = "agent_input" if rng.random() < 0.5 else "fixed_input"
        m_true = 0.0 if rng.random() < 0.5 else float(rng.uniform(0.0, 0.5))
        a_true = float(rng.uniform(0.0, 0.5)) if role == "agent_input" and rng.random() < 0.5 else 0.0
        return dict(
            n_items=int(rng.integers(12, 80)), n_clusters=int(rng.integers(2, 12)), role=role,
            m_true=m_true, a_true=a_true, sd_free=float(rng.uniform(0.01, 0.45)),
            agent_mult=float(rng.uniform(0.5, 5.0)), uptake=float(rng.uniform(0.0, 1.0)),
            delta=float(rng.uniform(0.03, 0.4)), p_ceiling=float(rng.uniform(0.0, 0.9)),
            p_noise=float(rng.uniform(0.0, 0.6)), floor_mean=float(rng.uniform(0.3, 0.99)),
            budget=int(rng.integers(10, 400)))
    role = "agent_input" if rng.random() < 0.4 else "fixed_input"
    m_true = 0.0 if rng.random() < 0.45 else float(rng.uniform(0.01, 0.30))
    a_true = 0.0
    if role == "agent_input" and rng.random() < 0.5: a_true = float(rng.uniform(0.05, 0.30))
    return dict(
        n_items=int(rng.integers(60, 400)), n_clusters=int(rng.integers(4, 41)), role=role,
        m_true=m_true, a_true=a_true, sd_free=float(rng.uniform(0.05, 0.30)),
        agent_mult=float(rng.uniform(1.0, 3.0)), uptake=float(rng.uniform(0.1, 1.0)),
        delta=float(rng.uniform(0.08, 0.25)), p_ceiling=float(rng.uniform(0.0, 0.5)),
        p_noise=float(rng.uniform(0.0, 0.3)), floor_mean=float(rng.uniform(0.55, 0.90)),
        budget=int(rng.integers(50, 201)))


def make_items(s, rng):
    n = s["n_items"]
    cl = rng.integers(0, s["n_clusters"], size=n)
    pc, pn = s["p_ceiling"], s["p_noise"]
    if pc + pn > 0.95: pc, pn = 0.95 * pc / (pc + pn), 0.95 * pn / (pc + pn)
    kind = rng.choice(["normal", "ceiling", "noise"], size=n, p=[1 - pc - pn, pc, pn])
    f = np.clip(rng.normal(s["floor_mean"], 0.20, size=n), 0.05, 0.99)
    f[kind == "ceiling"] = 1.0
    f[kind == "noise"] = rng.uniform(0.0, 0.3, size=(kind == "noise").sum())
    het = rng.normal(0.0, s["sd_free"], size=n)
    lift = s["m_true"] + het
    lift[kind == "ceiling"] = 0.0
    lift[kind == "noise"] = rng.normal(0.0, s["sd_free"], size=(kind == "noise").sum())
    c = np.clip(f + lift, 0.0, 1.0)
    return dict(cluster=cl, kind=kind, f=f, lift=lift, cminus1=f, c=c)


def agent_arms(s, it, idx, rng, uptake):
    """classical and fm arm values on items idx. Returns (classical, fm, used)."""
    sd = s["sd_free"] * s["agent_mult"]
    f = it["f"][idx]; kind = it["kind"][idx]; lift = it["lift"][idx]
    used = rng.random(len(idx)) < uptake
    e1 = rng.normal(0, sd, len(idx)); e2 = rng.normal(0, sd, len(idx))
    cls = np.clip(f + e1, 0, 1)
    fm = np.clip(f + used * (lift + s["a_true"]) + e2, 0, 1)
    cls[kind == "ceiling"] = 1.0; fm[kind == "ceiling"] = 1.0
    noise = kind == "noise"
    cls[noise] = rng.uniform(0, 0.3, noise.sum()); fm[noise] = rng.uniform(0, 0.3, noise.sum())
    return cls, fm, used


def cluster_stats(d, cl):
    """cluster means of paired differences, sd, MDE (z-based like power.py), t-interval."""
    groups = collections.defaultdict(list)
    for x, c in zip(d, cl): groups[c].append(x)
    means = np.array([np.mean(v) for v in groups.values()])
    n = len(means)
    if n < 2: return dict(n=n, mean=float(means.mean()) if n else 0.0, sd=float("nan"), mde=float("inf"), ci=(-9, 9))
    sd = float(means.std(ddof=1)); se = sd / math.sqrt(n)
    tc = t_crit(n - 1)
    return dict(n=n, mean=float(means.mean()), sd=sd, mde=(Z95 + Z80) * sd / math.sqrt(n),
                ci=(float(means.mean() - tc * se), float(means.mean() + tc * se)))


def oracle(s, it, rng, reps=60):
    """Replicate the cohort run to price the true cluster-level MDE and the achievable power."""
    n = s["n_items"]; cl = it["cluster"]; S = min(s["budget"], n)
    sds, mdes, hits = [], [], 0
    for _ in range(reps):
        idx = rng.permutation(n)[:S]
        cls, fm, _ = agent_arms(s, it, idx, rng, s["uptake"])
        cs = cluster_stats(fm - cls, cl[idx]); sds.append(cs["sd"]); mdes.append(cs["mde"])
    sd = float(np.mean(sds)); k = cluster_stats(np.zeros(S), cl[rng.permutation(n)[:S]])["n"]
    mde_true = (Z95 + Z80) * sd / math.sqrt(max(k, 2))
    for _ in range(reps):
        idx = rng.permutation(n)[:S]
        cls, fm, _ = agent_arms(s, it, idx, rng, s["uptake"])
        cs = cluster_stats(fm - cls, cl[idx]); lo, hi = cs["ci"]
        if lo > 0 and cs["mean"] > mde_true: hits += 1
    return dict(mde_true=mde_true, power=hits / reps, resolvable=mde_true <= s["delta"])


def run_pipeline(s, it, rng, revised, pilot_n, pilot_rule, uptake_band=0.5, lb_z=0.8416):
    """Returns a record of where the run stopped, cells spent, claim, and transition count."""
    rec = dict(stop=None, cells=0, claim="NONE", transitions=0, route="grant", lifted=False, effect=None, mde=None)
    def step(): rec["transitions"] += 1; assert rec["transitions"] <= MAX_TRANSITIONS, "transition budget exceeded"
    n = s["n_items"]; cl = it["cluster"]

    # P2 floor share of ceiling (aggregate close rule, both pipelines)
    step()
    floor_share = float(it["cminus1"].mean())
    if floor_share >= 0.97: rec["stop"] = "P2_close_ceiling"; return rec
    if revised: rec["zero_headroom_share"] = float((it["kind"] == "ceiling").mean())

    # P3/P4 provisional: positive supply band declared before the count
    step()
    k = s["n_clusters"]
    if k < 5: rec["stop"] = "P4_close_supply"; return rec

    # I1 floors exist. I2 channel count
    step()
    d_free = it["c"] - it["cminus1"]
    m = float(d_free.mean()); sd = float(d_free.std(ddof=1)); se = sd / math.sqrt(n)
    lo, hi = m - Z95 * se, m + Z95 * se
    dead = (lo <= 0 <= hi and hi < s["delta"]) or hi < 0
    uptake = s["uptake"]
    if revised and dead:
        if s["role"] == "agent_input":
            rec["lifted"] = True; rec["route"] = "lift"; uptake = 1.0      # required consultation
        else:
            rec["stop"] = "I2_close"; return rec
    # P4 final (revised) is a bookkeeping step; no new closure
    step()

    # P7 pass 1 from the free variance, cluster level
    step()
    cs_free = cluster_stats(d_free, cl)
    mde_free = cs_free["mde"]
    if mde_free > s["delta"]: rec["stop"] = "P7_close_free"; return rec

    # cohort and pilot
    all_idx = np.arange(n)
    rng.shuffle(all_idx)
    S = min(s["budget"], n)
    cohort = all_idx[:S]
    mde_final = mde_free
    if revised:
        # R3 pilot cohort outside the arm cohort. sigma_d comes from the pilot, the MDE is priced
        # at the cohort's own cluster count. Bounded ladder: at most one enlargement, then close.
        k_cohort = len(set(cl[cohort].tolist()))
        spare = all_idx[S:]
        need = pilot_n
        if len(spare) < need:
            take = max(0, min(need, n - 5))       # burn cohort items rather than loop
            cohort = all_idx[take:] if take else cohort
            spare = all_idx[:take]
            k_cohort = len(set(cl[cohort].tolist()))
            if len(spare) < 5: rec["stop"] = "P7_undemonstrated_pilot"; return rec
        # cohort cluster structure: the within-item component shrinks with items per cluster
        sizes = collections.Counter(cl[cohort].tolist()); inv_m = float(np.mean([1.0 / v for v in sizes.values()]))
        var_item_free = float(d_free.var(ddof=1)); var_cl_free = cs_free["sd"] ** 2
        inv_m_free = float(np.mean([1.0 / v for v in collections.Counter(cl.tolist()).values()]))
        var_between_free = max(0.0, var_cl_free - var_item_free * inv_m_free)
        def pilot_pass(pilot):
            cls_p, fm_p, used_p = agent_arms(s, it, pilot, rng, uptake)
            d_p = fm_p - cls_p
            if len(d_p) < 8: return None, None, used_p          # too few items to price the arm variance
            var_item_pilot = float(d_p.var(ddof=1)); df = len(d_p) - 1
            def mde_at(var_item):
                var_cluster_final = var_between_free + var_item * inv_m
                return (Z95 + Z80) * math.sqrt(var_cluster_final) / math.sqrt(k_cohort)
            point = max(mde_free, mde_at(var_item_pilot))
            lower = max(mde_free, mde_at(var_item_pilot * df / chi2_q(df, lb_z)))   # 80% lower bound on the variance
            return point, lower, used_p
        pilot = spare[:need]
        step(); rec["cells"] += 3 * len(pilot)
        mde_final, mde_lower, used_p = pilot_pass(pilot)
        if pilot_rule == "hard":
            if mde_final is None: rec["stop"] = "P7_undemonstrated_pilot"; return rec
            if mde_final > s["delta"]: rec["stop"] = "P7_close_pilot"; return rec
        else:
            # escalate: enlarge when the point estimate prices MDE above delta (or the pilot is too small).
            # bound: same trigger, but closure after enlargement needs the 80% lower bound above delta.
            trigger = mde_final is None or mde_final > s["delta"]
            if trigger:
                if len(spare) >= 2 * need:
                    step(); pilot2 = spare[:2 * need]; rec["cells"] += 3 * (len(pilot2) - len(pilot))
                    mde_final, mde_lower, used_p = pilot_pass(pilot2)
                    if mde_final is None: rec["stop"] = "P7_undemonstrated_pilot"; return rec
                    closing = mde_final if pilot_rule == "escalate" else mde_lower
                    if closing > s["delta"]: rec["stop"] = "P7_close_pilot"; return rec
                else:
                    if mde_final is None: rec["stop"] = "P7_undemonstrated_pilot"; return rec
                    closing = mde_final if pilot_rule == "escalate" else mde_lower
                    if closing > s["delta"]: rec["stop"] = "P7_close_pilot"; return rec
        # R8 uptake row
        step()
        up = float(used_p.mean())
        if not rec["lifted"] and up < uptake_band: rec["route"] = "itt"
    rec["mde"] = mde_final

    # R5 armed. Main run
    step()
    cls, fm, used = agent_arms(s, it, cohort, rng, uptake)
    rec["cells"] += 3 * len(cohort)
    cs = cluster_stats(fm - cls, cl[cohort])
    rec["effect"] = cs["mean"]
    lo_c, hi_c = cs["ci"]
    step()
    if (lo_c > 0 or hi_c < 0) and abs(cs["mean"]) > mde_final:
        rec["claim"] = "POS" if cs["mean"] > 0 else "NEG"
    rec["stop"] = "A4_scored"
    return rec


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=1000); p.add_argument("--seed", type=int, default=1)
    p.add_argument("--pilot", type=int, default=10)
    p.add_argument("--stress", action="store_true", help="draw settings from the edges of plausibility")
    p.add_argument("--pilot-rule", default="bound", choices=["hard", "escalate", "bound"],
                   help="hard: close on the first pilot point estimate. escalate: enlarge the pilot once, then close on the "
                        "point estimate. bound: enlarge once, close only when the 80%% lower bound of the arm variance "
                        "still prices the MDE above delta; claims still use the point estimate")
    a = p.parse_args()
    rng = np.random.default_rng(a.seed)

    rows = []
    for i in range(a.n):
        s = draw_setting(rng, a.stress); it = make_items(s, rng)
        seed_i = int(rng.integers(0, 2**31))
        old = run_pipeline(s, it, np.random.default_rng(seed_i), False, a.pilot, a.pilot_rule)
        new = run_pipeline(s, it, np.random.default_rng(seed_i), True, a.pilot, a.pilot_rule)
        orc = oracle(s, it, np.random.default_rng(seed_i + 7))
        true_effect_grant = s["uptake"] * (s["m_true"] + s["a_true"])
        true_effect_lift = s["m_true"] + s["a_true"]
        rows.append(dict(s=s, old=old, new=new, orc=orc, te_grant=true_effect_grant, te_lift=true_effect_lift))

    def summarise(key):
        c = collections.Counter(r[key]["stop"] for r in rows)
        cells = sum(r[key]["cells"] for r in rows)
        maxt = max(r[key]["transitions"] for r in rows)
        return c, cells, maxt

    print(f"\n{a.n} instances, seed {a.seed}, pilot {a.pilot} ({a.pilot_rule})\n")
    for key, label in (("old", "original"), ("new", "revision 2")):
        c, cells, maxt = summarise(key)
        print(f"== {label}: stops {dict(sorted(c.items()))}")
        print(f"   cells {cells}  (${cells * COST_PER_CELL:,.0f})   max transitions {maxt}  (budget {MAX_TRANSITIONS})")

    # truth-conditioned outcomes
    null = [r for r in rows if r["te_grant"] == 0.0]
    real = [r for r in rows if r["te_grant"] >= r["s"]["delta"]]
    real_res = [r for r in real if r["orc"]["resolvable"]]
    print("\n== against the truth (oracle = the cohort run replicated 60 times)")
    print(f"   true effect exactly zero: {len(null)}   grant-level effect at or above delta: {len(real)}   "
          f"of which the cohort can truly resolve (oracle MDE <= delta): {len(real_res)}")
    for key, label in (("old", "original"), ("new", "revision 2")):
        false_claims = sum(1 for r in null if r[key]["claim"] != "NONE")
        wasted = sum(1 for r in null if r[key]["stop"] == "A4_scored")
        found = sum(1 for r in real_res if r[key]["claim"] == "POS")
        ran = sum(1 for r in real_res if r[key]["stop"] == "A4_scored")
        under = sum(1 for r in rows if r[key]["claim"] == "POS" and abs(r[key]["effect"]) <= r["orc"]["mde_true"])
        print(f"   {label:11s} type I on null {false_claims}/{len(null)}   scored runs on null {wasted}/{len(null)}   "
              f"resolvable real effects found {found}/{len(real_res)} (ran {ran})   "
              f"claims below the true MDE {under}")
    achievable = sum(r["orc"]["power"] for r in real_res)
    print(f"   oracle power summed over resolvable real effects: {achievable:.1f} of {len(real_res)}")

    # premature stops: stopped before scored cells although the effect is real and the cohort could resolve it
    prem = [r for r in real_res if r["new"]["stop"] != "A4_scored"]
    print(f"\n== premature stops in revision 2: {len(prem)} of {len(real_res)} resolvable real effects "
          f"stopped before scored cells; by stage {dict(collections.Counter(r['new']['stop'] for r in prem))}")
    for r in prem[:8]:
        s = r["s"]
        print(f"   - stop {r['new']['stop']:22s} role {s['role']:11s} m_true {s['m_true']:.3f} a_true {s['a_true']:.3f} "
              f"uptake {s['uptake']:.2f} delta {s['delta']:.2f} te {r['te_grant']:.3f} oracle mde {r['orc']['mde_true']:.3f} "
              f"power {r['orc']['power']:.2f} n {s['n_items']} k {s['n_clusters']} mult {s['agent_mult']:.1f}")
    unres = [r for r in rows if not r["orc"]["resolvable"]]
    unres_stopped = sum(1 for r in unres if r["new"]["stop"] != "A4_scored")
    unres_ran_old = sum(1 for r in unres if r["old"]["stop"] == "A4_scored")
    print(f"== instances the cohort cannot truly resolve: {len(unres)}; revision 2 stopped {unres_stopped} of them "
          f"before cells, the original ran {unres_ran_old}")

    # lifts
    lifted = [r for r in rows if r["new"]["lifted"]]
    lift_found = sum(1 for r in lifted if r["new"]["claim"] == "POS" and r["te_lift"] > 0)
    lift_null = sum(1 for r in lifted if r["te_lift"] == 0)
    print(f"\n== LIFT route taken {len(lifted)} times; positive claim under lift {lift_found}; "
          f"lifted instances whose true lifted effect is zero {lift_null}")
    itt = sum(1 for r in rows if r["new"]["route"] == "itt")
    print(f"== intention-to-treat route taken {itt} times (uptake below band in the pilot)")

    # second-pass P7 diagnostics
    pc = [r for r in rows if r["new"]["stop"] == "P7_close_pilot"]
    pc_res = sum(1 for r in pc if r["orc"]["resolvable"])
    print(f"== P7 closed on the pilot pass {len(pc)} times; {pc_res} of those were truly resolvable (false closures)")
    i2 = [r for r in rows if r["new"]["stop"] == "I2_close"]
    i2_real = [r for r in i2 if r["te_grant"] >= r["s"]["delta"] and r["orc"]["resolvable"]]
    i2_pow = [r for r in i2_real if r["orc"]["power"] >= 0.5]
    print(f"== I2 closed {len(i2)} times; {len(i2_real)} of those carried a resolvable effect at or above delta, "
          f"{len(i2_pow)} with oracle power >= 0.5")
    for r in i2_real[:6]:
        s = r["s"]
        print(f"   - m_true {s['m_true']:.3f} delta {s['delta']:.3f} uptake {s['uptake']:.2f} floor_mean {s['floor_mean']:.2f} "
              f"p_ceiling {s['p_ceiling']:.2f} p_noise {s['p_noise']:.2f} n {s['n_items']} k {s['n_clusters']} "
              f"oracle mde {r['orc']['mde_true']:.3f} power {r['orc']['power']:.2f}")
    # the strict premature metric: stopped before cells while the full run would have found it more often than not
    strict = [r for r in rows if r["new"]["stop"] != "A4_scored" and r["orc"]["power"] >= 0.5 and r["te_grant"] > 0]
    print(f"== strict premature stops (oracle power >= 0.5, effect > 0): {len(strict)} of "
          f"{sum(1 for r in rows if r['orc']['power'] >= 0.5 and r['te_grant'] > 0)} findable effects; "
          f"by stage {dict(collections.Counter(r['new']['stop'] for r in strict))}")
    return 0


if __name__ == "__main__": raise SystemExit(main())
