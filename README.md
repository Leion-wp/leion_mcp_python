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
