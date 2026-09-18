import asyncio, json, os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
EP="2283_20200218.144324_CA3"; OUT="rev23/runtime/g1/"+EP
async def main():
    p=StdioServerParameters(command="env/.venv/bin/python",args=["runtime/mcp/server_pool.py","--episode",EP,"--arm","classical","--out",OUT],env=dict(os.environ,FMAB_B_EQE="3"))
    J=lambda r: json.loads(r.content[0].text); out=[]
    async with stdio_client(p) as (r,w):
        async with ClientSession(r,w) as s:
            await s.initialize()
            for i in range(4): out.append(J(await s.call_tool("measure_eqe",{"index":i})))
    json.dump(out,open(OUT+"/g1.json","w"),indent=1); print([("error" in o) for o in out])
asyncio.run(main())
