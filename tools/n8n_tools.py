from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastmcp import FastMCP


DEFAULT_TIMEOUT_SECONDS = 30
MAX_RESPONSE_BYTES = 2 * 1024 * 1024


def _error(code: str, message: str, **extra: Any) -> Dict[str, Any]:
    return {"ok": False, "error": {"code": code, "message": message}, **extra}


def _api_base() -> str:
    return os.getenv("N8N_API_BASE_URL", "http://localhost:5678/api/v1").rstrip("/")


def _api_key() -> str:
    return os.getenv("N8N_API_KEY", "").strip()


def _mutations_enabled() -> bool:
    return os.getenv("N8N_MUTATIONS_ENABLED", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _request(
    method: str,
    path: str,
    *,
    payload: Optional[Dict[str, Any]] = None,
    query: Optional[Dict[str, Any]] = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
) -> Dict[str, Any]:
    key = _api_key()
    if not key:
        return _error(
            "N8N_API_KEY_MISSING",
            "Set N8N_API_KEY before using the n8n MCP tools.",
        )

    base = _api_base()
    url = f"{base}/{path.lstrip('/')}"
    if query:
        clean_query = {
            key: value
            for key, value in query.items()
            if value is not None and value != ""
        }
        if clean_query:
            url = f"{url}?{urlencode(clean_query)}"

    body = None
    headers = {
        "Accept": "application/json",
        "X-N8N-API-KEY": key,
    }
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = Request(url, data=body, method=method.upper(), headers=headers)

    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if len(raw) > MAX_RESPONSE_BYTES:
                return _error(
                    "N8N_RESPONSE_TOO_LARGE",
                    f"n8n response exceeded {MAX_RESPONSE_BYTES} bytes.",
                )
            text = raw.decode("utf-8", errors="replace")
            if not text:
                data: Any = None
            else:
                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    return _error(
                        "N8N_RESPONSE_INVALID",
                        "n8n returned a non-JSON response.",
                        status=getattr(response, "status", None),
                    )
            return {
                "ok": True,
                "status": getattr(response, "status", 200),
                "data": data,
            }
    except HTTPError as exc:
        raw = exc.read(MAX_RESPONSE_BYTES).decode("utf-8", errors="replace")
        try:
            detail: Any = json.loads(raw) if raw else None
        except json.JSONDecodeError:
            detail = raw[:4096]
        return _error(
            "N8N_HTTP_ERROR",
            f"n8n API returned HTTP {exc.code}.",
            status=exc.code,
            detail=detail,
        )
    except URLError as exc:
        return _error("N8N_UNREACHABLE", f"Could not reach n8n: {exc.reason}")
    except TimeoutError:
        return _error("N8N_TIMEOUT", "n8n API request timed out.")
    except Exception as exc:
        return _error("N8N_REQUEST_FAILED", str(exc))


def _require_mutations() -> Optional[Dict[str, Any]]:
    if _mutations_enabled():
        return None
    return _error(
        "N8N_MUTATIONS_DISABLED",
        "Set N8N_MUTATIONS_ENABLED=true to create, update, activate, or deactivate workflows.",
    )


def register_n8n_tools(server: FastMCP) -> None:
    """Register a bounded adapter around n8n's public API.

    The surface intentionally excludes credentials and workflow deletion.
    Mutating operations are additionally gated by N8N_MUTATIONS_ENABLED.
    """

    @server.tool()
    def n8n_status() -> Dict[str, Any]:
        """Verify authenticated access to the local n8n public API."""
        result = _request("GET", "/workflows", query={"limit": 1, "excludePinnedData": "true"})
        if not result.get("ok"):
            return result
        data = result.get("data") or {}
        return {
            "ok": True,
            "reachable": True,
            "workflow_sample_count": len(data.get("data", [])) if isinstance(data, dict) else None,
            "mutations_enabled": _mutations_enabled(),
        }

    @server.tool()
    def n8n_list_workflows(
        active: Optional[bool] = None,
        name: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 50,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List workflows visible to the configured n8n API key."""
        if limit < 1 or limit > 250:
            return _error("N8N_LIMIT_INVALID", "limit must be between 1 and 250")
        return _request(
            "GET",
            "/workflows",
            query={
                "active": str(active).lower() if active is not None else None,
                "name": name,
                "projectId": project_id,
                "limit": limit,
                "cursor": cursor,
                "excludePinnedData": "true",
            },
        )

    @server.tool()
    def n8n_get_workflow(workflow_id: str) -> Dict[str, Any]:
        """Retrieve one workflow definition without pinned execution data."""
        value = (workflow_id or "").strip()
        if not value:
            return _error("N8N_WORKFLOW_ID_REQUIRED", "workflow_id is required")
        return _request(
            "GET",
            f"/workflows/{value}",
            query={"excludePinnedData": "true"},
        )

    @server.tool()
    def n8n_create_workflow(workflow: Dict[str, Any]) -> Dict[str, Any]:
        """Create a workflow through n8n's public API. Mutations must be enabled."""
        gate = _require_mutations()
        if gate:
            return gate
        if not isinstance(workflow, dict) or not workflow.get("name"):
            return _error(
                "N8N_WORKFLOW_INVALID",
                "workflow must be an object containing at least a name.",
            )
        return _request("POST", "/workflows", payload=workflow)

    @server.tool()
    def n8n_update_workflow(
        workflow_id: str,
        workflow: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Replace/update a workflow definition. Mutations must be enabled."""
        gate = _require_mutations()
        if gate:
            return gate
        value = (workflow_id or "").strip()
        if not value:
            return _error("N8N_WORKFLOW_ID_REQUIRED", "workflow_id is required")
        if not isinstance(workflow, dict):
            return _error("N8N_WORKFLOW_INVALID", "workflow must be an object")
        return _request("PUT", f"/workflows/{value}", payload=workflow)

    @server.tool()
    def n8n_activate_workflow(workflow_id: str) -> Dict[str, Any]:
        """Activate a workflow. Mutations must be enabled."""
        gate = _require_mutations()
        if gate:
            return gate
        value = (workflow_id or "").strip()
        if not value:
            return _error("N8N_WORKFLOW_ID_REQUIRED", "workflow_id is required")
        return _request("POST", f"/workflows/{value}/activate")

    @server.tool()
    def n8n_deactivate_workflow(workflow_id: str) -> Dict[str, Any]:
        """Deactivate a workflow. Mutations must be enabled."""
        gate = _require_mutations()
        if gate:
            return gate
        value = (workflow_id or "").strip()
        if not value:
            return _error("N8N_WORKFLOW_ID_REQUIRED", "workflow_id is required")
        return _request("POST", f"/workflows/{value}/deactivate")

    @server.tool()
    def n8n_list_executions(
        workflow_id: Optional[str] = None,
        status: Optional[str] = None,
        include_data: bool = False,
        limit: int = 50,
        cursor: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List workflow executions using n8n's public API."""
        if limit < 1 or limit > 250:
            return _error("N8N_LIMIT_INVALID", "limit must be between 1 and 250")
        if status and status not in {"error", "success", "waiting"}:
            return _error(
                "N8N_EXECUTION_STATUS_INVALID",
                "status must be error, success, or waiting",
            )
        return _request(
            "GET",
            "/executions",
            query={
                "workflowId": workflow_id,
                "status": status,
                "includeData": str(include_data).lower(),
                "limit": limit,
                "cursor": cursor,
            },
        )

    @server.tool()
    def n8n_get_execution(
        execution_id: str,
        include_data: bool = False,
    ) -> Dict[str, Any]:
        """Retrieve one n8n execution."""
        value = (execution_id or "").strip()
        if not value:
            return _error("N8N_EXECUTION_ID_REQUIRED", "execution_id is required")
        return _request(
            "GET",
            f"/executions/{value}",
            query={"includeData": str(include_data).lower()},
        )
