import os
from typing import Any, Dict, Optional

import requests
from fastmcp import FastMCP


# Base URLs for external orchestrators (override with env vars)
FLOWISE_BASE_URL = os.getenv("FLOWISE_BASE_URL", "http://localhost:3000")
RUBE_BASE_URL = os.getenv("RUBE_BASE_URL", "http://localhost:3005")
ZAPIER_HOOK_BASE_URL = os.getenv("ZAPIER_HOOK_BASE_URL")  # optional


def register_flowise_rube_zapier_tools(server: FastMCP):

    @server.tool()
    def flowise_run(chatflow_id: str, payload: Dict[str, Any]):
        """
        Execute a Flowise chatflow by ID with a JSON payload.

        - chatflow_id: the Flowise flow ID
        - payload: dict sent as JSON body to the Flowise API
        """
        url = f"{FLOWISE_BASE_URL}/api/v1/prediction/{chatflow_id}"
        try:
            resp = requests.post(url, json=payload, timeout=120)
            resp.raise_for_status()
            return {"ok": True, "url": url, "status_code": resp.status_code, "data": resp.json()}
        except Exception as e:
            return {"ok": False, "error": str(e), "url": url, "payload": payload}

    @server.tool()
    def rube_trigger(endpoint: str, payload: Dict[str, Any]):
        """
        Call a Rube HTTP endpoint with a JSON payload.

        - endpoint: relative path like \"/api/run-workflow\"
        - payload: JSON body
        """
        endpoint = endpoint.lstrip('/')
        url = f"{RUBE_BASE_URL}/{endpoint}"
        try:
            resp = requests.post(url, json=payload, timeout=120)
            resp.raise_for_status()
            # try json, fallback to text
            try:
                data = resp.json()
            except Exception:
                data = {"text": resp.text}
            return {"ok": True, "url": url, "status_code": resp.status_code, "data": data}
        except Exception as e:
            return {"ok": False, "error": str(e), "url": url, "payload": payload}

    @server.tool()
    def zapier_hook(hook_path: str, payload: Dict[str, Any]):
        """
        Trigger a Zapier catch hook or webhook.

        - hook_path: full URL or path relative to ZAPIER_HOOK_BASE_URL
        - payload: JSON body
        """
        if hook_path.startswith("http://") or hook_path.startswith("https://"):
            url = hook_path
        else:
            if not ZAPIER_HOOK_BASE_URL:
                return {"ok": False, "error": "ZAPIER_HOOK_BASE_URL not configured"}
            hook_path = hook_path.lstrip('/')
            url = f"{ZAPIER_HOOK_BASE_URL}/{hook_path}"

        try:
            resp = requests.post(url, json=payload, timeout=60)
            resp.raise_for_status()
            try:
                data = resp.json()
            except Exception:
                data = {"text": resp.text}
            return {"ok": True, "url": url, "status_code": resp.status_code, "data": data}
        except Exception as e:
            return {"ok": False, "error": str(e), "url": url, "payload": payload}
