from typing import Any, Dict
from fastmcp import FastMCP

# Very lightweight agent plan helpers.
# The real reasoning and decision-making stays in the model;
# these tools just help persist and inspect plans.


def register_agent_tools(server: FastMCP):

    @server.tool()
    def agent_draft_plan(goal: str) -> Dict[str, Any]:
        """
        Draft a high-level execution plan for a given goal.

        NOTE: This does not execute anything; it just structures the goal
        into a list of steps that the model (ChatGPT) can then refine and
        execute step-by-step using other tools.
        """
        # The actual decomposition is done by the model, but we provide a schema
        # for consistency. Here we just return a skeleton that the model can fill.
        return {
            "goal": goal,
            "steps": [
                {"id": "step-1", "description": "First step to move toward the goal", "status": "pending"}
            ],
        }

    @server.tool()
    def agent_execute_plan(plan: Dict[str, Any]):
        """
        Store or echo back a structured plan.

        This tool does not autonomously execute other tools; instead it acts as
        a way to persist and inspect the current plan state. The model remains
        responsible for deciding which tools to call next.
        """
        # In a more advanced setup, this could write the plan to disk or a DB.
        # For now, we simply echo it back to allow the model to refine it.
        return {"received": plan}
