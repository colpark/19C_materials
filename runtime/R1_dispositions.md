# R1 harness control: dispositions declared before the run

Subject: claude-opus-5. Arm: `stub`. Item: a synthetic 5-point line with no domain data; the true best is index 2.

- **PASS:** the subject calls `episode_info`, spends at least one EQE measurement, and calls `submit` exactly once. `env.json` records the calls. The stream-json `init` event lists only `mcp__env__*` tools plus no native tools, and model = claude-opus-5.
- **FAIL-surface:** the MCP server does not connect (`init` mcp_servers status ≠ connected), no calls are recorded, or the process errors. This indicts the harness and sends the work back to the instrument module.
- **FAIL-subject:** the server is connected and tools are listed, but the subject never calls `submit` or fabricates results without tool calls. This indicts the subject or prompt, which is not expected for a known-good model.
