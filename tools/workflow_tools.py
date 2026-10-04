import os
from fastmcp import FastMCP

# The portable embedded runner is the default. The legacy HTTP engine remains
# available only when explicitly selected in the environment.
BASE_URL = os.getenv("LEION_WORKFLOW_API", "http://localhost:3100")


def _use_local_runner() -> bool:
    return os.getenv("WORKFLOW_RUNNER", "local").strip().lower() in ("local", "python", "embedded")


def _remote_request(method: str, url: str, *, payload: dict | None = None, timeout: int) -> dict:
    try:
        import requests
    except ModuleNotFoundError:
        return {
            "ok": False,
            "error": "WORKFLOW_REMOTE_DEPENDENCY_MISSING",
            "message": "Install the declared requests dependency to use WORKFLOW_RUNNER=remote.",
            "endpoint": url,
        }

    try:
        response = requests.request(method, url, json=payload, timeout=timeout)
        response.raise_for_status()
        return {"ok": True, "data": response.json(), "endpoint": url}
    except Exception as exc:
        return {"ok": False, "error": str(exc), "endpoint": url, "payload": payload}


def register_workflow_tools(server: FastMCP):

    @server.tool()
    def workflow_list():
        """List available workflows.

        - Default / WORKFLOW_RUNNER=local: list validated local JSON definitions.
        - WORKFLOW_RUNNER=remote: proxy to the legacy workflow engine /workflows.
        """
        if _use_local_runner():
            from tools.local_workflow_runner import list_definitions

            return list_definitions()

        url = f"{BASE_URL}/workflows"
        return _remote_request("GET", url, timeout=10)

    @server.tool()
    def workflow_run(workflow_id: str, inputs: dict | None = None):
        """Execute a workflow by ID.

        - Default / WORKFLOW_RUNNER=local: validate and run an embedded workflow.
        - WORKFLOW_RUNNER=remote: POST to the legacy engine /workflows/{workflow_id}.
        """
        payload = inputs or {}

        if _use_local_runner():
            from tools.local_workflow_runner import read_definition, run_workflow

            read_res, _ = read_definition(workflow_id)
            if not read_res.get("ok"):
                return read_res
            definition = read_res.get("definition") or {}
            try:
                return run_workflow(definition, payload)
            except Exception as exc:
                return {"ok": False, "error": str(exc), "workflow_id": workflow_id}

        url = f"{BASE_URL}/workflows/{workflow_id}"
        return _remote_request("POST", url, payload=payload, timeout=60)
