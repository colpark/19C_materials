"""R2 for server_pool fm_forced on a burned episode: FM value read back, forged receipt rejected, consultation gate both ways."""
import asyncio, json, sys, os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
EP = sys.argv[1]; OUT = f"rev23/runtime/r2/{EP}"
async def main():
    env = dict(os.environ, FMAB_B_EQE="3")
    p = StdioServerParameters(command="env/.venv/bin/python", args=["runtime/mcp/server_pool.py", "--episode", EP, "--arm", "fm_forced", "--out", OUT], env=env)
    res = {}; J = lambda r: json.loads(r.content[0].text)
    async with stdio_client(p) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            res["catalog"] = sorted(t.name for t in (await s.list_tools()).tools)
            info = J(await s.call_tool("episode_info", {}))
            res["gate_must_fire"] = J(await s.call_tool("measure_eqe", {"index": 3}))
            ph = J(await s.call_tool("list_phases", {}))
            pid = next(x["id"] for x in ph["phases"] if sum(v > 0 for v in x["cation_fractions"].values()) >= 2)
            m = J(await s.call_tool("mace_stability", {"phase_id": pid})); res["mace"] = m
            res["forged_receipt"] = J(await s.call_tool("record_consultation", {"index": 3, "receipts": ["deadbeef0000"], "verdict": "forged receipt should be rejected by the gate"}))
            res["consult_ok"] = J(await s.call_tool("record_consultation", {"index": 3, "receipts": [m["receipt"]], "verdict": "the MACE hull says this phase is stable, so measuring candidate 3 is supported"}))
            res["gate_must_not_fire"] = J(await s.call_tool("measure_eqe", {"index": 3}))
            res["gate_refires_after_measure"] = J(await s.call_tool("measure_eqe", {"index": 4}))
    json.dump(res, open(f"{OUT}/r2_result.json", "w"), indent=1); print(json.dumps({k: (v if k != "catalog" else v) for k, v in res.items()}, indent=1)[:2500])
asyncio.run(main())
