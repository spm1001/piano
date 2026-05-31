# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=1.2"]
# ///
"""Smoke-test the ping MCP over stdio: handshake, list tools, call ping."""

import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> int:
    params = StdioServerParameters(
        command="uv", args=["run", "--directory", "./mcp/ping", "ping-server"]
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = [t.name for t in tools.tools]
            print(f"tools: {names}")
            assert names == ["ping"], f"expected [ping], got {names}"
            result = await session.call_tool("ping", {})
            text = result.content[0].text
            print(f"ping -> {text}")
            assert text.startswith("pong @ "), f"unexpected: {text!r}"
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
