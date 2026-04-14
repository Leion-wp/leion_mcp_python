from typing import Any, Dict
from fastmcp import FastMCP

from .leion_cc_common_tools import make_output


async def _fake_workflow_run(
    workflow_id: str,
    inputs: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    # TODO: remplacer par le vrai moteur de workflow (workflow_run)
    return {
        "run_id": "run_fake_123",
        "status": "success",
        "output": {
            "summary": f"Workflow {workflow_id} executed (mock).",
            "inputs": inputs or {},
        },
    }


def register_leion_cc_run_workflow_tools(server: FastMCP):

    @server.tool()
    async def leion_cc_run_workflow(
        workflow_id: str,
        inputs: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """
        Point d'entrée standard pour lancer un workflow depuis le widget.
        """
        result = await _fake_workflow_run(workflow_id, inputs or {})

        structured = {
            "type": "leion_workflow_run_result",
            "workflow_id": workflow_id,
            "run_id": result["run_id"],
            "status": result["status"],
            "output": result.get("output", {}),
        }

        return make_output(
            f"Résultat exécution workflow {workflow_id}",
            structured,
            with_widget=False,
        )
