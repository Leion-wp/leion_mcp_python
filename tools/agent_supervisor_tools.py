from typing import Any, Dict

from fastmcp import FastMCP


def register_agent_supervisor_tools(server: FastMCP):

    @server.tool()
    def agent_draft_plan_advanced(goal: str, constraints: str = "", mode: str = "default"):
        """
        Propose un plan d'actions multi-étapes pour un objectif donné.

        Ce tool ne fait que décrire un plan que le modèle peut suivre.
        """
        return {
            "goal": goal,
            "constraints": constraints,
            "mode": mode,
            "steps": [
                "analyze_context",
                "design_solution",
                "implement_changes",
                "validate_results",
            ],
        }

    @server.tool()
    def agent_execute_step_plan(step: str, context: Dict[str, Any]):
        """
        Prépare un plan d'exécution pour une étape donnée.
        """
        return {
            "step": step,
            "context": context,
        }

    @server.tool()
    def agent_supervise_plan(plan: Dict[str, Any]):
        """
        Décrit comment superviser un plan d'agent.
        """
        return {
            "plan": plan,
            "checks": [
                "cohérence",
                "risques",
                "alignement_objectif",
            ],
        }
