import json
import os
from pathlib import Path
from typing import Any, Dict, Tuple


def _definitions_root() -> Path:
    # Default path inside container (mounted from host)
    default = "/workspace/leion-autobuilder/workflows/definitions"
    return Path(os.getenv("WORKFLOW_DEFINITIONS_DIR", default))


def list_definitions() -> Dict[str, Any]:
    root = _definitions_root()
    if not root.exists():
        return {"ok": False, "error": "definitions dir not found", "root": str(root), "workflows": []}

    workflows = []
    for p in sorted(root.glob("*.json")):
        workflows.append({"id": p.stem, "path": str(p)})

    return {"ok": True, "root": str(root), "workflows": workflows}


def read_definition(workflow_id: str) -> Tuple[Dict[str, Any], str]:
    root = _definitions_root()
    path = root / f"{workflow_id}.json"
    if not path.exists():
        return ({"ok": False, "error": "workflow definition not found", "path": str(path)}, str(path))
    try:
        definition = json.loads(path.read_text(encoding="utf-8"))
        return ({"ok": True, "path": str(path), "definition": definition}, str(path))
    except Exception as e:
        return ({"ok": False, "error": str(e), "path": str(path)}, str(path))


def run_workflow(definition: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Very small runner for the 'test_workflow' style graphs.

    Supported node types:
    - input: provides outputs from `inputs`
    - transform: supports transform 'uppercase'
    - output: collects named inputs into result

    This is intentionally minimal to unblock MCP validation.
    """
    nodes = {n.get("id"): n for n in definition.get("nodes", [])}
    edges = definition.get("edges", [])

    # Build adjacency: target -> list of (source, sourceHandle, targetHandle)
    incoming = {}
    for e in edges:
        incoming.setdefault(e.get("target"), []).append((e.get("source"), e.get("sourceHandle"), e.get("targetHandle")))

    cache: Dict[Tuple[str, str], Any] = {}

    def get_output(node_id: str, handle: str):
        key = (node_id, handle)
        if key in cache:
            return cache[key]

        node = nodes.get(node_id)
        if not node:
            raise ValueError(f"Unknown node: {node_id}")
        ntype = node.get("type")
        data = node.get("data", {})

        if ntype == "input":
            # map handle -> inputs[handle]
            val = inputs.get(handle)
            cache[key] = val
            return val

        if ntype == "transform":
            # get its input values based on incoming edge(s)
            in_edges = incoming.get(node_id, [])
            # find edge that maps to this handle
            src_val = None
            for (src, src_h, tgt_h) in in_edges:
                if tgt_h == handle:
                    src_val = get_output(src, src_h)
                    break
            # if asking for output handle, compute from its single input named 'value' by convention
            if handle in ("result",):
                # Find input connected to 'value' (common)
                val_in = None
                for (src, src_h, tgt_h) in in_edges:
                    if tgt_h == "value":
                        val_in = get_output(src, src_h)
                        break
                transform = data.get("transform")
                if transform == "uppercase":
                    out = ("" if val_in is None else str(val_in)).upper()
                else:
                    raise ValueError(f"Unsupported transform: {transform}")
                cache[key] = out
                return out
            # else it's an input handle request
            cache[key] = src_val
            return src_val

        if ntype == "output":
            # outputs don't generate values; but allow fetching their input as passthrough
            in_edges = incoming.get(node_id, [])
            for (src, src_h, tgt_h) in in_edges:
                if tgt_h == handle:
                    val = get_output(src, src_h)
                    cache[key] = val
                    return val
            cache[key] = None
            return None

        raise ValueError(f"Unsupported node type: {ntype}")

    # Collect outputs: use definition.outputs keys if present, else just gather inputs to output node
    outputs_spec = definition.get("outputs") or {}
    if outputs_spec:
        out = {}
        for out_name in outputs_spec.keys():
            # Try to read from output node via incoming mapping
            # Find node of type output
            output_nodes = [nid for nid, n in nodes.items() if n.get("type") == "output"]
            if output_nodes:
                out[out_name] = get_output(output_nodes[0], out_name)
            else:
                out[out_name] = None
        return {"ok": True, "result": out}

    # fallback
    return {"ok": True, "result": {}}
