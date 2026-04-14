import os
from typing import Any, Dict
import requests
from fastmcp import FastMCP

COMPOSIO_BASE = os.getenv("COMPOSIO_BASE_URL", "https://api.composio.dev")
COMPOSIO_KEY = os.getenv("COMPOSIO_API_KEY")


def _auth_headers() -> Dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if COMPOSIO_KEY:
        headers["Authorization"] = f"Bearer {COMPOSIO_KEY}"
    return headers


# 👉 RENDUE GLOBALE — disponible pour l'import
def composio_run_action(app: str, action: str, payload: Dict[str, Any]):
    if not COMPOSIO_KEY:
        return {
            "ok": False,
            "error": "COMPOSIO_API_KEY manquante dans l'environnement",
        }

    url = f"{COMPOSIO_BASE.rstrip('/')}/v1/actions/run"
    body = {"app": app, "action": action, "params": payload}

    try:
        resp = requests.post(url, json=body, headers=_auth_headers(), timeout=60)
        return {
            "ok": resp.ok,
            "status_code": resp.status_code,
            "data": resp.json()
            if resp.headers.get("content-type", "").startswith("application/json")
            else resp.text,
        }
    except Exception as e:
        return {"ok": False, "error": str(e)}


def register_composio_tools(server: FastMCP):

    @server.tool()
    def composio_status():
        return {
            "base_url": COMPOSIO_BASE,
            "has_api_key": bool(COMPOSIO_KEY),
        }

    @server.tool()
    def composio_run_action_tool(app: str, action: str, payload: Dict[str, Any]):
        # réutilise la fonction globale
        return composio_run_action(app, action, payload)
