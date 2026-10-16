"""Native MCP App entrypoint and official Wikipedia PDF export links."""

import re
from pathlib import Path
from urllib.parse import quote

from fastmcp import FastMCP

UI_URI = "ui://wikipedia/start"


def register_app(server: FastMCP) -> None:
    """Attach the UI without changing the existing Wikipedia tools."""

    @server.resource(
        UI_URI,
        name="Wikipedia request form",
        mime_type="text/html;profile=mcp-app",
        meta={
            "ui": {"csp": {"connectDomains": [], "resourceDomains": []}, "prefersBorder": True},
            "openai/ui": {"availableDisplayModes": ["inline", "fullscreen"], "preferredDisplayMode": "fullscreen"},
        },
    )
    def wikipedia_form() -> str:
        return Path(__file__).with_name("ui").joinpath("start.html").read_text(encoding="utf-8")

    @server.tool(
        name="open_wikipedia",
        title="Wikipedia kh",
        description=(
            "Open the Wikipedia UI first when the user starts a Wikipedia request. "
            "The form collects topic, output option, then PDF count when PDFs are selected. "
            "Pass known topic, output and PDF count as optional prefill, or call with no arguments. "
            "Wait for the user to submit the form."
        ),
        annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
        meta={
            "ui": {"resourceUri": UI_URI, "visibility": ["model", "app"]},
            "openai/outputTemplate": UI_URI,
            "openai/ui": {"entrypoints": [{"type": "global"}]},
        },
    )
    def open_wikipedia(topic: str = "", output: str = "", pdf_count: int = 0) -> dict:
        if not 0 <= pdf_count <= 500:
            raise ValueError("Choose 1 to 500 PDF files per batch")
        return {
            "status": "awaiting_user",
            "first_step": "topic",
            "default_pdf_delivery": ["individual", "combined"],
            "prefill": {"topic": topic, "output": output, "pdf_count": pdf_count},
        }

    @server.tool(
        name="wikipedia_pdf_exports",
        title="Official Wikipedia PDFs",
        description=(
            "Return official Wikipedia article PDF export URLs for exact article titles. "
            "These are article PDFs, not externally cited research papers. "
            "This tool provides export links; use the PDF skill to download, validate, ZIP and merge."
        ),
        annotations={"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": True},
    )
    def wikipedia_pdf_exports(titles: list[str], language: str = "en") -> dict:
        if not re.fullmatch(r"[a-z]{2,12}(?:-[a-z0-9]{1,12})*", language):
            raise ValueError("Use a Wikipedia language code such as en or ar")
        clean = list(dict.fromkeys(title.strip() for title in titles if title.strip()))
        if not clean or len(clean) > 500:
            raise ValueError("Supply between 1 and 500 distinct article titles")
        files = []
        for title in clean:
            slug = quote(title.replace(" ", "_"), safe="()")
            base = f"https://{language}.wikipedia.org"
            files.append(
                {
                    "title": title,
                    "mime_type": "application/pdf",
                    "article_url": f"{base}/wiki/{slug}",
                    "pdf_url": f"{base}/api/rest_v1/page/pdf/{slug}",
                    "download_page": f"{base}/wiki/Special:DownloadAsPdf/{slug}",
                }
            )
        return {"count": len(files), "language": language, "files": files, "downloaded": False}
