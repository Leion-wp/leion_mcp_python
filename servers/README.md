# Leion MCP servers (split)

This folder contains split FastMCP servers.

Each file defines a `server = FastMCP(...)` and registers only a subset of tools.

Recommended usage:
- Run each server on its own port.
- Expose only the router MCP to OpenWebUI (so the model doesn't see all tools).

Servers:
- mcp_fs.py: filesystem + patch + watch + monitor
- mcp_git_project.py: git + project scan/summary + repo builder
- mcp_workflows.py: workflows + workflow builder + flowise + CC workflow UI
- mcp_memory.py: memory + vector store + profile
- mcp_agents.py: agent planning + supervisor + orchestrator + CC agents UI
- mcp_integrations.py: composio + app listing/connection + comm planning
- mcp_dev_quality.py: refactor + deps + tests + observability
- mcp_business.py: business planning + assets + composio business + asset briefs
- mcp_ui.py: UI component planner
- mcp_control_center.py: dashboard + resources
- mcp_runtime.py: bounded cli_leion_engine runtime protocol (port 7011)
- mcp_n8n.py: bounded n8n public API adapter (port 7013)
- mcp_revenue.py: federated revenue meta-server over business/integrations/workflows/memory/runtime/n8n (port 7014)
- mcp_development.py: federated development meta-server over fs/git/workflows/memory/agents/dev/runtime/n8n (port 7015)


## Local CLI runtime server

The runtime server deliberately exposes the structured public CLI protocol
instead of an arbitrary shell tool. Configure `LEION_CLI_REPO` and
`LEION_RUNTIME_ALLOWED_ROOTS`, build `cli_leion_engine`, then run:

```powershell
python -m servers.mcp_runtime
```

Typical Windows configuration:

```dotenv
LEION_CLI_REPO=D:/Leion/cli_leion_engine
LEION_RUNTIME_ALLOWED_ROOTS=D:/Leion
MCP_RUNTIME_URL=http://localhost:7011
```

The MCP surface provides describe/catalog/validate/run/status/list/logs and
pause/resume/cancel operations. It does not expose `shell_run`.


## Multi-server launcher

Use the launcher to start a compartmented server set instead of opening each
terminal manually:

```powershell
.\start_leion.ps1 -Profile core
.\start_leion.ps1 -Profile revenue
.\start_leion.ps1 -Profile dev
.\start_leion.ps1 -Profile full
```

Equivalent Python command:

```powershell
python launcher/start_all.py --profile revenue
```

The launcher:
- skips ports that are already occupied and treats them as externally managed;
- writes one log file per MCP under `.logs/mcp`;
- restarts a managed server up to five times after a crash;
- terminates managed process trees on shutdown, including Windows children;
- starts the top-level router after its child servers.

The profile catalog lives in `launcher/servers.json`.
