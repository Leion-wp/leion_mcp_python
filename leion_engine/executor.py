from __future__ import annotations

from typing import Any, Dict, Protocol

from .parser import Plan, Step


class ToolRunner(Protocol):
    """Abstraction mince au-dessus de ton système de tools MCP.

    Ça permet de brancher ici soit un appel direct Python, soit un client HTTP,
    soit un wrapper autour de ton existing `leion-os` tool executor.
    """

    def run_tool(self, tool_name: str, args: Dict[str, Any]) -> Any:  # pragma: no cover - interface
        ...


class PlanExecutor:
    def __init__(self, runner: ToolRunner) -> None:
        self.runner = runner

    def execute_step(self, step: Step) -> Dict[str, Any]:
        """Execute un step individuel.

        Pour l'instant : un seul appel de tool optionnel.
        Plus tard : on pourra supporter les branches, les parallélisations, etc.
        """
        result: Dict[str, Any] = {
            "step_index": step.index,
            "description": step.description,
        }

        if step.tool_name:
            output = self.runner.run_tool(step.tool_name, step.tool_args or {})
            result["tool_name"] = step.tool_name
            result["tool_args"] = step.tool_args or {}
            result["tool_output"] = output
        return result

    def execute_plan(self, plan: Plan) -> Dict[str, Any]:
        """Execute séquentiellement toutes les étapes d'un plan.

        Cette fonction peut être utilisée par un outil "orchestrator_run"
        qui, lui, sera piloté par l'IA.
        """
        steps_results = []
        for step in plan.steps:
            steps_results.append(self.execute_step(step))

        return {
            "goal_id": plan.goal_id,
            "goal": plan.goal,
            "steps": steps_results,
        }
