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
AXES = {"positive_supply","negative_supply","contamination_exposure","tool_coverage",
        "cluster_structure","split_integrity","unprocessable_units"}
REQ = {"axis_ledger":["candidate","axes","ruling","completeness"],
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
    if kind == "power_record" and o.get("ruling") == "RESOLVABLE" and o.get("mde", 1) > o.get("delta", 0):
        f.append("ruled RESOLVABLE while MDE exceeds delta")
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
            if t.get("status") == "CERTIFIED" and cr.get("construct_validity") != "PASS":
                f.append(f"{t.get('name')}: CERTIFIED without construct validity")
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
        worst |= 1 if f else 0
    return worst

if __name__ == "__main__": raise SystemExit(main())
