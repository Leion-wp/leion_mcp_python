import os
from typing import Any, Dict, List, Optional

import requests
from fastmcp import FastMCP

from . import local_memory_store

# The default is a deterministic local namespace store. Opt in to an HTTP
# vector store only when it is explicitly configured, so starting the memory
# backend never relies on an undeclared service at localhost:8085.
MEMORY_BACKEND = os.getenv("MEMORY_BACKEND", "local").strip().lower()
VECTOR_STORE_BASE_URL = os.getenv("VECTOR_STORE_BASE_URL", "").strip().rstrip("/")


def _post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    if MEMORY_BACKEND != "http":
        return {
            "ok": False,
            "error": "MEMORY_BACKEND is local; use the local namespace implementation.",
        }
    if not VECTOR_STORE_BASE_URL:
        return {
            "ok": False,
            "error": "MEMORY_BACKEND=http requires VECTOR_STORE_BASE_URL.",
        }
    url = f"{VECTOR_STORE_BASE_URL}{path}"
    try:
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        return {"ok": True, "url": url, "data": resp.json()}
    except Exception as e:
        return {"ok": False, "error": str(e), "url": url, "payload": payload}


def register_vector_memory_tools(server: FastMCP):

    @server.tool()
    def memory_backend_status() -> Dict[str, Any]:
        """Describe the memory backend selected for this MCP process."""
        if MEMORY_BACKEND == "http":
            return {
                "ok": bool(VECTOR_STORE_BASE_URL),
                "backend": "http-vector-store",
                "url": VECTOR_STORE_BASE_URL or None,
            }
        return {
            "ok": MEMORY_BACKEND == "local",
            "backend": "local-json",
            "workspace_root": str(local_memory_store.workspace_root()),
            "note": "Lexical matching is deterministic; configure MEMORY_BACKEND=http for an external vector service.",
        }

    @server.tool()
    def vector_store_add(
        namespace: str,
        items: List[Dict[str, Any]],
    ):
        """
        Add one or more items to the vector store.

        Each item should look like:
        {
          "id": "unique-id",
          "text": "content to embed",
          "metadata": { ... optional ... }
        }
        """
        if MEMORY_BACKEND == "local":
            return local_memory_store.add(namespace, items)
        return _post("/add", {"namespace": namespace, "items": items})

    @server.tool()
    def vector_store_query(
        namespace: str,
        query: str,
        top_k: int = 5,
        filter: Optional[Dict[str, Any]] = None,
    ):
        """
        Query the vector store for the most relevant items.
        """
        if MEMORY_BACKEND == "local":
            return local_memory_store.query(namespace, query, top_k, filter)
        payload: Dict[str, Any] = {"namespace": namespace, "query": query, "top_k": top_k}
        if filter is not None:
            payload["filter"] = filter
        return _post("/query", payload)

    @server.tool()
    def vector_store_delete(namespace: str, ids: List[str]):
        """
        Delete items from the vector store by ID.
        """
        if MEMORY_BACKEND == "local":
            return local_memory_store.delete(namespace, ids)
        return _post("/delete", {"namespace": namespace, "ids": ids})
