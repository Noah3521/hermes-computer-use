"""End-to-end smoke test against a running Xvfb stack.

Spins up the MCP server as a subprocess over stdio, lists its tools, and
exercises a handful of them. Requires `scripts/display.sh start` to have been
run, so there is a real Chrome visible on :99.

Run from the repo root after `pip install -e .`:

    python examples/smoke_test.py
"""
from __future__ import annotations

import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    env = {
        **os.environ,
        "DISPLAY": f":{os.environ.get('CU_DISPLAY', '99')}",
        "CU_DISPLAY": os.environ.get("CU_DISPLAY", "99"),
        "CU_WIDTH": os.environ.get("CU_WIDTH", "1440"),
        "CU_HEIGHT": os.environ.get("CU_HEIGHT", "900"),
    }
    env.pop("WAYLAND_DISPLAY", None)

    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "hermes_computer_use"],
        env=env,
    )

    async with stdio_client(params) as (read, write), ClientSession(read, write) as sess:
        await sess.initialize()

        tools = await sess.list_tools()
        names = sorted(t.name for t in tools.tools)
        print(f"tools ({len(names)}): {', '.join(names)}")

        info = await sess.call_tool("screen_info", {})
        print("screen_info:", info.content[0].text)

        shot = await sess.call_tool("screenshot", {})
        img = next((c for c in shot.content if c.type == "image"), None)
        txt = next((c for c in shot.content if c.type == "text"), None)
        assert img, "screenshot did not return image content"
        print(f"screenshot : {len(img.data)} b64 chars ({txt.text if txt else ''})")

        r = await sess.call_tool("move", {"x": 720, "y": 450, "human": False})
        print("move       :", r.content[0].text)

        r = await sess.call_tool("cursor_position", {})
        print("cursor     :", r.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())
