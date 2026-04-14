from typing import Any, Dict
from fastmcp import FastMCP

from .leion_cc_common_tools import make_output


async def _fake_os_health_check() -> Dict[str, Any]:
    # TODO: remplacer par ton vrai call
    return {
        "flowise": "ok",
        "composio": "ok",
        "vector_store": "degraded",
        "llm_providers": [
            {"name": "openrouter", "status": "ok"},
            {"name": "groq", "status": "ok"},
            {"name": "ollama", "status": "fallback"},
        ],
    }


async def _fake_workflow_list_definitions() -> list[Dict[str, Any]]:
    # TODO: remplacer
    return [
        {"id": "daily_sync", "name": "Daily sync CRM"},
        {"id": "nightly_backup", "name": "Nightly backup"},
    ]


async def _fake_get_default_project_summaries() -> list[Dict[str, Any]]:
    # TODO: remplacer
    return [
        {
            "id": "leion-autobuilder",
            "summary": "Autobuilder pipeline.",
            "status": "active",
        },
        {
            "id": "leion_mcp_python",
            "summary": "MCP server & tools.",
            "status": "active",
        },
    ]


async def _fake_os_list_recent_events(limit: int = 20) -> list[Dict[str, Any]]:
    # TODO: remplacer
    return [
        {
            "ts": "2025-11-26T10:23:00Z",
            "type": "workflow_run",
            "message": "workflow 'daily_sync' ran successfully",
        }
    ]


def register_leion_cc_dashboard_tools(server: FastMCP):

    @server.tool()
    async def leion_cc_dashboard() -> Dict[str, Any]:
        """Retourne l'état global de Leion OS pour le widget dashboard."""
        # Version mockée v0 pour ne rien casser
        health = await _fake_os_health_check()
        workflows = await _fake_workflow_list_definitions()
        projects = await _fake_get_default_project_summaries()
        recent_events = await _fake_os_list_recent_events(limit=20)

        structured_content = {
            "type": "leion_dashboard",
            "health": health,
            "projects": projects,
            "workflows": {"count": len(workflows)},
            "recent_events": recent_events,
        }

        return make_output(
            "Leion Control Center - Dashboard",
            structured_content,
            with_widget=True,
        )
