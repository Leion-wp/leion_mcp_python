"""Exercise the priority backends through actual MCP list/call contracts."""

import os
import tempfile
import unittest
from unittest.mock import patch

from fastmcp import Client
from servers import mcp_business, mcp_memory, mcp_workflows


class MCPContractTests(unittest.IsolatedAsyncioTestCase):
    async def test_priority_backends_register_expected_tools(self):
        for server, expected in (
            (mcp_workflows.server, "workflow_run"),
            (mcp_memory.server, "vector_store_query"),
            (mcp_business.server, "business_launch_plan"),
        ):
            async with Client(server) as client:
                names = {tool.name for tool in await client.list_tools()}
                self.assertIn(expected, names)
                self.assertNotIn("shell_run", names)

    async def test_memory_add_and_query_over_mcp(self):
        with tempfile.TemporaryDirectory() as root, patch.dict(
            os.environ, {"LEION_WORKSPACE_ROOT": root}, clear=False
        ), patch("tools.vector_memory_tools.MEMORY_BACKEND", "local"):
            async with Client(mcp_memory.server) as client:
                added = await client.call_tool("vector_store_add", {
                    "namespace": "contract", "items": [{"id": "note", "text": "MCP memory proof"}],
                })
                self.assertTrue(added.data["ok"])
                found = await client.call_tool("vector_store_query", {"namespace": "contract", "query": "proof"})
                self.assertEqual(found.data["items"][0]["id"], "note")

    async def test_workflow_save_read_and_run_use_the_same_root(self):
        definition = {
            "nodes": [{"id": "input", "type": "input"}, {"id": "output", "type": "output"}],
            "edges": [{"source": "input", "sourceHandle": "value", "target": "output", "targetHandle": "result"}],
        }
        with tempfile.TemporaryDirectory() as root, patch.dict(
            os.environ, {"WORKFLOW_DEFINITIONS_DIR": root, "WORKFLOW_RUNNER": "local"}, clear=False
        ):
            async with Client(mcp_workflows.server) as client:
                saved = await client.call_tool("workflow_save_definition", {"workflow_id": "proof", "definition": definition})
                self.assertTrue(saved.data["ok"])
                run = await client.call_tool("workflow_run", {"workflow_id": "proof", "inputs": {"value": "verified"}})
                self.assertEqual(run.data, {"ok": True, "result": {"result": "verified"}})

    async def test_business_plan_is_available_without_external_accounts(self):
        async with Client(mcp_business.server) as client:
            plan = await client.call_tool("business_launch_plan", {"niche": "test", "objective": "verify"})
            self.assertEqual(plan.data["niche"], "test")
            self.assertEqual(len(plan.data["steps"]), 6)
