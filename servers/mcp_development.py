import os
from typing import Any, Dict, Optional

from fastmcp import FastMCP

from utils.config import load_env
from utils.federation import McpFederation
from utils.logger import setup_logger


load_env()
setup_logger()

federation = McpFederation(
    {
        "fs": os.environ.get("MCP_FS_URL", "http://localhost:7001"),
        "git": os.environ.get("MCP_GIT_URL", "http://localhost:7002"),
        "workflows": os.environ.get("MCP_WORKFLOWS_URL", "http://localhost:7003"),
        "memory": os.environ.get("MCP_MEMORY_URL", "http://localhost:7004"),
        "agents": os.environ.get("MCP_AGENTS_URL", "http://localhost:7005"),
        "dev": os.environ.get("MCP_DEV_QUALITY_URL", "http://localhost:7007"),
        "runtime": os.environ.get("MCP_RUNTIME_URL", "http://localhost:7011"),
        "n8n": os.environ.get("MCP_N8N_URL", "http://localhost:7013"),
    }
)

server = FastMCP(
    name="leion-development",
    version="1.0.0",
)


@server.tool()
def development_backends() -> Dict[str, Any]:
    """List the only child MCP domains this development meta-server can reach."""
    return {"backends": federation.describe()}


@server.tool()
async def development_list_tools(domain: str) -> Dict[str, Any]:
    """List tools in one explicitly allowed development child domain."""
    return await federation.list_tools(domain)


@server.tool()
async def development_call(
    domain: str,
    tool: str,
    args: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Call one tool on an explicitly allowed development child MCP."""
    return await federation.call(domain, tool, args)


if __name__ == "__main__":
    server.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 7015)),
    )
