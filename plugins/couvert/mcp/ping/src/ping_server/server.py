"""ping — a deliberately trivial diagnostic MCP server.

Its only job is to prove the transport works: stdio for CLI/desktop, and
streamable-HTTP for the claude.ai web surface (Stage 1). Do not make it useful;
make it certain.
"""

import datetime
import os

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ping")


@mcp.tool()
def ping() -> str:
    """Deterministic pong — proves the transport works."""
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    return f"pong @ {now} pid={os.getpid()}"


def main() -> None:
    # One source, both surfaces. Transport is chosen at runtime so the SAME
    # canonical server serves stdio (CLI/desktop) and streamable-HTTP (the
    # claude.ai chat surface) without a second implementation.
    #   PING_TRANSPORT=stdio  (default) -> CLI/desktop
    #   PING_TRANSPORT=http             -> streamable-HTTP (Stage 1 web reach)
    transport = os.environ.get("PING_TRANSPORT", "stdio").lower()
    if transport in ("http", "streamable-http"):
        # Bind address is deployment-dependent (a PaaS host sets $PORT). FastMCP
        # ignores FASTMCP_* env when its constructor sets defaults, so apply them
        # to settings here. $PORT/$HOST win, with FASTMCP_* as a fallback.
        host = os.environ.get("HOST") or os.environ.get("FASTMCP_HOST")
        port = os.environ.get("PORT") or os.environ.get("FASTMCP_PORT")
        if host:
            mcp.settings.host = host
        if port:
            mcp.settings.port = int(port)
        mcp.run(transport="streamable-http")
    else:
        mcp.run()


if __name__ == "__main__":
    main()
