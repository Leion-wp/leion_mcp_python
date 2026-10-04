import json
from typing import Any, Dict

from fastmcp import FastMCP

from .local_workflow_runner import definitions_root, validate_definition, workflow_path


def _ensure_workflows_dir():
    root = definitions_root()
    root.mkdir(parents=True, exist_ok=True)
    return root


def register_workflow_builder_tools(server: FastMCP):

    @server.tool()
    def workflow_save_definition(workflow_id: str, definition: Dict[str, Any]):
        """
        Save a workflow JSON definition into the Leion Auto-Builder definitions folder.

        - workflow_id: filename without .json
        - definition: full workflow JSON (nodes, connections, metadata, etc.)
        """
        validation = validate_definition(definition)
        if not validation["ok"]:
            return validation
        try:
            root = _ensure_workflows_dir()
            path = workflow_path(workflow_id)
            temporary = path.with_suffix(".tmp")
            temporary.write_text(json.dumps(definition, indent=2, ensure_ascii=False, sort_keys=True), encoding="utf-8")
            temporary.replace(path)
            return {"ok": True, "path": str(path)}
        except (OSError, ValueError) as exc:
            return {"ok": False, "error": str(exc)}

    @server.tool()
    def workflow_list_definitions():
        """
        List workflow definition files available in the definitions folder.
        """
        root = definitions_root()
        items: list[dict[str, Any]] = []
        if not root.exists():
            return {"root": str(root), "workflows": items}
        for p in root.glob('*.json'):
            items.append({"id": p.stem, "path": str(p)})
        return {"root": str(root), "workflows": items}

    @server.tool()
    def workflow_read_definition(workflow_id: str):
        """
        Read a workflow JSON definition by ID.
        """
        try:
            path = workflow_path(workflow_id)
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}
        if not path.exists():
            return {"ok": False, "error": "workflow definition not found", "path": str(path)}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            validation = validate_definition(data)
            if not validation["ok"]:
                return {**validation, "path": str(path)}
            return {"ok": True, "path": str(path), "definition": data}
        except (OSError, json.JSONDecodeError) as exc:
            return {"ok": False, "error": str(exc), "path": str(path)}
