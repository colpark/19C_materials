#!/usr/bin/env python3
"""O1: route on closure. The orchestrator's decision policy, as code.

    python router.py route --closure P7_CLOSE_UNRESOLVABLE --candidate C1 \\
        --context context.json --manifest manifest.json --portfolio portfolio.json --out decision_001.json
    python router.py card decision_001.json
    python router.py next --portfolio portfolio.json

A closure names what bound (the key). The remedy table lists the moves that could
unbind it, in order. Each move is autonomous or reserved. The router launches the
autonomous moves whose preconditions hold and whose projected cost stays inside the
resource envelope's hard limit, refuses the rest with the reason, and writes one
decision record. Reserved moves go to the human on a decision card. Nothing blocks
on the card: the portfolio's next candidate keeps running.

Three guards bound the loops the router introduces: remedy depth per candidate,
re-entries per (candidate, stage), and a retired list for a move that failed twice.
No autonomous move ever changes a preregistered element after outcomes were seen.
"""
import argparse, collections, json, sys

RESOURCES = ("gpu_hours", "storage_gb", "tokens_m", "wall_hours")
GUARDS = {"max_depth": 3, "max_reentry": 2, "max_failures": 2}

# ---------------------------------------------------------------- remedy table
# class: autonomous | reserved. reentry: the stage the move re-enters.
# needs: context keys that must be truthy. cost: projected spend per resource.
# prereg: True when the move changes a preregistered element; such a move is
# autonomous only before A1, and reserved to the human after outcomes are seen.
REMEDIES = {
  "search_sibling_libraries": dict(cls="autonomous", reentry="D2",
      cost=dict(gpu_hours=0, storage_gb=5, tokens_m=5, wall_hours=3), needs=[], prereg=False,
      what="search the corpus sources and public deposits for sibling libraries of the same task family, read whole, log to the exclusion ledger"),
  "pool_libraries_new_tau": dict(cls="autonomous", reentry="D3",
      cost=dict(gpu_hours=2, storage_gb=10, tokens_m=2, wall_hours=2), needs=["sibling_libraries_found"], prereg=False,
      what="pool the found libraries and re-measure tau; the unit may change, so the axis ledger is recounted"),
  "spin_explain_candidate": dict(cls="autonomous", reentry="D4",
      cost=dict(gpu_hours=0, storage_gb=1, tokens_m=3, wall_hours=2), needs=["heterogeneity_detected", "explain_grader_available"], prereg=False,
      what="open the explain candidate on the per-cluster channel effect, graded by the mechanical ablation floors at zero cells"),
  "buy_episodes_per_cluster": dict(cls="autonomous", reentry="P7",
      cost=dict(gpu_hours=1, storage_gb=1, tokens_m=4, wall_hours=6), needs=["items_bound", "unburned_supply"], prereg=False,
      what="enlarge the cohort from unburned supply so the within-cluster component shrinks; re-run the final P7 pass"),
  "swap_fm_checkpoint": dict(cls="autonomous", reentry="I2",
      cost=dict(gpu_hours=6, storage_gb=20, tokens_m=1, wall_hours=4), needs=["alt_fms"], prereg=False,
      what="precompute the alternative checkpoint on the same structures, rebuild the composition, re-run lift.py"),
  "change_role_scorer_lift": dict(cls="autonomous", reentry="I1",
      cost=dict(gpu_hours=1, storage_gb=1, tokens_m=2, wall_hours=3), needs=["agent_input_possible", "before_a1"], prereg=True,
      what="move the channel from predictor to scorer on agent-built inputs, rebuild the floor for the lifted task"),
  "forced_consultation_lift": dict(cls="autonomous", reentry="I1",
      cost=dict(gpu_hours=1, storage_gb=1, tokens_m=3, wall_hours=3), needs=["before_a1"], prereg=True,
      what="require consultation with a written verdict, rebuild the floor as the mechanical consultation"),
  "filter_by_exposure_key": dict(cls="autonomous", reentry="D2",
      cost=dict(gpu_hours=0, storage_gb=1, tokens_m=1, wall_hours=1), needs=["exposure_key_exists"], prereg=False,
      what="keep only items whose deposition postdates every subject's cutoff; recount the axis ledger"),
  "advance_next_candidate": dict(cls="autonomous", reentry="portfolio",
      cost=dict(gpu_hours=0, storage_gb=0, tokens_m=0, wall_hours=0), needs=["portfolio_has_next"], prereg=False,
      what="start the next active candidate in the portfolio by priority"),
  "request_new_libraries": dict(cls="reserved", reentry="D2",
      cost=dict(gpu_hours=0, storage_gb=0, tokens_m=0, wall_hours=0), needs=[], prereg=False,
      what="ask collaborators for libraries or new experiments; a scientific and programme decision"),
  "change_task_budget": dict(cls="reserved", reentry="D4",
      cost=dict(gpu_hours=1, storage_gb=1, tokens_m=1, wall_hours=2), needs=[], prereg=True,
      what="set the per-item measurement budget from what a campaign affords; cost of action belongs to the PI"),
  "different_scored_quantity": dict(cls="reserved", reentry="D4",
      cost=dict(gpu_hours=0, storage_gb=0, tokens_m=0, wall_hours=0), needs=[], prereg=True,
      what="move to a task whose scored quantity the FM's construct measures; a change of scientific question"),
  "accept_proxy_grader": dict(cls="reserved", reentry="I4",
      cost=dict(gpu_hours=0, storage_gb=0, tokens_m=0, wall_hours=0), needs=[], prereg=True,
      what="accept a disclosed proxy grader; a judgment about what counts as evidence"),
  "later_data": dict(cls="reserved", reentry="D2",
      cost=dict(gpu_hours=0, storage_gb=0, tokens_m=0, wall_hours=0), needs=[], prereg=False,
      what="wait for data deposited after the subject cutoff"),
  "escalate_rung_7": dict(cls="reserved", reentry="R1",
      cost=dict(gpu_hours=0, storage_gb=0, tokens_m=0, wall_hours=0), needs=[], prereg=False,
      what="the ladder's last rung: a harness fault no rule covers"),
}

# closure key -> ordered remedies. Supply closures split by what the variance says.
TABLE = {
  "I2_CLOSE":                 ["swap_fm_checkpoint", "change_role_scorer_lift", "advance_next_candidate", "different_scored_quantity"],
  "I4_FAIL":                  ["swap_fm_checkpoint", "advance_next_candidate", "different_scored_quantity", "accept_proxy_grader"],
  "SUPPLY_CLUSTERS":          ["search_sibling_libraries", "pool_libraries_new_tau", "spin_explain_candidate", "advance_next_candidate", "request_new_libraries", "change_task_budget"],
  "SUPPLY_ITEMS":             ["buy_episodes_per_cluster", "forced_consultation_lift", "advance_next_candidate", "change_task_budget"],
  "P2_CEILING":               ["advance_next_candidate", "change_task_budget"],
  "P3_CONTAMINATION":         ["filter_by_exposure_key", "advance_next_candidate", "later_data"],
  "R_STALL":                  ["advance_next_candidate", "escalate_rung_7"],
  "A4_NO_CLAIM_AT_LIMIT":     ["buy_episodes_per_cluster", "search_sibling_libraries", "spin_explain_candidate", "advance_next_candidate", "request_new_libraries", "change_task_budget"],
}


def closure_key(closure, ctx):
    """Map a stage ruling onto a table key, splitting supply closures by the variance decomposition."""
    c = closure.upper()
    if c in ("P7_CLOSE_UNRESOLVABLE", "P4_CLOSE", "P4_CLOSE_SUPPLY"):
        return "SUPPLY_CLUSTERS" if ctx.get("var_between_share", 1.0) >= 0.3 or ctx.get("n_min_clusters", 0) > ctx.get("n_clusters", 0) else "SUPPLY_ITEMS"
    if c.startswith("I2"): return "I2_CLOSE"
    if c.startswith("I4"): return "I4_FAIL"
    if c.startswith("P2"): return "P2_CEILING"
    if c.startswith("P3"): return "P3_CONTAMINATION"
    if c.startswith("R"): return "R_STALL"
    if c.startswith("A4"): return "A4_NO_CLAIM_AT_LIMIT"
    raise SystemExit(f"no table entry for closure {closure!r}")


def envelope_fit(env, cost):
    """Return (fits_hard, over_soft, projected) for a move's cost against the envelope."""
    tol = env.get("tolerance", 3.0); projected = {}; fits = True; over_soft = False
    for r in RESOURCES:
        ceiling = env[r]["ceiling"]; spent = env[r].get("spent", 0) + env[r].get("committed", 0)
        p = spent + cost.get(r, 0); projected[r] = p
        if p > ceiling * tol: fits = False
        if p > ceiling: over_soft = True
    return fits, over_soft, projected


def route(closure, candidate, ctx, manifest, portfolio):
    """The decision. Pure function of its inputs plus the guard state carried in the portfolio."""
    key = closure_key(closure, ctx)
    env = manifest["envelope"]; rights = manifest.get("decision_rights", {})
    delegated = set(rights.get("delegated", REMEDIES.keys()))
    state = portfolio.setdefault("guard_state", {}).setdefault(candidate, {"depth": 0, "reentry": {}, "failures": {}, "retired": []})
    after_outcomes = bool(ctx.get("outcomes_seen", False))
    ctx = dict(ctx); ctx["before_a1"] = not after_outcomes
    ctx["portfolio_has_next"] = any(c["status"] == "active" and c["id"] != candidate for c in portfolio.get("candidates", []))

    launched, carded, refused = [], [], []
    if state["depth"] >= GUARDS["max_depth"]:
        refused.append({"remedy": "*", "reason": f"remedy depth {state['depth']} reached the guard; the candidate closes as it stands"})
        remedies = []
    else:
        remedies = TABLE[key]
    reentered = set()
    for rid in remedies:
        r = REMEDIES[rid]
        fits, over_soft, projected = envelope_fit(env, r["cost"])
        missing = [n for n in r["needs"] if not ctx.get(n)]
        entry = {"remedy": rid, "class": r["cls"], "reentry": r["reentry"], "what": r["what"], "cost": r["cost"]}
        if rid in state["retired"]:
            refused.append({**entry, "reason": "retired: failed twice for this candidate"}); continue
        if r["cls"] == "reserved" or rid not in delegated:
            carded.append({**entry, "reason": "reserved to the human by the decision rights"}); continue
        if r["prereg"] and after_outcomes:
            carded.append({**entry, "reason": "changes a preregistered element after outcomes were seen; reserved"}); continue
        if missing:
            refused.append({**entry, "reason": f"precondition not met: {', '.join(missing)}"}); continue
        if not fits:
            carded.append({**entry, "reason": "projected spend exceeds the envelope's hard limit; needs a human", "projected": projected}); continue
        if state["reentry"].get(r["reentry"], 0) >= GUARDS["max_reentry"] and r["reentry"] != "portfolio":
            refused.append({**entry, "reason": f"stage {r['reentry']} already re-entered {GUARDS['max_reentry']} times for this candidate"}); continue
        if r["reentry"] in reentered:
            refused.append({**entry, "reason": f"stage {r['reentry']} already re-entered by an earlier move in this decision"}); continue
        # launch: commit the cost, count the re-entry, flag soft overruns
        for res in RESOURCES: env[res]["committed"] = env[res].get("committed", 0) + r["cost"].get(res, 0)
        if r["reentry"] != "portfolio": state["reentry"][r["reentry"]] = state["reentry"].get(r["reentry"], 0) + 1
        reentered.add(r["reentry"])
        launched.append({**entry, "over_soft_ceiling": over_soft, "projected": projected})
    if launched: state["depth"] += 1
    rec = {"closure": closure, "key": key, "candidate": candidate, "outcomes_seen": after_outcomes,
           "launched": launched, "carded": carded, "refused": refused,
           "guard_state": dict(state), "envelope_after": {r: dict(env[r]) for r in RESOURCES},
           "amendments": [f"O1: {l['remedy']} re-enters {l['reentry']} for {candidate}" for l in launched],
           "completeness": (f"routed {closure} as {key} for {candidate}: {len(launched)} launched, {len(carded)} carded to the human, "
                            f"{len(refused)} refused, depth {state['depth']} of {GUARDS['max_depth']}")}
    return rec


def report_outcome(portfolio, candidate, remedy, succeeded):
    """R-stage feedback: a failed move counts against its retirement; a success resets nothing."""
    st = portfolio["guard_state"][candidate]
    if not succeeded:
        st["failures"][remedy] = st["failures"].get(remedy, 0) + 1
        if st["failures"][remedy] >= GUARDS["max_failures"] and remedy not in st["retired"]: st["retired"].append(remedy)


def next_candidate(portfolio):
    """Highest-priority active candidate: resolving power first, cost class to break ties."""
    act = [c for c in portfolio.get("candidates", []) if c["status"] == "active"]
    if not act: return None
    return sorted(act, key=lambda c: (-c.get("resolving_power", 0), c.get("cost_class", 9)))[0]


def card(rec):
    lines = [f"# Decision card: {rec['closure']} on {rec['candidate']}", ""]
    if rec["launched"]:
        lines += ["Running now, no decision needed:"] + [f"- {l['remedy']} (re-enters {l['reentry']}): {l['what']}" for l in rec["launched"]] + [""]
    if rec["carded"]:
        lines += ["Your decisions:"] + [f"- {c['remedy']}: {c['what']}. Why you: {c['reason']}" for c in rec["carded"]] + [""]
    if rec["refused"]:
        lines += ["Not taken:"] + [f"- {r['remedy']}: {r['reason']}" for r in rec["refused"]] + [""]
    lines.append(rec["completeness"])
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("route"); r.add_argument("--closure", required=True); r.add_argument("--candidate", required=True)
    r.add_argument("--context", required=True); r.add_argument("--manifest", required=True); r.add_argument("--portfolio", required=True)
    r.add_argument("--out")
    c = sub.add_parser("card"); c.add_argument("decision")
    n = sub.add_parser("next"); n.add_argument("--portfolio", required=True)
    a = p.parse_args()
    if a.cmd == "route":
        ctx = json.load(open(a.context)); man = json.load(open(a.manifest)); pf = json.load(open(a.portfolio))
        rec = route(a.closure, a.candidate, ctx, man, pf)
        json.dump(pf, open(a.portfolio, "w"), indent=2); json.dump(man, open(a.manifest, "w"), indent=2)
        txt = json.dumps(rec, indent=2)
        if a.out: open(a.out, "w").write(txt + "\n")
        print(txt); print("\n" + card(rec), file=sys.stderr)
        return 0
    if a.cmd == "card":
        print(card(json.load(open(a.decision)))); return 0
    if a.cmd == "next":
        nxt = next_candidate(json.load(open(a.portfolio)))
        print(json.dumps(nxt, indent=2) if nxt else "no active candidate"); return 0


if __name__ == "__main__": raise SystemExit(main())
