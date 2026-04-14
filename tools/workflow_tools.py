import os
import requests
from fastmcp import FastMCP

# External workflow engine (legacy monolith)
BASE_URL = os.getenv("LEION_WORKFLOW_API", "http://localhost:3100")

# Local runner toggle (new path)
USE_LOCAL_RUNNER = os.getenv("WORKFLOW_RUNNER", "remote").lower() in ("local", "python", "embedded")

if USE_LOCAL_RUNNER:
    from tools.local_workflow_runner import list_definitions as _local_list_defs
    from tools.local_workflow_runner import read_definition as _local_read_def
    from tools.local_workflow_runner import run_workflow as _local_run_workflow


def register_workflow_tools(server: FastMCP):

    @server.tool()
    def workflow_list():
        """List available workflows.

        - If WORKFLOW_RUNNER=local: list JSON definitions from WORKFLOW_DEFINITIONS_DIR (or default).
        - Else: proxy to the legacy workflow engine /workflows.
        """
        if USE_LOCAL_RUNNER:
            return _local_list_defs()

        url = f"{BASE_URL}/workflows"
        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e), "endpoint": url}

    @server.tool()
    def workflow_run(workflow_id: str, inputs: dict | None = None):
        """Execute a workflow by ID.

        - If WORKFLOW_RUNNER=local: load the definition and run it in-process (minimal runner).
        - Else: POST to the legacy engine /workflows/{workflow_id}.
        """
        payload = inputs or {}

        if USE_LOCAL_RUNNER:
            read_res, _ = _local_read_def(workflow_id)
            if not read_res.get("ok"):
                return read_res
            definition = read_res.get("definition") or {}
            try:
                return _local_run_workflow(definition, payload)
            except Exception as e:
                return {"ok": False, "error": str(e), "workflow_id": workflow_id}

        url = f"{BASE_URL}/workflows/{workflow_id}"
        try:
            resp = requests.post(url, json=payload, timeout=60)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            return {"error": str(e), "endpoint": url, "payload": payload}
