import json
import os
import re
from pathlib import Path
from typing import Any, Dict, Tuple


_WORKFLOW_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,63}$")
_SUPPORTED_NODE_TYPES = {"input", "transform", "output"}


def _definitions_root() -> Path:
    """Return the portable, bounded location for local workflow definitions."""
    default = Path(__file__).resolve().parents[1] / ".leion_workspace" / "workflows" / "definitions"
    configured = os.getenv("WORKFLOW_DEFINITIONS_DIR", "").strip()
    return Path(configured).expanduser().resolve() if configured else default


def definitions_root() -> Path:
    """Public shared resolver used by the workflow builder and runner."""
    return _definitions_root()


def _validated_workflow_id(workflow_id: str) -> str:
    value = (workflow_id or "").strip()
    if not _WORKFLOW_ID_PATTERN.fullmatch(value):
        raise ValueError(
            "workflow_id must be 1-64 characters of letters, digits, '.', '_' or '-', "
            "and must not contain a path separator"
        )
    return value


def workflow_path(workflow_id: str) -> Path:
    return _definitions_root() / f"{_validated_workflow_id(workflow_id)}.json"


def validate_definition(definition: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the deliberately small, deterministic embedded workflow format."""
    if not isinstance(definition, dict):
        return {"ok": False, "error": "workflow definition must be an object"}

    nodes = definition.get("nodes")
    edges = definition.get("edges", [])
    if not isinstance(nodes, list) or not nodes:
        return {"ok": False, "error": "workflow definition requires a non-empty nodes array"}
    if not isinstance(edges, list):
        return {"ok": False, "error": "workflow definition edges must be an array"}
    if len(nodes) > 256 or len(edges) > 4096:
        return {"ok": False, "error": "workflow definition exceeds the 256 node / 4096 edge limit"}

    node_ids: set[str] = set()
    node_types: Dict[str, str] = {}
    for node in nodes:
        if not isinstance(node, dict):
            return {"ok": False, "error": "each workflow node must be an object"}
        node_id = node.get("id")
        node_type = node.get("type")
        if not isinstance(node_id, str) or not _WORKFLOW_ID_PATTERN.fullmatch(node_id):
            return {"ok": False, "error": "each node id must be a bounded identifier"}
        if node_id in node_ids:
            return {"ok": False, "error": f"duplicate node id: {node_id}"}
        if not isinstance(node_type, str) or node_type not in _SUPPORTED_NODE_TYPES:
            return {
                "ok": False,
                "error": f"unsupported node type: {node_type}",
                "supported_node_types": sorted(_SUPPORTED_NODE_TYPES),
            }
        data = node.get("data", {})
        if not isinstance(data, dict):
            return {"ok": False, "error": "each node data value must be an object when supplied"}
        if node_type == "transform" and data.get("transform") != "uppercase":
            return {"ok": False, "error": "transform nodes currently support only data.transform='uppercase'"}
        node_ids.add(node_id)
        node_types[node_id] = node_type

    adjacency: Dict[str, list[str]] = {node_id: [] for node_id in node_ids}
    for edge in edges:
        if not isinstance(edge, dict):
            return {"ok": False, "error": "each workflow edge must be an object"}
        source, target = edge.get("source"), edge.get("target")
        if not isinstance(source, str) or not isinstance(target, str) or source not in node_ids or target not in node_ids:
            return {"ok": False, "error": "workflow edges must reference existing nodes"}
        if not isinstance(edge.get("sourceHandle"), str) or not isinstance(edge.get("targetHandle"), str):
            return {"ok": False, "error": "workflow edges require string sourceHandle and targetHandle"}
        adjacency[source].append(target)

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node_id: str) -> bool:
        if node_id in visiting:
            return False
        if node_id in visited:
            return True
        visiting.add(node_id)
        if not all(visit(target) for target in adjacency[node_id]):
            return False
        visiting.remove(node_id)
        visited.add(node_id)
        return True

    if not all(visit(node_id) for node_id in node_ids):
        return {"ok": False, "error": "workflow definition must be acyclic"}
    if "outputs" in definition and not isinstance(definition["outputs"], dict):
        return {"ok": False, "error": "workflow outputs must be an object when supplied"}
    if not any(node_type == "output" for node_type in node_types.values()):
        return {"ok": False, "error": "workflow definition requires an output node"}
    return {"ok": True}


def list_definitions() -> Dict[str, Any]:
    root = _definitions_root()
    if not root.exists():
        return {"ok": True, "root": str(root), "workflows": []}

    workflows = []
    for p in sorted(root.glob("*.json")):
        workflows.append({"id": p.stem, "path": str(p)})

    return {"ok": True, "root": str(root), "workflows": workflows}


def read_definition(workflow_id: str) -> Tuple[Dict[str, Any], str]:
    root = _definitions_root()
    try:
        path = workflow_path(workflow_id)
    except ValueError as exc:
        return ({"ok": False, "error": str(exc)}, "")
    if not path.exists():
        return ({"ok": False, "error": "workflow definition not found", "path": str(path)}, str(path))
    try:
        definition = json.loads(path.read_text(encoding="utf-8"))
        validation = validate_definition(definition)
        if not validation["ok"]:
            return ({**validation, "path": str(path)}, str(path))
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
    validation = validate_definition(definition)
    if not validation["ok"]:
        return validation

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

    # If no output names were supplied, collect the connected output handles.
    output_node = next(nid for nid, node in nodes.items() if node["type"] == "output")
    handles = sorted({edge[2] for edge in incoming.get(output_node, [])})
    return {"ok": True, "result": {handle: get_output(output_node, handle) for handle in handles}}
