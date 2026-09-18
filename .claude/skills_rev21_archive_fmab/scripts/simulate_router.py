#!/usr/bin/env python3
"""Route synthetic closures through router.py and check that they route well.

    python simulate_router.py --n 1000 --seed 1

Each world draws a closure, a context (what exists in the world: sibling libraries,
alternative checkpoints, heterogeneity, unburned supply, an exposure key, a portfolio),
a resource envelope with some of it already spent, and a human who answers decision
cards slowly and says no half the time. Three policies run on identical worlds:

    router        revision 2.1: autonomous moves launched, reserved moves carded, guards on
    stop_and_ask  every closure waits for the human
    naive_retry   retries the first applicable move without guards or retirement

Reported: resolution rate, rounds to terminal state, cards per world, envelope breaches,
preregistration violations, guard trips, and termination inside the round cap.
"""
import argparse, collections, copy, json, os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import router as R

KEYS = ["SUPPLY_CLUSTERS", "SUPPLY_ITEMS", "I2_CLOSE", "I4_FAIL", "P2_CEILING", "P3_CONTAMINATION", "R_STALL", "A4_NO_CLAIM_AT_LIMIT"]
KEY_P = [0.28, 0.14, 0.20, 0.06, 0.10, 0.05, 0.10, 0.07]
CLOSURE_OF = {"SUPPLY_CLUSTERS": "P7_CLOSE_UNRESOLVABLE", "SUPPLY_ITEMS": "P7_CLOSE_UNRESOLVABLE", "I2_CLOSE": "I2_CLOSE",
              "I4_FAIL": "I4_FAIL", "P2_CEILING": "P2_CLOSE", "P3_CONTAMINATION": "P3_CONTAMINATION", "R_STALL": "R_STALL",
              "A4_NO_CLAIM_AT_LIMIT": "A4_NO_CLAIM_AT_LIMIT"}
ROUND_CAP = 40


def draw_world(rng, human_p=0.6, spent_lo=0.1, spent_hi=1.3):
    key = rng.choice(KEYS, p=KEY_P)
    n_sib = int(rng.integers(0, 4)); n_alt = int(rng.integers(0, 3))
    items_bound = key == "SUPPLY_ITEMS"
    ctx = dict(n_clusters=int(rng.integers(4, 30)), n_min_clusters=int(rng.integers(10, 60)),
               var_between_share=float(rng.uniform(0.35, 0.9)) if key in ("SUPPLY_CLUSTERS", "A4_NO_CLAIM_AT_LIMIT") else float(rng.uniform(0.0, 0.25)),
               heterogeneity_detected=bool(rng.random() < 0.6), explain_grader_available=bool(rng.random() < 0.7),
               items_bound=items_bound or bool(rng.random() < 0.2), unburned_supply=bool(rng.random() < 0.6),
               alt_fms=n_alt, agent_input_possible=bool(rng.random() < 0.5), exposure_key_exists=bool(rng.random() < 0.7),
               outcomes_seen=bool(rng.random() < 0.5), sibling_libraries_found=False)
    env = {}
    for r, lo, hi in (("gpu_hours", 50, 300), ("storage_gb", 100, 1000), ("tokens_m", 50, 500), ("wall_hours", 24, 120)):
        ceiling = float(rng.uniform(lo, hi)); env[r] = {"ceiling": ceiling, "spent": ceiling * float(rng.uniform(spent_lo, spent_hi)), "committed": 0.0}
    env["tolerance"] = 3.0
    n_other = int(rng.integers(0, 4))
    portfolio = {"candidates": [{"id": "C1", "status": "active", "resolving_power": 1.0, "cost_class": 2}] +
                 [{"id": f"C{i+2}", "status": "active", "resolving_power": float(rng.uniform(0.2, 1.5)), "cost_class": int(rng.integers(1, 4))} for i in range(n_other)]}
    world = dict(key=key, n_sib_true=n_sib, ctx=ctx, env=env, portfolio=portfolio,
                 human_answer_p=human_p, human_yes_p=0.5)
    return world


def success_p(remedy, world, ctx):
    """How likely a move is to unbind the closure, given what the world actually contains."""
    w = world
    return {
        "search_sibling_libraries": 1 - 0.3 ** w["n_sib_true"] if w["n_sib_true"] else 0.0,
        "pool_libraries_new_tau": 0.6, "spin_explain_candidate": 0.85, "buy_episodes_per_cluster": 0.7 if ctx.get("items_bound") else 0.15,
        "swap_fm_checkpoint": 1 - 0.65 ** max(ctx.get("alt_fms", 0), 1) if ctx.get("alt_fms") else 0.0,
        "change_role_scorer_lift": 0.5, "forced_consultation_lift": 0.6, "filter_by_exposure_key": 0.8,
        "advance_next_candidate": 0.5, "request_new_libraries": 0.4, "change_task_budget": 0.7,
        "different_scored_quantity": 0.5, "accept_proxy_grader": 0.5, "later_data": 0.2, "escalate_rung_7": 0.8,
    }[remedy]


def run_router(world, rng, policy):
    """Drive one world to a terminal state. Returns a record of what happened."""
    ctx = dict(world["ctx"]); man = {"envelope": copy.deepcopy(world["env"]), "decision_rights": {"delegated": [k for k, v in R.REMEDIES.items() if v["cls"] == "autonomous"]}}
    pf = copy.deepcopy(world["portfolio"]); cand = "C1"
    rec = dict(policy=policy, key=world["key"], rounds=0, cards=0, launched=0, refused=0, human_decisions=0,
               resolved=False, terminal=None, prereg_violation=0, hard_breach=0, soft_overruns=0, depth_trips=0, retired=0)
    pending = []      # (round_done, remedy, kind)  kind: auto | human
    open_cards = []   # reserved moves waiting for the human
    closure = CLOSURE_OF[world["key"]]

    def decide():
        nonlocal closure
        if policy == "router":
            d = R.route(closure, cand, ctx, man, pf)
            rec["launched"] += len(d["launched"]); rec["refused"] += len(d["refused"])
            for l in d["launched"]:
                if R.REMEDIES[l["remedy"]]["prereg"] and ctx.get("outcomes_seen"): rec["prereg_violation"] += 1
                for res in R.RESOURCES:
                    if l["projected"][res] > man["envelope"][res]["ceiling"] * man["envelope"]["tolerance"]: rec["hard_breach"] += 1
                if l["over_soft_ceiling"]: rec["soft_overruns"] += 1
                pending.append((rec["rounds"] + max(1, int(round(l["cost"]["wall_hours"] / 3))), l["remedy"], "auto"))
            if d["carded"]: rec["cards"] += 1; open_cards.extend(c["remedy"] for c in d["carded"] if c["remedy"] not in open_cards)
            if any(r["reason"].startswith("remedy depth") for r in d["refused"]): rec["depth_trips"] += 1
            rec["retired"] = len(pf["guard_state"][cand]["retired"])
            return bool(d["launched"] or d["carded"])
        if policy == "stop_and_ask":
            key = R.closure_key(closure, ctx); rec["cards"] += 1
            for rid in R.TABLE[key]:
                if rid not in open_cards: open_cards.append(rid)
            return True
        if policy == "naive_retry":
            key = R.closure_key(closure, ctx)
            for rid in R.TABLE[key]:
                r = R.REMEDIES[rid]
                if r["cls"] != "autonomous": continue
                missing = [n for n in r["needs"] if not ctx.get(n) and n != "before_a1"]
                if missing: continue
                rec["launched"] += 1
                if r["prereg"] and ctx.get("outcomes_seen"): rec["prereg_violation"] += 1
                for res in R.RESOURCES:
                    man["envelope"][res]["committed"] += r["cost"][res]
                    if man["envelope"][res]["spent"] + man["envelope"][res]["committed"] > man["envelope"][res]["ceiling"] * 3.0: rec["hard_breach"] += 1
                pending.append((rec["rounds"] + max(1, int(round(r["cost"]["wall_hours"] / 3))), rid, "auto"))
                return True
            rec["cards"] += 1; open_cards.extend(x for x in R.TABLE[key] if x not in open_cards)
            return True

    acted = decide()
    while rec["rounds"] < ROUND_CAP and not rec["resolved"]:
        rec["rounds"] += 1
        # the human answers open cards slowly and says no half the time
        if open_cards and rng.random() < world["human_answer_p"]:
            rid = open_cards.pop(0); rec["human_decisions"] += 1
            if rng.random() < world["human_yes_p"]:
                pending.append((rec["rounds"] + 2, rid, "human"))
        # moves complete
        done = [p for p in pending if p[0] <= rec["rounds"]]; pending[:] = [p for p in pending if p[0] > rec["rounds"]]
        new_closure = False
        for _, rid, kind in done:
            if rid == "search_sibling_libraries":
                found = rng.random() < success_p(rid, world, ctx); ctx["sibling_libraries_found"] = found
                if not found and policy == "router": R.report_outcome(pf, cand, rid, False)
                new_closure = True; continue          # pooling is the move that resolves
            unmet = [n for n in R.REMEDIES[rid]["needs"] if n not in ("before_a1", "portfolio_has_next") and not ctx.get(n)]
            ok = (not unmet) and rng.random() < success_p(rid, world, ctx)
            if ok: rec["resolved"] = True; rec["terminal"] = f"resolved_by_{rid}"; break
            if policy == "router": R.report_outcome(pf, cand, rid, False)
            if rid == "advance_next_candidate":
                for c in pf["candidates"]:
                    if c["status"] == "active" and c["id"] != cand: c["status"] = "closed"; break
            new_closure = True
        if rec["resolved"]: break
        if not pending and not open_cards:
            if new_closure or not acted:
                acted = decide()
                if not pending and not open_cards:
                    rec["terminal"] = "closed_no_moves_left"; break
        elif new_closure and policy == "router" and not pending:
            acted = decide()
    if rec["rounds"] >= ROUND_CAP and not rec["resolved"]:
        rec["terminal"] = "LOOP_CAP" if pending else ("waiting_on_human" if open_cards else "closed_no_moves_left")
    if rec["terminal"] is None: rec["terminal"] = "closed_no_moves_left"
    return rec


def main():
    p = argparse.ArgumentParser(); p.add_argument("--n", type=int, default=1000); p.add_argument("--seed", type=int, default=1)
    p.add_argument("--human-p", type=float, default=0.6, help="probability per round that the human answers an open card")
    p.add_argument("--spent", default="0.1,1.3", help="range of the envelope already spent, as a fraction of the ceiling")
    a = p.parse_args(); rng = np.random.default_rng(a.seed)
    lo, hi = (float(x) for x in a.spent.split(","))
    worlds = [draw_world(rng, a.human_p, lo, hi) for _ in range(a.n)]
    print(f"human answers with p={a.human_p} per round; envelope spent {lo}-{hi} of ceiling; tolerance 3.0")
    out = {pol: [run_router(w, np.random.default_rng(1000 + i), pol) for i, w in enumerate(worlds)] for pol in ("router", "stop_and_ask", "naive_retry")}
    print(f"\n{a.n} worlds, seed {a.seed}\n")
    print(f"{'policy':13s}{'resolved':>10s}{'rounds':>8s}{'cards':>7s}{'human':>7s}{'launched':>10s}{'prereg':>8s}{'hard':>6s}{'soft':>6s}{'depth':>7s}{'retired':>9s}{'loop-cap':>9s}{'waiting':>9s}")
    for pol, recs in out.items():
        n = len(recs)
        print(f"{pol:13s}{sum(r['resolved'] for r in recs)/n:10.2f}{np.mean([r['rounds'] for r in recs]):8.1f}"
              f"{np.mean([r['cards'] for r in recs]):7.2f}{np.mean([r['human_decisions'] for r in recs]):7.2f}"
              f"{np.mean([r['launched'] for r in recs]):10.2f}{sum(r['prereg_violation'] for r in recs):8d}"
              f"{sum(r['hard_breach'] for r in recs):6d}{sum(r['soft_overruns'] for r in recs):6d}"
              f"{sum(r['depth_trips'] for r in recs):7d}{sum(1 for r in recs if r['retired']):9d}"
              f"{sum(1 for r in recs if r['terminal']=='LOOP_CAP'):9d}{sum(1 for r in recs if r['terminal']=='waiting_on_human'):9d}")
    print("\nrouter, by closure key: resolved rate, mean cards, mean launched, terminal states")
    recs = out["router"]
    for key in KEYS:
        rr = [r for r in recs if r["key"] == key]
        if not rr: continue
        term = collections.Counter(r["terminal"].split("_by_")[0] if not r["terminal"].startswith("resolved") else "resolved" for r in rr)
        print(f"  {key:22s} n={len(rr):4d}  resolved {np.mean([r['resolved'] for r in rr]):.2f}  cards {np.mean([r['cards'] for r in rr]):.2f}  "
              f"launched {np.mean([r['launched'] for r in rr]):.2f}  {dict(term)}")
    print("\nrouter, what resolved closures (top):", collections.Counter(r["terminal"] for r in recs if r["resolved"]).most_common(8))
    print("router, closures with outcomes already seen that launched a preregistration-changing move:",
          sum(r["prereg_violation"] for r in recs))
    return 0


if __name__ == "__main__": raise SystemExit(main())
