from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from fastmcp import Client


class McpFederation:
    """Small explicit federation helper used by meta-MCP servers."""

    def __init__(self, backends: Dict[str, str]) -> None:
        self.backends = {
            str(name): str(url).rstrip("/")
            for name, url in backends.items()
            if str(name).strip() and str(url).strip()
        }

    def describe(self) -> Dict[str, str]:
        return dict(self.backends)

    def require_backend(self, backend: str) -> str:
        key = (backend or "").strip()
        if key not in self.backends:
            allowed = ", ".join(sorted(self.backends))
            raise ValueError(f"Unknown backend '{key}'. Allowed: {allowed}")
        return self.backends[key]

    async def list_tools(self, backend: str) -> Dict[str, Any]:
        url = self.require_backend(backend)
        client = Client(url)
        async with client:
            tools = await client.list_tools()
        return {
            "backend": backend,
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description or "",
                    "input_schema": tool.inputSchema or {},
                }
                for tool in tools
            ],
        }

    async def call(
        self,
        backend: str,
        tool: str,
        args: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = self.require_backend(backend)
        tool_name = (tool or "").strip()
        if not tool_name:
            raise ValueError("tool is required")

        client = Client(url)
        async with client:
            result = await client.call_tool(
                tool_name,
                args or {},
                raise_on_error=False,
            )

        return {
            "backend": backend,
            "tool": tool_name,
            "is_error": bool(getattr(result, "is_error", False)),
            "data": getattr(result, "data", None),
            "structured_content": getattr(result, "structured_content", None),
            "content": [
                getattr(item, "text", None) if hasattr(item, "text") else str(item)
                for item in (getattr(result, "content", None) or [])
            ],
            "meta": getattr(result, "meta", None),
        }
