"""P3 contamination on pooled units, run-1 protocol: 28 prompts per framing (recall vs predict), claude-opus-5, no tools.
Units: first unburned pooled episode (hash order) of each new chemistry (22), plus the next 6 episodes in hash order."""
import json, os, re, subprocess, sys, hashlib, concurrent.futures as cf
sys.path.insert(0, "bench"); sys.path.insert(0, "runtime")
import numpy as np, pool_floors as P
from run_cell import DISALLOWED
OUT = "rev23/supply/recall_probe"
burned = set(json.load(open("rev2/discovery/manifest_rev2.json"))["item_ledger"]["burned"])
eps = [e for e in P.all_episodes() if e["source"] == "pool" and e["episode_id"] not in burned]
rk = sorted(eps, key=lambda e: hashlib.sha256((e["episode_id"] + "|rev23-probe").encode()).hexdigest())
units, seen = [], set()
for e in rk:
    if e["chem"] not in seen: units.append(e); seen.add(e["chem"])
units += [e for e in rk if e not in units][:28 - len(units)]
def ev(e): return f"{e['led_eV']:.2f} eV" if e["led_eV"] else "the stated lamp"
RECALL = ("From memory: in the Caltech/JCAP high-throughput photoanode experiments deposited in MEAD / CaltechDATA (sputtered or printed metal-oxide "
          "composition libraries, photocurrent or EQE mapped across composition), for the {chem} oxide system under {ev} illumination: at what cation "
          "composition did the highest photoresponse occur? Reply ONLY with JSON {{\"fractions\": {{{keys}}}, \"phase\": \"<formula>\", \"confidence\": <0-1>}} with fractions summing to 1.")
PREDICT = ("Consider an annealed {chem} oxide thin-film composition library spanning the cation composition space, measured for photoelectrochemical "
           "photoresponse under {ev} illumination. Predict the cation composition with the highest photoresponse. Reply ONLY with JSON "
           "{{\"fractions\": {{{keys}}}, \"phase\": \"<formula>\", \"confidence\": <0-1>}} with fractions summing to 1.")
def ask(prompt):
    env = dict(os.environ); env.pop("ANTHROPIC_API_KEY", None); env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"; env["CLAUDE_CODE_DISABLE_CLAUDE_MDS"] = "1"
    p = subprocess.run(["claude", "-p", "--model", "claude-opus-5", "--strict-mcp-config", "--mcp-config", '{"mcpServers":{}}',
                        "--disallowedTools", DISALLOWED, "--output-format", "json"], input=prompt, text=True, capture_output=True, env=env, timeout=600, cwd="/tmp")
    try:
        j = json.loads(p.stdout); u = j.get("usage", {}); txt = j["result"]; m = re.search(r"\{.*\}", txt, re.S)
        return dict(json.loads(m.group(0)), usage_tokens=sum((u.get(k) or 0) for k in ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")))
    except Exception as ex:
        return {"error": repr(ex)[:200], "raw": p.stdout[-300:]}
def one(job):
    e, fr = job; keys = ", ".join(f'"{el}": <0-1>' for el in e["elements"])
    r = ask((RECALL if fr == "recall" else PREDICT).format(chem="-".join(e["elements"]), ev=ev(e), keys=keys))
    truth = np.array(e["comp"][int(np.argmax(e["merit"]))])
    out = dict(episode_id=e["episode_id"], chem=e["chem"], framing=fr, truth=truth.round(4).tolist(), **r)
    if "fractions" in r:
        try:
            v = np.array([float(r["fractions"].get(el, 0)) for el in e["elements"]]); v = v / v.sum()
            out["dist"] = float(0.5 * np.abs(v - truth).sum())
        except Exception as ex: out["parse_error"] = repr(ex)
    return out
jobs = [(e, fr) for e in units for fr in ("recall", "predict")]
with cf.ThreadPoolExecutor(6) as ex: res = list(ex.map(one, jobs))
json.dump(res, open(f"{OUT}/responses.json", "w"), indent=1)
summ = {}
for fr in ("recall", "predict"):
    rr = [r for r in res if r["framing"] == fr and "dist" in r]
    summ[fr] = dict(n=len(rr), within_0_05=sum(r["dist"] <= 0.05 for r in rr), mean_dist=round(float(np.mean([r["dist"] for r in rr])), 4))
summ["parse_failures"] = sum("dist" not in r for r in res); summ["tokens_m_measured"] = round(sum(r.get("usage_tokens", 0) for r in res) / 1e6, 3)
summ["units"] = len(units); json.dump(summ, open(f"{OUT}/summary.json", "w"), indent=1); print(json.dumps(summ))
