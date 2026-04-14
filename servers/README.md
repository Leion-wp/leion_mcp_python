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
