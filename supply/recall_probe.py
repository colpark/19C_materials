"""P3 contamination axis: does the subject recall the published answer? Two framings per element; no tools."""
import json, os, re, subprocess, sys, concurrent.futures as cf
sys.path.insert(0, "bench"); sys.path.insert(0, "runtime")
import data, numpy as np
from run_cell import DISALLOWED
OUT = "supply/recall_probe"
RECALL = ("From memory: in the Caltech/JCAP high-throughput study of metal antimonate photoanodes (ACS Sustainable Chem. Eng., 2022; 22 X-Sb-O "
          "thin-film libraries, EQE measured at 3.2, 2.7, 2.4 and 2.1 eV), for X = {el}: at what Sb/(X+Sb) cation fraction did the highest EQE under "
          "{ev} eV illumination occur? Reply ONLY with JSON {{\"sb_fraction\": <0-1>, \"phase\": \"<formula>\", \"confidence\": <0-1>}}.")
PREDICT = ("Consider a sputtered, annealed {el}-Sb-O thin-film composition gradient spanning Sb/({el}+Sb) from about 0.1 to 0.9, measured for "
           "photoelectrochemical EQE under {ev} eV illumination. Predict the Sb/({el}+Sb) cation fraction with the highest EQE. Reply ONLY with JSON "
           "{{\"sb_fraction\": <0-1>, \"phase\": \"<formula>\", \"confidence\": <0-1>}}.")
def ask(prompt):
    env = dict(os.environ); env.pop("ANTHROPIC_API_KEY", None); env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"; env["CLAUDE_CODE_DISABLE_CLAUDE_MDS"] = "1"
    p = subprocess.run(["claude", "-p", "--model", "claude-opus-5", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
                        "--disallowedTools", DISALLOWED, "--output-format", "json"], input=prompt, text=True, capture_output=True, env=env, timeout=600, cwd="/tmp")
    try:
        txt = json.loads(p.stdout)["result"]; m = re.search(r"\{.*\}", txt, re.S); return json.loads(m.group(0))
    except Exception as e:
        return {"error": repr(e)[:200], "raw": p.stdout[-400:]}
def truth(el, rtech):
    v = [e["sb"][int(np.argmax(e["eqe"]))] for e in data.episodes() if e["el"] == el and e["rtech"] == rtech]
    return float(np.median(v))
jobs = [(el, rt, fr) for el in sorted({e["el"] for e in data.episodes()}) for rt in ("CA1", "CA4") for fr in ("recall", "predict")]
def one(j):
    el, rt, fr = j; ev = data.LED_EV[rt]
    r = ask((RECALL if fr == "recall" else PREDICT).format(el=el, ev=ev))
    return dict(el=el, rtech=rt, framing=fr, truth_sb=truth(el, rt), **r)
with cf.ThreadPoolExecutor(6) as ex: res = list(ex.map(one, jobs))
json.dump(res, open(f"{OUT}/responses.json", "w"), indent=1)
ok = [r for r in res if "sb_fraction" in r]
for fr in ("recall", "predict"):
    rr = [r for r in ok if r["framing"] == fr]
    hit = [abs(float(r["sb_fraction"]) - r["truth_sb"]) <= 0.05 for r in rr]
    err = [abs(float(r["sb_fraction"]) - r["truth_sb"]) for r in rr]
    print(fr, f"n={len(rr)} within0.05={sum(hit)} mean_abs_err={np.mean(err):.3f}")
# chance: uniform guess over the line vs truth
print("parse failures", len(res) - len(ok))
