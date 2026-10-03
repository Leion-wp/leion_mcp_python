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
        "business": os.environ.get("MCP_BUSINESS_URL", "http://localhost:7008"),
        "integrations": os.environ.get("MCP_INTEGRATIONS_URL", "http://localhost:7006"),
        "workflows": os.environ.get("MCP_WORKFLOWS_URL", "http://localhost:7003"),
        "memory": os.environ.get("MCP_MEMORY_URL", "http://localhost:7004"),
        "runtime": os.environ.get("MCP_RUNTIME_URL", "http://localhost:7011"),
        "n8n": os.environ.get("MCP_N8N_URL", "http://localhost:7013"),
    }
)

server = FastMCP(
    name="leion-revenue",
    version="1.0.0",
)


@server.tool()
def revenue_backends() -> Dict[str, Any]:
    """List the only child MCP domains this revenue meta-server can reach."""
    return {"backends": federation.describe()}


@server.tool()
async def revenue_list_tools(domain: str) -> Dict[str, Any]:
    """List tools in one explicitly allowed revenue child domain."""
    return await federation.list_tools(domain)


@server.tool()
async def revenue_call(
    domain: str,
    tool: str,
    args: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Call one tool on an explicitly allowed revenue child MCP."""
    return await federation.call(domain, tool, args)


if __name__ == "__main__":
    server.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 7014)),
    )
