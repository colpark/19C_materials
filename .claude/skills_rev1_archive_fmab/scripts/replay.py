#!/usr/bin/env python3
"""Replay harness. Must-fire and must-not-fire are reported separately,
because one aggregate rate hides a module that flags everything.

    python replay.py audit
    python replay.py emit  --set development --stage P3
    python replay.py score --verdicts v.json --set sealed
"""
import argparse, csv, json, os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
CASES = os.path.join(HERE, "..", "cases", "cases.csv")
RULINGS = os.path.join(HERE, "..", "cases", "RULINGS_SEALED.csv")
MODULE = {"D": "discovery", "P": "supply", "I": "instrument", "R": "runtime", "A": "adjudication", "L": "ladder"}

def load(path=CASES):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))

def mod(stage):
    return MODULE.get(stage[0], "?")

def pick(cases, which="all", stage=None, module=None):
    out = cases
    if which == "development": out = [c for c in out if c["sealed"].strip().upper() != "Y"]
    elif which == "sealed":    out = [c for c in out if c["sealed"].strip().upper() == "Y"]
    if stage:  out = [c for c in out if c["stage"] == stage]
    if module: out = [c for c in out if mod(c["stage"]) == module]
    return out

def cmd_emit(a):
    cs = pick(load(), a.set, a.stage, a.module)
    if not cs: raise SystemExit("no cases match")
    for c in cs:
        print(f"--- {c['case_id']}  stage={c['stage']}  polarity={c['polarity']}")
        print(c["input"]); print()
    print(f"{len(cs)} cases. Write verdicts as:")
    print(json.dumps({cs[0]["case_id"]: {"fired": True, "ruling": "...", "via": "stage"}}, indent=2))
    print('"via" is "stage" when the stage\'s own refusal caught it, "validator" when')
    print("only the provenance check did. A validator-only pass is not earned.")
    return 0

def cmd_score(a):
    cs = {c["case_id"]: c for c in pick(load(), a.set, a.stage, a.module)}
    if not cs: raise SystemExit("no cases match")
    v = json.load(open(a.verdicts))
    rul = {r["case_id"]: r for r in csv.DictReader(open(RULINGS, newline=""))} if os.path.exists(RULINGS) else {}
    tal = defaultdict(lambda: {"n": 0, "ok": 0, "miss": 0})
    bymod = defaultdict(lambda: {"n": 0, "ok": 0})
    vonly, lines = [], []
    for cid, c in sorted(cs.items()):
        pol = c["polarity"]; t = tal[pol]; t["n"] += 1
        m = bymod[mod(c["stage"])]; m["n"] += 1
        got = v.get(cid)
        if got is None:
            t["miss"] += 1
            lines.append(f"  {cid:4s} {c['stage']:<7}{pol:<14}NO VERDICT, undemonstrated"); continue
        ok = bool(got.get("fired")) == (pol == "must_fire")
        if ok: t["ok"] += 1; m["ok"] += 1
        if ok and got.get("via") == "validator": vonly.append(cid)
        note = "" if ok else rul.get(cid, {}).get("rule_it_rests_on", "")
        lines.append(f"  {cid:4s} {c['stage']:<7}{pol:<14}{'ok  ' if ok else 'FAIL'} {note}")
    print(f"set={a.set}" + (f" stage={a.stage}" if a.stage else "") + (f" module={a.module}" if a.module else ""))
    print("\n".join(lines)); print()
    for pol in ("must_fire", "must_not_fire"):
        t = tal[pol]
        if t["n"]:
            print(f"{pol:<14}{t['ok']} of {t['n']}" + (f", {t['miss']} undemonstrated" if t["miss"] else ""))
    print()
    for k in sorted(bymod):
        m = bymod[k]; print(f"  {k:<14}{m['ok']} of {m['n']}")
    if vonly:
        print(f"\nvalidator-only {len(vonly)}: {', '.join(vonly)}")
        print("  Convert each into a required refusal inside its owning stage.")
    failed = sum(t["n"] - t["ok"] for t in tal.values())
    if failed: print(f"\n{failed} case(s) failed.")
    return 1 if failed else 0

def cmd_audit(a):
    cs = load()
    by = defaultdict(lambda: {"must_fire": 0, "must_not_fire": 0, "sealed": 0})
    for c in cs:
        e = by[mod(c["stage"])]; e[c["polarity"]] += 1
        if c["sealed"].strip().upper() == "Y": e["sealed"] += 1
    print(f"{len(cs)} cases across {len(by)} modules\n")
    print(f"{'module':<16}{'must_fire':>10}{'must_not_fire':>15}{'sealed':>8}")
    probs = []
    for k in sorted(by):
        e = by[k]
        print(f"{k:<16}{e['must_fire']:>10}{e['must_not_fire']:>15}{e['sealed']:>8}")
        if e["must_not_fire"] == 0:
            probs.append(f"{k}: no must-not-fire case, it would score full marks by flagging everything")
        if e["sealed"] == 0:
            probs.append(f"{k}: nothing sealed, every case is available for tuning")
    mnf = sum(e["must_not_fire"] for e in by.values())
    if mnf < len(cs) * 0.25:
        probs.append("under a quarter of cases are must-not-fire, over-firing will go undetected")
    print()
    for p in probs: print(f"  - {p}")
    if not probs: print("  suite shape ok")
    return 1 if probs else 0

def main():
    p = argparse.ArgumentParser(); sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in (("emit", cmd_emit), ("score", cmd_score), ("audit", cmd_audit)):
        s = sub.add_parser(name)
        if name != "audit":
            s.add_argument("--set", default="development", choices=["development", "sealed", "all"])
            s.add_argument("--stage"); s.add_argument("--module")
        if name == "score": s.add_argument("--verdicts", required=True)
        s.set_defaults(fn=fn)
    a = p.parse_args(); return a.fn(a)

if __name__ == "__main__":
    raise SystemExit(main())
