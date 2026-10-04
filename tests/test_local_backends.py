import os
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from tools import local_memory_store
from tools.local_workflow_runner import run_workflow, validate_definition


class LocalBackendTests(unittest.TestCase):
    def test_memory_concurrent_upserts_do_not_lose_items(self):
        with tempfile.TemporaryDirectory() as root, patch.dict(
            os.environ, {"LEION_WORKSPACE_ROOT": root}, clear=False
        ):
            def add_item(index):
                return local_memory_store.add("parallel", [{"id": str(index), "text": "shared note"}])

            with ThreadPoolExecutor(max_workers=8) as pool:
                results = list(pool.map(add_item, range(32)))
            found = local_memory_store.query("parallel", "shared", top_k=100)
        self.assertTrue(all(result["ok"] for result in results))
        self.assertEqual(len(found["items"]), 32)

    def test_memory_rejects_path_traversal_and_malformed_store(self):
        with tempfile.TemporaryDirectory() as root, patch.dict(
            os.environ, {"LEION_WORKSPACE_ROOT": root}, clear=False
        ):
            rejected = local_memory_store.add("../escape", [{"id": "1", "text": "note"}])
            self.assertFalse(rejected["ok"])
            self.assertFalse((Path(root) / "escape.json").exists())
            path = local_memory_store._namespace_path("broken")
            path.parent.mkdir(parents=True)
            path.write_text('{}', encoding="utf-8")
            self.assertFalse(local_memory_store.query("broken", "note")["ok"])

    def test_workflow_rejects_unhashable_types_and_oversized_graphs(self):
        for definition in (
            {"nodes": [{"id": "output", "type": []}]},
            {"nodes": [{"id": "output", "type": "output"}], "edges": [{"source": [], "target": "output"}]},
            {"nodes": [{"id": str(index), "type": "output"} for index in range(257)]},
        ):
            with self.subTest(definition=definition):
                self.assertFalse(validate_definition(definition)["ok"])

    def test_local_memory_is_deterministic_and_filterable(self):
        with tempfile.TemporaryDirectory() as root, patch.dict(
            os.environ, {"LEION_WORKSPACE_ROOT": root}, clear=False
        ):
            added = local_memory_store.add(
                "revenue",
                [
                    {"id": "asset", "text": "Revenue asset scout", "metadata": {"kind": "note"}},
                    {"id": "gate", "text": "Workflow quality gate", "metadata": {"kind": "gate"}},
                ],
            )
            found = local_memory_store.query("revenue", "revenue asset", filter_values={"kind": "note"})
            deleted = local_memory_store.delete("revenue", ["asset"])

        self.assertEqual(added["count"], 2)
        self.assertEqual([item["id"] for item in found["items"]], ["asset"])
        self.assertEqual(deleted["deleted"], ["asset"])

    def test_local_workflow_requires_a_safe_acyclic_definition(self):
        definition = {
            "nodes": [
                {"id": "input", "type": "input"},
                {"id": "upper", "type": "transform", "data": {"transform": "uppercase"}},
                {"id": "output", "type": "output"},
            ],
            "edges": [
                {"source": "input", "sourceHandle": "value", "target": "upper", "targetHandle": "value"},
                {"source": "upper", "sourceHandle": "result", "target": "output", "targetHandle": "result"},
            ],
            "outputs": {"result": {}},
        }

        self.assertEqual(validate_definition(definition), {"ok": True})
        self.assertEqual(run_workflow(definition, {"value": "hello"}), {"ok": True, "result": {"result": "HELLO"}})

        definition["edges"].append(
            {"source": "output", "sourceHandle": "result", "target": "input", "targetHandle": "value"}
        )
        self.assertEqual(validate_definition(definition)["error"], "workflow definition must be acyclic")


if __name__ == "__main__":
    unittest.main()
