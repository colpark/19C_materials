# R1 harness control for the pooled server: dispositions declared before the run

Subject claude-opus-5; server `runtime/mcp/server_pool.py`, arm `stub`; synthetic 5-point line; true best index 2.

- **PASS:** the MCP server connects; the init catalog is exactly the 4 env tools; there is at least one merit measurement and exactly one submit.
- **FAIL-surface:** no connection, no calls, or a process error. Send back to the instrument module.
- **FAIL-subject:** connected, but no submit or fabricated results.
