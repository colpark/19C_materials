"""Run one agent cell: claude -p (subject model) against the episode MCP server for one arm.

    python runtime/run_cell.py --episode <id> --arm bare|classical|fm|stub [--tag r1]

No retry is allowed: an existing cell directory refuses. Traces are stream-json.
"""
from __future__ import annotations
import argparse, hashlib, json, os, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = ROOT / "env/.venv/bin/python"
MODEL = "claude-opus-5"
DISALLOWED = ("Task,Agent,Bash,CronCreate,CronDelete,CronList,DesignSync,Edit,EnterWorktree,ExitWorktree,"
              "ListAgents,Monitor,NotebookEdit,PushNotification,Read,RemoteTrigger,ReportFindings,"
              "ScheduleWakeup,SendMessage,Skill,TaskOutput,TaskStop,TaskCreate,TaskGet,TaskList,TaskUpdate,"
              "ToolSearch,WebFetch,WebSearch,Workflow,Write,Glob,Grep,ListMcpResourcesTool,"
              "ReadMcpResourceTool,ReadMcpResourceDirTool,Artifact,ArtifactComments,ArtifactData,AskUserQuestion,EnterPlanMode,ExitPlanMode")
PROMPT_PATH = ROOT / os.environ.get("FMAB_PROMPT", "runtime/prompt.md")
PROMPT = PROMPT_PATH.read_text() if PROMPT_PATH.exists() else ""
SERVER = ROOT / os.environ.get("FMAB_SERVER", "runtime/mcp/server.py")


def sha(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def run(episode: str, arm: str, tag: str, timeout: int = 1500) -> dict:
    cell = ROOT / "runtime/cells" / tag / f"{episode}__{arm}"
    if cell.exists():
        raise SystemExit(f"refusing to retry {cell}")
    (cell / "workdir").mkdir(parents=True)
    cfg = {"mcpServers": {"env": {"command": str(PY), "args": [str(SERVER),
            "--episode", episode, "--arm", arm, "--out", str(cell)],
            "env": {k: v for k, v in os.environ.items() if k.startswith("FMAB_") or k in ("PATH", "HOME", "LD_LIBRARY_PATH", "CUDA_VISIBLE_DEVICES", "HF_HOME", "XDG_CACHE_HOME")}}}}   # allowlist: mcp.json is committed
    (cell / "mcp.json").write_text(json.dumps(cfg, indent=1))
    prompt = PROMPT
    cmd = ["claude", "-p", "--model", MODEL, "--strict-mcp-config", "--mcp-config", str(cell / "mcp.json"),
           "--allowedTools", "mcp__env", "--disallowedTools", DISALLOWED,
           "--output-format", "stream-json", "--verbose", "--max-turns", "60"]
    env = dict(os.environ)
    env.pop("ANTHROPIC_API_KEY", None)
    env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
    env["CLAUDE_CODE_DISABLE_CLAUDE_MDS"] = "1"
    (cell / "launch.json").write_text(json.dumps({"cmd": cmd, "prompt_sha256": sha(prompt),
        "prompt_bytes": len(prompt.encode()), "prompt_path": str(PROMPT_PATH), "server": str(SERVER), "model": MODEL, "arm": arm, "episode": episode,
        "labels_opened": False}, indent=1))
    t0 = time.monotonic()
    try:
        p = subprocess.run(cmd, input=prompt, text=True, capture_output=True, cwd=cell / "workdir", env=env, timeout=timeout)
        out, err, code, to = p.stdout, p.stderr, p.returncode, False
    except subprocess.TimeoutExpired as e:
        out = (e.stdout or b"").decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        err, code, to = "", None, True
    (cell / "trace.jsonl").write_text(out)
    (cell / "stderr.txt").write_text(err)
    # emitted-side facts from the stream: model, tool catalog, first user message
    init, result = None, None
    for line in out.splitlines():
        try: ev = json.loads(line)
        except Exception: continue
        if ev.get("type") == "system" and ev.get("subtype") == "init": init = ev
        if ev.get("type") == "result": result = ev
    meta = {"wall_s": round(time.monotonic() - t0, 1), "exit_code": code, "timed_out": to,
            "init_model": init and init.get("model"), "init_tools": init and init.get("tools"),
            "init_mcp": init and init.get("mcp_servers"),
            "result_subtype": result and result.get("subtype"), "num_turns": result and result.get("num_turns"),
            "cost_usd": result and result.get("total_cost_usd")}
    (cell / "meta.json").write_text(json.dumps(meta, indent=1))
    return meta


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--episode", required=True); ap.add_argument("--arm", required=True)
    ap.add_argument("--tag", required=True); ap.add_argument("--timeout", type=int, default=1500)
    a = ap.parse_args()
    print(json.dumps(run(a.episode, a.arm, a.tag, a.timeout)))
