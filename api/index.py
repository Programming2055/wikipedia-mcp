"""Vercel ASGI entrypoint for the existing Wikipedia MCP tools."""
import os
from wikipedia_mcp.server import create_server

mcp = create_server(
    language=os.getenv("WIKIPEDIA_LANGUAGE", "en"),
    enable_cache=False,
    access_token=os.getenv("WIKIPEDIA_ACCESS_TOKEN") or None,
)
app = mcp.http_app(path="/mcp", stateless_http=True)
