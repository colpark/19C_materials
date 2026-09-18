"""R2 isolating probe via a real MCP stdio client (no model): one FM tool, value read back, forged id rejected."""
import asyncio, json, sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
EP = sys.argv[1]; OUT = f"runtime/r2/{EP}"
async def main():
    p = StdioServerParameters(command="env/.venv/bin/python", args=["runtime/mcp/server.py", "--episode", EP, "--arm", "fm", "--out", OUT])
    res = {}
    async with stdio_client(p) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            tools = await s.list_tools(); res["catalog"] = sorted(t.name for t in tools.tools)
            ph = json.loads((await s.call_tool("list_phases", {})).content[0].text)
            tern = [x for x in ph["phases"] if x["sb_fraction"] not in (None, 1.0) and "Sb" in x["formula"] and "O" in x["formula"]]
            pid = tern[0]["id"]
            res["mace"] = json.loads((await s.call_tool("mace_stability", {"phase_id": pid})).content[0].text)
            res["gap"] = json.loads((await s.call_tool("megnet_bandgap", {"phase_id": pid})).content[0].text)
            f = await s.call_tool("mace_stability", {"phase_id": "mp-FORGED-999"}); res["forged"] = dict(is_error=f.is_error, text=f.content[0].text[:200])
            for i in range(6): last = json.loads((await s.call_tool("measure_eqe", {"index": i})).content[0].text)
            res["budget_6th_eqe"] = last
            hyp = json.loads((await s.call_tool("substitute_structure", {"phase_id": pid, "from_element": "Sb", "to_element": "Bi"})).content[0].text)
            res["hyp"] = hyp; res["hyp_mace"] = (await s.call_tool("mace_stability", {"phase_id": hyp["id"]})).content[0].text
    print(json.dumps(res, indent=1)); json.dump(res, open(f"{OUT}/r2_result.json", "w"), indent=1)
asyncio.run(main())
