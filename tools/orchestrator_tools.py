# D:/claude_code/leion_mcp_python/tools/orchestrator_tools.py
from __future__ import annotations

import json
from typing import Any, Dict

from fastmcp import FastMCP

from leion_engine.workflow_engine import OrchestratorEngine
from leion_engine.executor import ToolRunner


class MCPToolRunner(ToolRunner):
    """
    ToolRunner qui redirige run_tool -> ton moteur de tools MCP interne.

    Ici, on suppose que `mcp_server` a un mapping `tools` de la forme:
      mcp_server.tools[name] = python_callable
    """

    def __init__(self, mcp_server) -> None:
        self.mcp_server = mcp_server

    def run_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:
        if tool_name not in self.mcp_server.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        func = self.mcp_server.tools[tool_name]
        # Si tes tools sont déclarés en mode **kwargs:
        return func(**args)


# instance globale d'orchestrateur, initialisée une seule fois
_orchestrator: OrchestratorEngine | None = None


def init_orchestrator(mcp_server) -> None:
    """
    À appeler depuis register.py une fois que tous les tools sont enregistrés.
    """
    global _orchestrator
    runner = MCPToolRunner(mcp_server)
    _orchestrator = OrchestratorEngine(runner=runner, num_workers=2)


# ---------------------- LOGIQUE ORCHESTRATEUR ----------------------


def orchestrator_create_goal(goal: str) -> Dict[str, Any]:
    """
    Crée un nouvel objectif à long terme.
    """
    if _orchestrator is None:
        raise RuntimeError("Orchestrator not initialized")
    state = _orchestrator.api_create_goal(goal)
    return {
        "goal": state,
        "message": "Goal created.",
    }


def orchestrator_set_plan(goal_id: str, plan: Any) -> Dict[str, Any]:
    """
    Associe un plan structuré (généré par un LLM) à un goal existant.
    `plan` peut être un dict ou une string JSON.
    """
    if _orchestrator is None:
        raise RuntimeError("Orchestrator not initialized")

    if isinstance(plan, str):
        try:
            plan = json.loads(plan)
        except Exception as e:
            raise ValueError(f"Invalid JSON for plan: {e}")

    result = _orchestrator.api_set_plan(goal_id, plan)
    return {
        "result": result,
        "message": "Plan set.",
    }


def orchestrator_run_next_step(goal_id: str) -> Dict[str, Any]:
    """
    Enfile le prochain step du plan dans la job queue.
    (un worker en arrière-plan l’exécutera)
    """
    if _orchestrator is None:
        raise RuntimeError("Orchestrator not initialized")
    job = _orchestrator.api_run_next_step(goal_id)
    return {
        "job": job,
        "message": "Next step enqueued.",
    }


def orchestrator_get_goal_state(goal_id: str) -> Dict[str, Any]:
    """
    Retourne l’état du goal (progrès, dernier résultat, etc.)
    """
    if _orchestrator is None:
        raise RuntimeError("Orchestrator not initialized")
    return _orchestrator.api_get_goal_state(goal_id)


def orchestrator_list_goals() -> Dict[str, Any]:
    """
    Liste tous les goals actifs.
    """
    if _orchestrator is None:
        raise RuntimeError("Orchestrator not initialized")
    return {"goals": _orchestrator.api_list_goals()}


# ---------------------- ENREGISTREMENT FASTMCP ----------------------


def register_orchestrator_tools(server: FastMCP) -> None:
    """
    Enregistre les tools de l'orchestrateur dans le MCP server,
    puis initialise l'OrchestratorEngine avec ce server.

    Pattern identique à register_agent_tools (décorateur @server.tool()).
    """

    @server.tool()
    def orchestrator_create_goal_tool(goal: str) -> Dict[str, Any]:
        """Wrapper FastMCP -> logique orchestrator_create_goal."""
        return orchestrator_create_goal(goal)

    @server.tool()
    def orchestrator_set_plan_tool(goal_id: str, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Wrapper FastMCP -> logique orchestrator_set_plan."""
        return orchestrator_set_plan(goal_id, plan)

    @server.tool()
    def orchestrator_run_next_step_tool(goal_id: str) -> Dict[str, Any]:
        """Wrapper FastMCP -> logique orchestrator_run_next_step."""
        return orchestrator_run_next_step(goal_id)

    @server.tool()
    def orchestrator_get_goal_state_tool(goal_id: str) -> Dict[str, Any]:
        """Wrapper FastMCP -> logique orchestrator_get_goal_state."""
        return orchestrator_get_goal_state(goal_id)

    @server.tool()
    def orchestrator_list_goals_tool() -> Dict[str, Any]:
        """Wrapper FastMCP -> logique orchestrator_list_goals."""
        return orchestrator_list_goals()

    # Très important : on initialise l’orchestrateur APRÈS l’enregistrement
    # des tools, pour que MCPToolRunner voie tout le catalogue.
    init_orchestrator(server)
