"""R3 step 2 outputs: pilot item-level arm scores (for P7 final) and channel uptake per arm (for R8). Pilot items are burned."""
import json, sys, collections, pandas as pd
sys.path.insert(0, "bench"); import pool_floors as P
FM = {"mace_stability", "megnet_bandgap"}
split = json.load(open("rev21/pool/split.json")); cl = pd.read_csv("rev21/pool/floors_pooled_B3_clustered.csv").set_index("episode_id")["cluster"]
E = {e["episode_id"]: e for e in P.all_episodes()}
rows, up = [], collections.defaultdict(lambda: [0, 0])
for eid in split["pilot"]:
    r = dict(episode_id=eid, cluster=cl[eid])
    for arm in ("bare", "classical", "fm_forced"):
        d = f"runtime/cells/rev23_pilot/{eid}__{arm}"
        try:
            s = json.load(open(f"{d}/env.json")); meas = [int(k) for k in s["eqe"]]
            r[arm] = P.score(E[eid], meas) if meas else None
            tools = [json.loads(l)["tool"] for l in open(f"{d}/calls.jsonl")]
            up[arm][0] += any(t in FM for t in tools); up[arm][1] += 1
            r[arm + "_consultations"] = len(s.get("consultations", []))
        except FileNotFoundError:
            r[arm] = None
    rows.append(r)
df = pd.DataFrame(rows); df.to_csv("rev23/runtime/pilot_scores.csv", index=False)
coh = pd.DataFrame({"episode_id": split["cohort"]}); coh["cluster"] = coh.episode_id.map(cl); coh.to_csv("rev23/runtime/cohort_clusters.csv", index=False)
uptake = {a: dict(used=u, episodes=n, share=round(u / n, 3) if n else None) for a, (u, n) in up.items()}
json.dump(dict(uptake=uptake, band=0.8, channel="FM tools (mace_stability, megnet_bandgap)"), open("rev23/runtime/pilot_uptake.json", "w"), indent=1)
print(df.round(3).to_string()); print(uptake)
