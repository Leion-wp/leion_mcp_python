"""Deterministic, file-backed namespace storage for the memory MCP.

This is deliberately a small bounded store, not a conversational-memory
system and not a substitute for the separate memory_factory repository. It
keeps the existing namespace contract working locally until a real
memory_factory adapter is available.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
import threading
from functools import wraps
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


_NAMESPACE_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
_ITEM_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,127}$")
_TOKEN_PATTERN = re.compile(r"\w+", re.UNICODE)
_MAX_ITEMS_PER_WRITE = 100
_MAX_TEXT_CHARS = 20_000
_MAX_TOP_K = 100
_STORE_LOCK = threading.RLock()


def _serialized_write(function):
    """Serialize read/modify/write operations inside the single memory server."""
    @wraps(function)
    def locked(*args, **kwargs):
        with _STORE_LOCK:
            return function(*args, **kwargs)
    return locked


def workspace_root() -> Path:
    configured = os.getenv("LEION_WORKSPACE_ROOT", "").strip()
    if configured:
        return Path(configured).expanduser().resolve()
    return Path(__file__).resolve().parents[1] / ".leion_workspace"


def _validate_namespace(namespace: str) -> str:
    value = (namespace or "").strip()
    if not _NAMESPACE_PATTERN.fullmatch(value):
        raise ValueError("namespace must be a bounded identifier without path separators")
    return value


def _validate_item_id(item_id: Any) -> str:
    if not isinstance(item_id, str) or not _ITEM_ID_PATTERN.fullmatch(item_id):
        raise ValueError("each item id must be a bounded identifier without path separators")
    return item_id


def _namespace_path(namespace: str) -> Path:
    safe_namespace = _validate_namespace(namespace)
    return workspace_root() / "vector_store" / "namespaces" / f"{safe_namespace}.json"


def _load(namespace: str) -> Dict[str, Dict[str, Any]]:
    path = _namespace_path(namespace)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"memory namespace is unreadable: {exc}") from exc

    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise ValueError("memory namespace has an invalid schema")

    loaded: Dict[str, Dict[str, Any]] = {}
    for item in payload["items"]:
        if not isinstance(item, dict):
            raise ValueError("memory namespace contains an invalid item")
        item_id = _validate_item_id(item.get("id"))
        text = item.get("text")
        metadata = item.get("metadata", {})
        if not isinstance(text, str) or not isinstance(metadata, dict):
            raise ValueError("memory namespace contains an invalid item")
        loaded[item_id] = {"id": item_id, "text": text, "metadata": metadata}
    return loaded


def _write(namespace: str, items: Iterable[Dict[str, Any]]) -> None:
    path = _namespace_path(namespace)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "namespace": _validate_namespace(namespace),
        "items": sorted(items, key=lambda item: item["id"]),
    }
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent,
            prefix=f".{path.stem}-", suffix=".tmp", delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _normalise_item(item: Any) -> Dict[str, Any]:
    if not isinstance(item, dict):
        raise ValueError("each item must be an object")
    item_id = _validate_item_id(item.get("id"))
    text = item.get("text")
    metadata = item.get("metadata", {})
    if not isinstance(text, str) or not text.strip():
        raise ValueError("each item text must be a non-empty string")
    if len(text) > _MAX_TEXT_CHARS:
        raise ValueError(f"each item text must be at most {_MAX_TEXT_CHARS} characters")
    if not isinstance(metadata, dict):
        raise ValueError("each item metadata must be an object")
    try:
        json.dumps(metadata, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError) as exc:
        raise ValueError("each item metadata must be JSON serializable") from exc
    return {"id": item_id, "text": text, "metadata": metadata}


@_serialized_write
def add(namespace: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    try:
        safe_namespace = _validate_namespace(namespace)
        if not isinstance(items, list) or not items:
            raise ValueError("items must be a non-empty array")
        if len(items) > _MAX_ITEMS_PER_WRITE:
            raise ValueError(f"at most {_MAX_ITEMS_PER_WRITE} items may be written at once")
        normalised = [_normalise_item(item) for item in items]
        if len({item["id"] for item in normalised}) != len(normalised):
            raise ValueError("items must have unique ids within one write")
        existing = _load(safe_namespace)
        existing.update({item["id"]: item for item in normalised})
        _write(safe_namespace, existing.values())
        return {
            "ok": True,
            "backend": "local-json",
            "namespace": safe_namespace,
            "upserted": len(normalised),
            "count": len(existing),
        }
    except ValueError as exc:
        return {"ok": False, "error": {"code": "MEMORY_INPUT_INVALID", "message": str(exc)}}
    except OSError as exc:
        return {"ok": False, "error": {"code": "MEMORY_STORE_UNAVAILABLE", "message": str(exc)}}


def _matches_filter(metadata: Dict[str, Any], filter_values: Optional[Dict[str, Any]]) -> bool:
    return not filter_values or all(metadata.get(key) == value for key, value in filter_values.items())


def query(
    namespace: str,
    query_text: str,
    top_k: int = 5,
    filter_values: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    try:
        safe_namespace = _validate_namespace(namespace)
        if not isinstance(query_text, str) or not query_text.strip():
            raise ValueError("query must be a non-empty string")
        if not isinstance(top_k, int) or isinstance(top_k, bool) or not 1 <= top_k <= _MAX_TOP_K:
            raise ValueError(f"top_k must be an integer between 1 and {_MAX_TOP_K}")
        if filter_values is not None and not isinstance(filter_values, dict):
            raise ValueError("filter must be an object when supplied")

        terms = {token.casefold() for token in _TOKEN_PATTERN.findall(query_text)}
        matches = []
        for item in _load(safe_namespace).values():
            if not _matches_filter(item["metadata"], filter_values):
                continue
            item_tokens = {token.casefold() for token in _TOKEN_PATTERN.findall(item["text"])}
            score = len(terms & item_tokens)
            if score:
                matches.append({**item, "score": score})
        matches.sort(key=lambda item: (-item["score"], item["id"]))
        return {
            "ok": True,
            "backend": "local-json",
            "namespace": safe_namespace,
            "query": query_text,
            "items": matches[:top_k],
        }
    except ValueError as exc:
        return {"ok": False, "error": {"code": "MEMORY_INPUT_INVALID", "message": str(exc)}}
    except OSError as exc:
        return {"ok": False, "error": {"code": "MEMORY_STORE_UNAVAILABLE", "message": str(exc)}}


@_serialized_write
def delete(namespace: str, ids: List[str]) -> Dict[str, Any]:
    try:
        safe_namespace = _validate_namespace(namespace)
        if not isinstance(ids, list) or not ids:
            raise ValueError("ids must be a non-empty array")
        safe_ids = [_validate_item_id(item_id) for item_id in ids]
        if len(set(safe_ids)) != len(safe_ids):
            raise ValueError("ids must be unique")
        existing = _load(safe_namespace)
        deleted = [item_id for item_id in safe_ids if item_id in existing]
        for item_id in deleted:
            del existing[item_id]
        if deleted:
            _write(safe_namespace, existing.values())
        return {
            "ok": True,
            "backend": "local-json",
            "namespace": safe_namespace,
            "deleted": deleted,
            "count": len(existing),
        }
    except ValueError as exc:
        return {"ok": False, "error": {"code": "MEMORY_INPUT_INVALID", "message": str(exc)}}
    except OSError as exc:
        return {"ok": False, "error": {"code": "MEMORY_STORE_UNAVAILABLE", "message": str(exc)}}
