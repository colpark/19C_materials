#!/usr/bin/env python3
"""Check that every number carries its five provenance fields and every ledger
carries a completeness assertion. A stage that declines to rule scores the same
as one that rules correctly unless completeness is asserted.

    python validate.py provenance pr.json
    python validate.py ledger axis_ledger.json --kind axis_ledger
"""
import argparse, json, re, sys
FIVE = ["referent", "source", "population", "adjudicator", "falsifier"]
ID = re.compile(r"(::|/|\bcommit\b|\brevision\b|\bsha\b|\bhash\b|\bpinned\b|\bv\d+\.\d+"
                r"|\btable\s*\d|\bsection\s*\d|\.py\b|\.json\b|\.csv\b|\.md\b)", re.I)
OBS = re.compile(r"\b(rerun|re-run|permut|shuffl|invert|swap|replac|remov|withhold|ablat|exceed"
                 r"|below|outside|differ|fail|match|reproduc|resolve|return|measur)\w*", re.I)
HEDGE = re.compile(r"\b(probably|presumably|should be|seems|appears to be|roughly)\b", re.I)
NOTES = []  # informational, never a failure
AXES = {"positive_supply","negative_supply","contamination_exposure","tool_coverage",
        "cluster_structure","split_integrity","unprocessable_units"}
REQ = {"axis_ledger":["candidate","axes","ruling","completeness"],
       "lift_record":["n","mean_lift","ci95","delta","role","ruling","completeness"],
       "decision_record":["closure","key","candidate","launched","carded","refused","guard_state","envelope_after","completeness"],
       "power_record":["chance","n","sigma_d","mde","n_min","ruling","completeness"],
       "tool_card":["quantity_returned","served_checkpoint","disagreements","written_from"],
       "certification_record":["tools","completeness"],
       "gate_register":["gates","completeness"],
       "grant_record":["verified_from","model_side_catalog","canaries","completeness"],
       "score_record":["primary_metric","chance","arms","mde","claim","completeness"],
       "corpus_ledger":["seeds","inclusion_rules","rules_frozen_before_count","exclusion_ledger","coverage"],
       "cut_curve":["chosen_cut","justification","curve","sensitivity","completeness"],
       "domain_manifest":["tau","k","label_source","exposure_key","tool_inventory","delta","S","subject_set","frozen_hash"]}
ASSUMED = re.compile(r"^\s*(assumed|conventional|standard|typical|usual|default)\b", re.I)

def prov(r, f, tag=""):
    t = f"{tag}: " if tag else ""
    for k in FIVE:
        if not str(r.get(k, "")).strip(): f.append(f"{t}{k!r} empty. All five must resolve")
    if r.get("source") and not ID.search(str(r["source"])):
        f.append(f"{t}source has no identifier. An observation is not a specification")
    if r.get("falsifier") and not OBS.search(str(r["falsifier"])):
        f.append(f"{t}falsifier names no observation. It cannot be tested")
    for k in ("source", "adjudicator"):
        if HEDGE.search(str(r.get(k, ""))): f.append(f"{t}{k} hedges. State it or state it is unknown")

def ledger(o, kind, f):
    req = REQ.get(kind)
    if req is None: return f.append(f"unknown kind {kind!r}. Known: {sorted(REQ)}")
    for k in req:
        if o.get(k) in (None, "", [], {}): f.append(f"missing or empty {k!r}")
    if len(str(o.get("completeness", ""))) < 20:
        f.append("completeness assertion too thin to name what was covered and what was not")
    if kind == "axis_ledger":
        seen = {a.get("axis") for a in o.get("axes", []) if isinstance(a, dict)}
        for m in sorted(AXES - seen): f.append(f"axis {m!r} not counted. P4 refuses an incomplete ledger")
        if o.get("definition_widened"): f.append("a definition was widened after a low count")
        if o.get("ruling") and not o.get("binding_axis"): f.append("ruling without naming the binding axis")
        scope = o.get("scope", "provisional")
        if scope == "final" and "channel_lift" not in seen:
            f.append("final ruling without the eighth axis, channel lift from I2. No arm runs on this ledger")
        if scope != "final":
            NOTES.append("axis ledger scope is provisional: licenses I1 and I2 only, never an arm")
    if kind == "power_record" and o.get("ruling") == "RESOLVABLE" and o.get("mde", 1) > o.get("delta", 0):
        f.append("ruled RESOLVABLE while MDE exceeds delta")
    if kind == "power_record":
        scope = o.get("scope", "provisional")
        if scope == "final":
            if o.get("mde_pilot") is None or o.get("n_pilot") is None:
                f.append("final power record without pilot arm variance. The free variance is a lower bound, never the estimate")
            elif o.get("mde", 0) < max(o.get("mde_pilot", 0), o.get("mde_provisional", 0)) - 1e-9:
                f.append("final MDE is smaller than one of its two passes. The final record carries the larger")
            if o.get("n_pilot", 0) < 10: f.append("final power record on a pilot below ten items")
            if o.get("ruling") == "RUN_AT_LIMIT":
                if o.get("n_pilot", 0) < 20: f.append("RUN_AT_LIMIT before the pilot was enlarged to twenty")
                if o.get("mde_lower", 1) > o.get("delta", 0): f.append("RUN_AT_LIMIT while the lower bound exceeds delta. That is CLOSE")
                if o.get("mde", 0) <= o.get("delta", 1): f.append("RUN_AT_LIMIT with point MDE at or below delta. That is RESOLVABLE")
            if o.get("ruling") == "CLOSE_UNRESOLVABLE" and o.get("mde_lower") is not None and o.get("mde_lower") <= o.get("delta", 0):
                f.append("closed on a point estimate whose lower bound sits at or below delta. Enlarge the pilot or run at limit")
        else:
            NOTES.append("power record scope is provisional: R5 arms nothing and A3 scores nothing on it")
            if o.get("ruling") in ("ESCALATE_ENLARGE_PILOT", "UNDEMONSTRATED"):
                NOTES.append(f"{o.get('ruling')}: the second pass has not finished")
    if kind == "decision_record":
        for l in o.get("launched", []):
            if l.get("class") != "autonomous": f.append(f"{l.get('remedy')}: launched but not autonomous")
            if o.get("outcomes_seen") and l.get("remedy") in ("change_role_scorer_lift", "forced_consultation_lift", "change_task_budget", "different_scored_quantity", "accept_proxy_grader"):
                f.append(f"{l.get('remedy')}: changes a preregistered element after outcomes were seen. Refusal 21")
            env = o.get("envelope_after", {})
            for res, v in env.items():
                if isinstance(v, dict) and v.get("ceiling") and (v.get("spent", 0) + v.get("committed", 0)) > v["ceiling"] * 3.0 + 1e-9:
                    f.append(f"{res}: committed past the hard limit. Refusal 22")
        gs = o.get("guard_state", {})
        if gs.get("depth", 0) > 3: f.append("remedy depth above three. Refusal 22")
        if not o.get("launched") and not o.get("carded") and not o.get("refused"): f.append("a routing with no moves considered is 'open for the user'. Refusal 23")
    if kind == "lift_record":
        lo, hi = (o.get("ci95") or [None, None])[:2]
        if lo is not None and hi is not None and lo <= 0 <= hi and hi < o.get("delta", 0) and o.get("ruling") == "ADVANCE":
            f.append("interval covers zero and its upper bound sits below delta, yet the channel ADVANCED. I2 closes or lifts it")
        if o.get("ruling") == "LIFT" and o.get("role") != "agent_input":
            f.append("LIFT recorded for a channel that scores a fixed input. Only a channel on an agent-built input earns a lift")
    if kind == "power_record" and o.get("items_filtered_on_outcome"):
        f.append("items filtered on the outcome variable. Stratify instead")
    if kind == "tool_card":
        if o.get("written_from") != "code": f.append("card not written from code")
        if "disagreements" not in o: f.append("disagreement list absent. Silent reconciliation reproduces the failure")
        c = o.get("served_checkpoint", {})
        if not c.get("pin"): f.append("served checkpoint has no pin")
        if c.get("matches_adjudicating_composition") is False:
            f.append("served checkpoint differs from the composition it competes against. Halt")
    if kind == "certification_record":
        for t in o.get("tools", []):
            cr = t.get("criteria", {})
            if t.get("status") == "CERTIFIED" and cr.get("construct_validity") not in ("PASS", "PROXY"):
                f.append(f"{t.get('name')}: CERTIFIED without construct validity")
            if cr.get("construct_validity") == "PROXY" and not t.get("lift_ruling"):
                f.append(f"{t.get('name')}: PROXY on the scored quantity with no I2 ruling attached. A proxy pass travels to I2")
            if str(t.get("status", "")).upper() == "READY": f.append(f"{t.get('name')}: reported READY")
    if kind == "gate_register":
        for g in o.get("gates", []):
            mf, mn = g.get("must_fire_control", {}), g.get("must_not_fire_control", {})
            if g.get("armed") and not (mf.get("fired") and mn.get("fired") is False):
                f.append(f"{g.get('id')}: armed without both controls")
            if not g.get("named_threat"): f.append(f"{g.get('id')}: no named threat")
            if g.get("duplicates_platform_protection"): f.append(f"{g.get('id')}: duplicates a platform protection")
        for c in o.get("provenance_chain", []):
            if c.get("action") == "block" and c.get("difference_class") != "substantive":
                f.append(f"{c.get('cell')}: blocked before classifying the difference")
    if kind == "grant_record":
        if o.get("verified_from") != "model_side": f.append("grant read from configuration")
        for c in o.get("canaries", []):
            if c.get("excluded") and c.get("canary_result") == "unrun":
                f.append(f"{c.get('capability')}: excluded but never canaried")
        if o.get("arm_symmetry") is not None:
            for d in o.get("arm_symmetry", []):
                if d.get("differs") and not d.get("ruling"): f.append(f"arm difference {d.get('field')} unruled")
    if kind == "corpus_ledger":
        for sd in o.get("seeds", []):
            if not sd.get("read_in_full"):
                f.append(f"seed {sd.get('id')} not read in full. Never curate from summaries")
            for fact in sd.get("facts", []):
                if not fact.get("locator"): f.append(f"seed {sd.get('id')}: a fact carries no locator")
        if o.get("rules_frozen_before_count") is not True:
            f.append("inclusion rules were not frozen before counting")
        if "coverage" in o and "completeness_claim" in o:
            f.append("a curated corpus states coverage as an inventory, never a completeness claim")
        for it in o.get("answer_in_own_source", []):
            if isinstance(it, dict) and it.get("admitted") and not it.get("exposure_ruling"):
                f.append(f"{it.get('item')}: answer appears in its own source with no exposure ruling")
    if kind == "cut_curve":
        if o.get("chosen_to_increase_unit_count"): f.append("cut chosen to increase unit count")
        if len(o.get("curve", [])) < 3: f.append("fewer than three cuts swept, the curve bounds nothing")
        sen = o.get("sensitivity", {})
        if not (sen.get("looser") is not None or sen.get("tighter") is not None):
            f.append("no sensitivity reported at a looser or tighter cut")
    if kind == "domain_manifest":
        for k in REQ["domain_manifest"]:
            v = o.get(k)
            if isinstance(v, dict):
                pr = v.get("provenance", {})
                if ASSUMED.search(str(pr.get("source", ""))):
                    f.append(f"slot {k!r}: source reads assumed or conventional and does not resolve")
                prov(pr, f, f"slot {k}")
                if v.get("status") == "OVERRIDDEN" and not v.get("override_reason"):
                    f.append(f"slot {k!r}: overridden with no reason recorded")
    if kind == "score_record":
        if o.get("blind_files_hashed_before_labels") is False: f.append("labels opened before blind files hashed")
        dens = {a.get("denominator") for a in o.get("arms", [])}
        if len(dens) > 1 and not o.get("paired_comparisons"):
            f.append("unequal denominators with no paired comparison")
        for a_ in o.get("arms", []):
            if a_.get("primary") == 0 and a_.get("coverage_failures"):
                f.append(f"{a_.get('arm')}: scored zero while carrying coverage failures")
        for c in o.get("paired_comparisons", []):
            if abs(c.get("delta_primary", 0)) <= o.get("mde", 0) and o.get("claim") == "SEPARATION_DETECTED":
                f.append("separation claimed at or below the minimum detectable effect")

def main():
    p = argparse.ArgumentParser()
    p.add_argument("mode", choices=["provenance", "ledger"]); p.add_argument("paths", nargs="+")
    p.add_argument("--kind", default="auto")
    a = p.parse_args(); worst = 0
    for path in a.paths:
        o = json.load(open(path)); f = []
        if a.mode == "provenance":
            for r in (o if isinstance(o, list) else [o]): prov(r, f, r.get("id", ""))
        else:
            kind = a.kind
            if kind == "auto":
                kind = next((k for k in REQ if k in path), "unknown")
            ledger(o, kind, f)
            for r in o.get("provenance", []): prov(r, f, r.get("id", ""))
        print(("FAIL " if f else "PASS ") + path)
        for x in f: print(f"  - {x}")
        for x in NOTES: print(f"  ~ {x}")
        NOTES.clear()
        worst |= 1 if f else 0
    return worst

if __name__ == "__main__": raise SystemExit(main())
