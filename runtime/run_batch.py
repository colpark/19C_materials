"""Run the arm cohort: every (episode, arm) cell once, arms interleaved per episode, N in parallel.

    python runtime/run_batch.py --tag main --arms bare classical fm --workers 4 [--limit N]

Cells that already exist are skipped (never retried). The order is a fixed shuffle of the cohort.
"""
import argparse, concurrent.futures as cf, hashlib, json, random, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "runtime"))
import run_cell

ap = argparse.ArgumentParser()
ap.add_argument("--tag", required=True); ap.add_argument("--arms", nargs="+", required=True)
ap.add_argument("--workers", type=int, default=4); ap.add_argument("--limit", type=int, default=None)
ap.add_argument("--episodes", nargs="*", default=None)
a = ap.parse_args()

cohort = a.episodes or json.loads((ROOT / "discovery/corpus_ledger.json").read_text())["corpus"]["arm_cohort"]
cohort = sorted(cohort, key=lambda e: hashlib.sha256(("order|" + e).encode()).hexdigest())
if a.limit: cohort = cohort[:a.limit]
jobs = []
for i, e in enumerate(cohort):
    arms = list(a.arms); random.Random(e).shuffle(arms)
    jobs += [(e, arm) for arm in arms]
todo = [(e, arm) for e, arm in jobs if not (ROOT / "runtime/cells" / a.tag / f"{e}__{arm}").exists()]
print(f"{len(jobs)} cells, {len(todo)} to run", flush=True)
log = ROOT / "runtime/cells" / a.tag / "batch_log.jsonl"; log.parent.mkdir(parents=True, exist_ok=True)

def one(job):
    e, arm = job
    try:
        m = run_cell.run(e, arm, a.tag)
    except SystemExit as x:
        m = {"skipped": str(x)}
    except Exception as x:
        m = {"error": repr(x)[:300]}
    rec = dict(episode=e, arm=arm, t=time.time(), **{k: m.get(k) for k in ("wall_s", "exit_code", "timed_out", "result_subtype", "num_turns", "cost_usd", "error", "skipped")})
    with open(log, "a") as f: f.write(json.dumps(rec) + "\n")
    print(json.dumps(rec), flush=True)
    return rec

with cf.ThreadPoolExecutor(a.workers) as ex:
    list(ex.map(one, todo))
