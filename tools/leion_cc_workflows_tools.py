from typing import Any, Dict
from fastmcp import FastMCP

from .leion_cc_common_tools import make_output


async def _fake_workflow_list_definitions() -> list[Dict[str, Any]]:
    # TODO: remplacer par workflow_list réel
    return [
        {
            "id": "daily_sync",
            "name": "Daily sync CRM",
            "tags": ["business", "crm"],
            "description": "Sync CRM every morning",
        },
        {
            "id": "nightly_backup",
            "name": "Nightly backup",
            "tags": ["infra"],
            "description": "Backup all relevant data nightly",
        },
    ]


def register_leion_cc_workflows_tools(server: FastMCP):

    @server.tool()
    async def leion_cc_workflows(include_definitions: bool = False) -> Dict[str, Any]:
        """
        Fournit la liste des workflows pour l'onglet Workflows du Control Center.
        """
        workflows = await _fake_workflow_list_definitions()

        structured = {
            "type": "leion_workflows",
            "workflows": [
                {
                    "id": wf["id"],
                    "name": wf.get("name", wf["id"]),
                    "tags": wf.get("tags", []),
                    "description": wf.get("description", ""),
                    "has_required_inputs": True,
                }
                for wf in workflows
            ],
        }

        return make_output(
            "Liste des workflows Leion",
            structured,
            with_widget=False,
        )
