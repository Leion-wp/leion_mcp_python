from __future__ import annotations

import asyncio
import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from fastmcp import Client, FastMCP
from utils.config import load_env
from utils.logger import setup_logger


load_env()
setup_logger()


# --------------------------------------------------------------------------------------
# Router configuration
# --------------------------------------------------------------------------------------
# In docker-compose, use service DNS names (mcp-fs, mcp-git, etc.).
# Locally, you can export MCP_*_URL env vars.
DEFAULT_BACKENDS = {
    "fs": os.environ.get("MCP_FS_URL", "http://localhost:7001"),
    "git": os.environ.get("MCP_GIT_URL", "http://localhost:7002"),
    "workflows": os.environ.get("MCP_WORKFLOWS_URL", "http://localhost:7003"),
    "memory": os.environ.get("MCP_MEMORY_URL", "http://localhost:7004"),
    "agents": os.environ.get("MCP_AGENTS_URL", "http://localhost:7005"),
    "integrations": os.environ.get("MCP_INTEGRATIONS_URL", "http://localhost:7006"),
    "dev": os.environ.get("MCP_DEV_QUALITY_URL", "http://localhost:7007"),
    "business": os.environ.get("MCP_BUSINESS_URL", "http://localhost:7008"),
    "ui": os.environ.get("MCP_UI_URL", "http://localhost:7009"),
    "cc": os.environ.get("MCP_CONTROL_CENTER_URL", "http://localhost:7010"),
    "wp": os.environ.get("MCP_WP_URL", "http://localhost:7012"),

}


# Keyword routing rules (fast, deterministic). 80% of traffic should land here.
# You can tune these over time.
ROUTING_RULES: List[Tuple[str, List[str]]] = [
    ("fs", [
        r"\bfile\b", r"\bfichier\b", r"\bfs_", r"\bread\b", r"\bwrite\b", r"\bpatch\b",
        r"\bdirectory\b", r"\bdossier\b", r"\bmkdir\b", r"\bdelete\b", r"\bsupprim",
        r"\bwatch\b", r"\bmonitor\b",
    ]),
    ("git", [
        r"\bgit\b", r"\bcommit\b", r"\bbranch\b", r"\bcheckout\b", r"\bdiff\b", r"\blog\b",
        r"\brepo\b", r"\brepository\b", r"\bprojet\b", r"\bproject\b", r"\bscan\b",
    ]),
    ("workflows", [
        r"\bworkflow\b", r"\bflowise\b", r"\bchatflow\b", r"\bautobuilder\b", r"\bdefinition\b",
        r"\brun workflow\b", r"\bexecute workflow\b", r"\bplan workflow\b",
    ]),
    ("memory", [
        r"\bmemory\b", r"\bmemoire\b", r"\bvector\b", r"\bembedding\b", r"\bprofile\b",
        r"\brecall\b", r"\bnamespace\b",
    ]),
    ("agents", [
        r"\bagent\b", r"\bsupervis\b", r"\borchestr\b", r"\bplan\b", r"\bnext step\b",
    ]),
    ("wp", [
        r"wordpress", r"wp", r"post", r"page", r"media",
        r"plugin", r"publish", r"draft",
    ]),
    ("integrations", [
        r"\bcomposio\b", r"\bslack\b", r"\bgmail\b", r"\bnotion\b", r"\bgithub issue\b",
        r"\bconnect\b", r"\bintegration\b", r"\bemail\b", r"\bsms\b",
    ]),
    ("dev", [
        r"\brefactor\b", r"\bdependencies\b", r"\bdependenc\b", r"\btest\b", r"\bobservability\b",
        r"\blint\b", r"\bci\b",
    ]),
    ("business", [
        r"\bbusiness\b", r"\bniche\b", r"\boffer\b", r"\bassets\b", r"\bbrand\b", r"\blogo\b",
        r"\blaunch\b", r"\bmarket\b",
    ]),
    ("ui", [
        r"\bui\b", r"\breact\b", r"\bcomponent\b", r"\blayout\b", r"\bpage\b",
    ]),
    ("cc", [
        r"\bdashboard\b", r"\bcontrol center\b", r"\bwidget\b",
    ]),
]


@dataclass
class ToolInfo:
    name: str
    description: str
    input_schema: dict


server = FastMCP(
    name="leion-router",
    version="1.0.0",
)


# --------------------------------------------------------------------------------------
# Internal helpers
# --------------------------------------------------------------------------------------

def _normalize(text: str) -> str:
    return (text or "").strip().lower()


def _pick_backend(text: str, preferred: Optional[str] = None) -> str:
    if preferred and preferred in DEFAULT_BACKENDS:
        return preferred

    t = _normalize(text)
    for backend, patterns in ROUTING_RULES:
        for pat in patterns:
            if re.search(pat, t, flags=re.IGNORECASE):
                return backend

    # Sensible default: most interactive tasks end up being filesystem/project oriented
    return "fs"


async def _list_tools(backend: str) -> List[ToolInfo]:
    url = DEFAULT_BACKENDS.get(backend)
    if not url:
        raise ValueError(f"Unknown backend: {backend}")

    client = Client(url)
    async with client:
        tools = await client.list_tools()

    out: List[ToolInfo] = []
    for t in tools:
        # t is mcp.types.Tool
        out.append(
            ToolInfo(
                name=t.name,
                description=(t.description or ""),
                input_schema=(t.inputSchema or {}),
            )
        )
    return out


async def _call_tool(backend: str, tool: str, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = DEFAULT_BACKENDS.get(backend)
    if not url:
        raise ValueError(f"Unknown backend: {backend}")

    client = Client(url)
    async with client:
        result = await client.call_tool(tool, args or {}, raise_on_error=False)

    # FastMCP returns CallToolResult dataclass
    return {
        "backend": backend,
        "tool": tool,
        "is_error": bool(getattr(result, "is_error", False)),
        "data": getattr(result, "data", None),
        "structured_content": getattr(result, "structured_content", None),
        "content": [
            getattr(c, "text", None) if hasattr(c, "text") else str(c)
            for c in (getattr(result, "content", None) or [])
        ],
        "meta": getattr(result, "meta", None),
    }


def _match_tool_by_name(tools: List[ToolInfo], tool_name: str) -> Optional[ToolInfo]:
    for t in tools:
        if t.name == tool_name:
            return t
    return None


# --------------------------------------------------------------------------------------
# Public router tools (keep surface small)
# --------------------------------------------------------------------------------------

@server.tool()
def router_backends() -> Dict[str, Any]:
    """List configured MCP backends and their base URLs."""
    return {"backends": DEFAULT_BACKENDS}


@server.tool()
async def router_suggest_backend(query: str, preferred: Optional[str] = None) -> Dict[str, Any]:
    """Suggest which backend should handle a user query (fast rules)."""
    backend = _pick_backend(query, preferred=preferred)
    return {
        "suggested_backend": backend,
        "backend_url": DEFAULT_BACKENDS.get(backend),
    }


@server.tool()
async def router_list_tools(query: str, preferred: Optional[str] = None) -> Dict[str, Any]:
    """List tools for the best backend for this query (limits exposure to a single domain)."""
    backend = _pick_backend(query, preferred=preferred)
    tools = await _list_tools(backend)
    return {
        "backend": backend,
        "backend_url": DEFAULT_BACKENDS.get(backend),
        "tools": [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
            }
            for t in tools
        ],
    }


@server.tool()
async def router_call(
    query: str,
    tool: str,
    args: Optional[Dict[str, Any]] = None,
    preferred: Optional[str] = None,
) -> Dict[str, Any]:
    """Route and call a tool on the selected backend."""
    backend = _pick_backend(query, preferred=preferred)
    return await _call_tool(backend, tool, args=args)


@server.tool()
async def router_call_auto(
    query: str,
    args: Optional[Dict[str, Any]] = None,
    preferred: Optional[str] = None,
) -> Dict[str, Any]:
    """Route a query to the right backend and try to pick the most likely tool by name heuristics.

    This keeps the router light: no LLM call; only name matching.
    For best results, pass a query that includes the intended tool name (e.g., "fs_read_file").
    """
    backend = _pick_backend(query, preferred=preferred)
    tools = await _list_tools(backend)

    # Heuristic: if query contains an exact tool name, use it
    q = _normalize(query)
    for t in tools:
        if t.name.lower() in q:
            return await _call_tool(backend, t.name, args=args)

    # Heuristic: common verbs
    verb_map = [
        (r"\b(list|ls|directory|dossier)\b", "list"),
        (r"\b(read|open|lire)\b", "read"),
        (r"\b(write|save|ecrire|écrire)\b", "write"),
        (r"\b(delete|remove|supprim)\b", "delete"),
        (r"\b(patch)\b", "patch"),
        (r"\b(watch|monitor)\b", "watch"),
    ]

    chosen: Optional[str] = None
    for pat, verb in verb_map:
        if re.search(pat, q, flags=re.IGNORECASE):
            # choose the first tool that contains verb
            for t in tools:
                if verb in t.name.lower():
                    chosen = t.name
                    break
        if chosen:
            break

    if not chosen:
        return {
            "backend": backend,
            "error": "Could not auto-pick a tool. Use router_list_tools then router_call.",
            "backend_url": DEFAULT_BACKENDS.get(backend),
        }

    return await _call_tool(backend, chosen, args=args)


# Allow running this file as a script for quick manual tests

if __name__ == "__main__":
    import os
    server.run(
        transport="http",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 7000)),
    )
