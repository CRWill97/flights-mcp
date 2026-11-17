"""Launch the flight search MCP server over STDIO or HTTP."""

import argparse
import os

from mcp.server.transport_security import TransportSecuritySettings
from starlette.requests import Request
from starlette.responses import JSONResponse

from .services.search import mcp


@mcp.custom_route("/health", methods=["GET"])
async def health(request: Request) -> JSONResponse:
    """Liveness check; does not query Duffel or expose configuration."""
    return JSONResponse({"status": "ok"})


def configure_http():
    render_host = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
    mcp.settings.host = os.getenv("MCP_BIND_HOST", "0.0.0.0" if render_host else "127.0.0.1")
    mcp.settings.port = int(os.getenv("PORT", "8000"))
    mcp.settings.streamable_http_path = "/mcp"
    mcp.settings.stateless_http = True
    mcp.settings.json_response = True
    hosts = ["127.0.0.1", "127.0.0.1:*", "localhost", "localhost:*"]
    origins = ["http://127.0.0.1:*", "http://localhost:*"]
    if render_host:
        hosts.extend([render_host, f"{render_host}:443"])
        origins.append(f"https://{render_host}")
    mcp.settings.transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=hosts,
        allowed_origins=origins,
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--http", action="store_true")
    args = parser.parse_args()

    if args.http:
        configure_http()
        mcp.run(transport="streamable-http")
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
