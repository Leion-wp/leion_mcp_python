# leion_mcp_python

FastMCP server for Leion OS, with tool registration, split MCP servers, and an optional web widget.

## Requirements

- Python 3.11 recommended
- Git
- Optional: Docker
- Optional: Cloudflared for public tunnel exposure

## Quick start

1. Create a virtual environment.
2. Install the project.
3. Copy `.env.example` to `.env` and fill in the required secrets.
4. Run the MCP server in HTTP mode.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
Copy-Item .env.example .env
fastmcp run main.py:server --transport http --host 0.0.0.0 --port 3101
```

## Local MCP fabric

For the local Windows setup, the split-server fabric can be launched in one
command after configuring `.env`:

```powershell
.\start_leion.ps1 -Profile core
.\start_leion.ps1 -Profile revenue
.\start_leion.ps1 -Profile dev
.\start_leion.ps1 -Profile full
```

`core` starts the router plus the CLI runtime and n8n adapter. `revenue`
adds workflows, memory, integrations, business and the federated revenue MCP.
`dev` adds filesystem, git, agents, quality and the federated development
MCP. `full` starts every declared split server.

The n8n adapter is read-only by default. Set
`N8N_MUTATIONS_ENABLED=true` only when workflow create/update/activation
should be available to MCP clients.

The runtime adapter never exposes arbitrary `shell_run`; it delegates only to
the public `cli_leion_engine` protocol and confines workspace calls under
`LEION_RUNTIME_ALLOWED_ROOTS`.

## FastMCP config

The repo includes `fastmcp.yml` with HTTP enabled. If you use the CLI directly, the effective server object is `main.py:server`.

## Cloudflared

Example ingress mapping:

```yml
ingress:
  - hostname: mcp.neomind.club
    service: http://localhost:3101
  - service: http_status:404
```

## Repository notes

- Do not commit `.env`.
- Do not commit `venv/`, `node_modules/`, or generated build output.
- `app/web/package-lock.json` is kept in version control, but `app/web/node_modules/` is ignored.

## Suggested first push

```powershell
git branch -M main
git add .
git commit -m "Initial commit"
git remote add origin <github-repo-url>
git push -u origin main
```
