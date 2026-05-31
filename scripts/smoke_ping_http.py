# /// script
# requires-python = ">=3.10"
# dependencies = ["mcp>=1.2"]
# ///
"""Loopback smoke-test for ping over streamable-HTTP.

Boots the SAME canonical ping binary with PING_TRANSPORT=http, connects via a
streamable-HTTP client, and asserts the pong. This proves the transport split
(stdio vs HTTP) from one source — without any deployment. Public HTTPS
reachability + the claude.ai connector are Stage 1, not this.
"""

import asyncio
import os
import socket
import subprocess
import sys
import time

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

# A dedicated, unusual port so a stray server on the default 8000 cannot poison
# the smoke (FastMCP reads FASTMCP_HOST / FASTMCP_PORT from the environment).
HOST = "127.0.0.1"
PORT = 8791
URL = f"http://{HOST}:{PORT}/mcp"


def wait_for_port(host: str, port: int, timeout: float = 30.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            if s.connect_ex((host, port)) == 0:
                return
        time.sleep(0.25)
    raise TimeoutError(f"{host}:{port} did not open within {timeout}s")


async def exercise() -> None:
    async with streamablehttp_client(URL) as (read, write, _):
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


def main() -> int:
    env = {
        **os.environ,
        "PING_TRANSPORT": "http",
        "FASTMCP_HOST": HOST,
        "FASTMCP_PORT": str(PORT),
    }
    # Capture server output so a startup failure is visible, not silent.
    log = open("/tmp/smoke_ping_http_server.log", "w")
    server = subprocess.Popen(
        ["uv", "run", "--directory", "./mcp/ping", "ping-server"],
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
    )
    try:
        try:
            wait_for_port(HOST, PORT)
        except TimeoutError:
            log.flush()
            sys.stderr.write("--- server log ---\n")
            sys.stderr.write(open("/tmp/smoke_ping_http_server.log").read())
            raise
        asyncio.run(exercise())
    finally:
        server.terminate()
        try:
            server.wait(timeout=10)
        except subprocess.TimeoutExpired:
            server.kill()
        log.close()
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
