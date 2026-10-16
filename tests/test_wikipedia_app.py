import pytest
from fastmcp import Client
from wikipedia_mcp.server import create_server


@pytest.mark.asyncio
async def test_ui_tool_and_html_resource_are_discoverable():
    async with Client(create_server()) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}
        assert "open_wikipedia" in tools
        meta = tools["open_wikipedia"].meta
        assert meta["ui"]["resourceUri"] == "ui://wikipedia/start"
        assert meta["openai/ui"]["entrypoints"] == [{"type": "global"}]
        content = await client.read_resource("ui://wikipedia/start")
        assert content[0].mimeType == "text/html;profile=mcp-app"
        assert "How many PDF files" in content[0].text
        assert "ui/initialize" in content[0].text
        result = await client.call_tool("open_wikipedia", {})
        assert not result.is_error


@pytest.mark.asyncio
async def test_native_pdf_exports_are_official_and_distinct():
    async with Client(create_server()) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}
        assert "wikipedia_pdf_exports" in tools
        result = await client.call_tool(
            "wikipedia_pdf_exports",
            {"titles": ["Neural network (machine learning)", "Matrix calculus", "Matrix calculus"], "language": "en"},
        )
        assert not result.is_error
        data = result.data
        assert data["count"] == 2
        assert (
            data["files"][0]["pdf_url"]
            == "https://en.wikipedia.org/api/rest_v1/page/pdf/Neural_network_(machine_learning)"
        )
        assert data["files"][0]["mime_type"] == "application/pdf"


@pytest.mark.asyncio
async def test_invalid_pdf_language_cannot_choose_another_host():
    async with Client(create_server()) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}
        assert "wikipedia_pdf_exports" in tools
        with pytest.raises(Exception):
            await client.call_tool("wikipedia_pdf_exports", {"titles": ["Test"], "language": "evil.com/path"})
