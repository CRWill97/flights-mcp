"""Check a running HTTP MCP server without calling the Duffel API."""

import argparse
import asyncio
from datetime import timedelta

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


async def check(url: str) -> None:
    async with streamable_http_client(url) as (read, write, _):
        async with ClientSession(
            read, write, read_timeout_seconds=timedelta(seconds=20)
        ) as session:
            info = await session.initialize()
            result = await session.list_tools()
            names = {tool.name for tool in result.tools}
            expected = {"search_flights", "get_offer_details", "search_multi_city"}
            missing = expected - names
            if missing:
                raise RuntimeError(f"Missing tools: {sorted(missing)}")
            print(f"Connected to {info.serverInfo.name}")
            print(f"Tools: {', '.join(sorted(names))}")
            print("PASS: MCP initialization and tool discovery; Duffel API not called.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8000/mcp")
    args = parser.parse_args()
    asyncio.run(asyncio.wait_for(check(args.url), timeout=30))
