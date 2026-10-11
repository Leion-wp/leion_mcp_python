import unittest
from types import SimpleNamespace
from unittest.mock import patch
from mcp.types import TextContent, ImageContent, Tool, ToolAnnotations
from servers import mcp_router as router


class FakeClient:
    calls = []

    def __init__(self, url):
        self.url = url

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args):
        pass

    async def call_tool(self, tool, args, **_kwargs):
        self.calls.append((self.url, tool, args))
        return SimpleNamespace(
            content=[TextContent(type="text", text="diagram"), ImageContent(type="image", data="AA==", mimeType="image/png")],
            structured_content={"checkpointId": "one"}, meta={"ui": {"resourceUri": "ui://excalidraw/mcp-app.html"}},
            data={"checkpointId": "one"}, is_error=False,
        )

    async def list_tools(self):
        return [Tool(name=name, description="Example", inputSchema={"type": "object"},
                     annotations=ToolAnnotations(readOnlyHint=True), _meta={"ui": {"resourceUri": "ui://excalidraw/mcp-app.html"}})
                for name in ["read_me", "create_view", "save_checkpoint", "read_checkpoint", "export_to_excalidraw", "arbitrary"]]


class ExcalidrawRouterTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        FakeClient.calls = []

    async def test_typed_results_preserve_legacy_fields_and_metadata(self):
        with patch.object(router, "Client", FakeClient):
            result = await router._call_tool("excalidraw", "create_view", {"elements": '[{"id":"one","type":"rectangle"}]'})
        self.assertEqual(result["content"][0], "diagram")
        self.assertEqual(result["data"], {"checkpointId": "one"})
        self.assertEqual(result["mcp_result"]["content"][1], {"type": "image", "data": "AA==", "mimeType": "image/png"})
        self.assertEqual(result["mcp_result"]["structuredContent"], {"checkpointId": "one"})
        self.assertEqual(result["mcp_result"]["_meta"], result["meta"])
        self.assertEqual(FakeClient.calls[0][0], "https://mcp.excalidraw.com")

    async def test_allowlist_and_bounded_inputs_block_before_transport(self):
        cases = [("export_to_excalidraw", {"json": "{}"}), ("arbitrary", {}), ("read_me", {"url": "https://elsewhere.test/"}),
                 ("create_view", {"elements": "{}"}), ("create_view", {"elements": "[" + " " * 524289 + "]"}),
                 ("read_checkpoint", {"id": "../outside"}), ("save_checkpoint", {"id": "one", "data": []}),
                 ("save_checkpoint", {"id": "one", "data": "[]"})]
        with patch.object(router, "Client", FakeClient):
            for tool, args in cases:
                with self.subTest(tool=tool, args_type=type(args)):
                    with self.assertRaises(ValueError):
                        await router._call_tool("excalidraw", tool, args)
        self.assertEqual(FakeClient.calls, [])

    async def test_checkpoint_contract_is_string_json_and_catalog_is_filtered(self):
        with patch.object(router, "Client", FakeClient):
            await router._call_tool("excalidraw", "save_checkpoint", {"id": "checkpoint-one", "data": '{"elements":[]}'})
            tools = await router._list_tools("excalidraw")
            legacy = await router._call_tool("runtime", "leion_runtime_catalog", {})
        self.assertEqual({tool.name for tool in tools}, router.EXCALIDRAW_TOOLS)
        self.assertEqual(tools[0].metadata["ui"]["resourceUri"], "ui://excalidraw/mcp-app.html")
        self.assertTrue(tools[0].annotations["readOnlyHint"])
        self.assertEqual(legacy["backend"], "runtime")
        self.assertEqual(router._pick_backend("excalidraw diagram"), "excalidraw")


if __name__ == "__main__":
    unittest.main()
