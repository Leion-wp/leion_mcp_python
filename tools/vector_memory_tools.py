import os
from typing import Any, Dict, List, Optional

import requests
from fastmcp import FastMCP

# Simple HTTP-based vector store client.
# You can back this with anything (Chroma, LanceDB, pgvector, etc.) via a small HTTP service.
# Configure the base URL via VECTOR_STORE_BASE_URL.

VECTOR_STORE_BASE_URL = os.getenv("VECTOR_STORE_BASE_URL", "http://localhost:8085")


def _post(path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{VECTOR_STORE_BASE_URL}{path}"
    try:
        resp = requests.post(url, json=payload, timeout=60)
        resp.raise_for_status()
        return {"ok": True, "url": url, "data": resp.json()}
    except Exception as e:
        return {"ok": False, "error": str(e), "url": url, "payload": payload}


def register_vector_memory_tools(server: FastMCP):

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
        payload = {"namespace": namespace, "items": items}
        return _post("/add", payload)

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
        payload: Dict[str, Any] = {"namespace": namespace, "query": query, "top_k": top_k}
        if filter is not None:
            payload["filter"] = filter
        return _post("/query", payload)

    @server.tool()
    def vector_store_delete(namespace: str, ids: List[str]):
        """
        Delete items from the vector store by ID.
        """
        payload = {"namespace": namespace, "ids": ids}
        return _post("/delete", payload)
