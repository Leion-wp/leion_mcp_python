from typing import Any, Dict, Literal
from fastmcp import FastMCP

from .leion_cc_common_tools import make_output

Mode = Literal["draft_plan", "execute_step"]


async def _fake_agent_draft_plan(goal: str) -> Dict[str, Any]:
    # TODO: brancher ton vrai agent_draft_plan_advanced
    return {
        "plan_id": "plan_fake_001",
        "steps": [
            {"id": "1", "title": "Analyser le repo", "status": "pending"},
            {"id": "2", "title": "Créer les tools backend", "status": "pending"},
            {"id": "3", "title": "Mettre en place le widget", "status": "pending"},
        ],
    }


async def _fake_agent_execute_step(
    plan: Dict[str, Any],
    step_id: str,
) -> Dict[str, Any]:
    # TODO: brancher ton vrai agent_execute_plan
    updated_steps = []
    for s in plan.get("steps", []):
        if s.get("id") == step_id:
            updated_steps.append({**s, "status": "done"})
        else:
            updated_steps.append(s)

    return {
        "plan_id": plan.get("plan_id", "plan_fake_001"),
        "steps": updated_steps,
        "executed_step_id": step_id,
    }


def register_leion_cc_agents_tools(server: FastMCP):

    @server.tool()
    async def leion_cc_agents(
        mode: Mode,
        goal: str | None = None,
        plan: Dict[str, Any] | None = None,
        step_id: str | None = None,
    ) -> Dict[str, Any]:
        """
        Interface widget pour les agents :
        - mode = draft_plan : proposer un plan structuré à partir d'un goal
        - mode = execute_step : exécuter un step du plan
        """
        if mode == "draft_plan":
            if not goal:
                raise ValueError("goal is required in draft_plan mode")
            plan_data = await _fake_agent_draft_plan(goal)
            structured = {
                "type": "leion_agent_plan",
                "plan": plan_data,
            }
            title = f"Plan agent pour: {goal}"
        else:
            if not plan or not step_id:
                raise ValueError("plan and step_id are required in execute_step mode")
            exec_result = await _fake_agent_execute_step(plan, step_id)
            structured = {
                "type": "leion_agent_plan",
                "plan": exec_result,
            }
            title = f"Plan mis à jour, step {step_id} exécuté"

        return make_output(
            title,
            structured,
            with_widget=False,
        )
