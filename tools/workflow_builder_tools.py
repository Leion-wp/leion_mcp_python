import json
from pathlib import Path
from typing import Any, Dict

from fastmcp import FastMCP


WORKFLOWS_DEFINITIONS_DIR = Path("D:/claude_code/leion-autobuilder/workflows/definitions")


def _ensure_workflows_dir() -> Path:
    WORKFLOWS_DEFINITIONS_DIR.mkdir(parents=True, exist_ok=True)
    return WORKFLOWS_DEFINITIONS_DIR


def register_workflow_builder_tools(server: FastMCP):

    @server.tool()
    def workflow_save_definition(workflow_id: str, definition: Dict[str, Any]):
        """
        Save a workflow JSON definition into the Leion Auto-Builder definitions folder.

        - workflow_id: filename without .json
        - definition: full workflow JSON (nodes, connections, metadata, etc.)
        """
        root = _ensure_workflows_dir()
        path = root / f"{workflow_id}.json"
        try:
            path.write_text(json.dumps(definition, indent=2, ensure_ascii=False), encoding="utf-8")
            return {"ok": True, "path": str(path)}
        except Exception as e:
            return {"ok": False, "error": str(e), "path": str(path)}

    @server.tool()
    def workflow_list_definitions():
        """
        List workflow definition files available in the definitions folder.
        """
        root = _ensure_workflows_dir()
        items: list[dict[str, Any]] = []
        for p in root.glob('*.json'):
            items.append({"id": p.stem, "path": str(p)})
        return {"root": str(root), "workflows": items}

    @server.tool()
    def workflow_read_definition(workflow_id: str):
        """
        Read a workflow JSON definition by ID.
        """
        root = _ensure_workflows_dir()
        path = root / f"{workflow_id}.json"
        if not path.exists():
            return {"ok": False, "error": "workflow definition not found", "path": str(path)}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return {"ok": True, "path": str(path), "definition": data}
        except Exception as e:
            return {"ok": False, "error": str(e), "path": str(path)}
