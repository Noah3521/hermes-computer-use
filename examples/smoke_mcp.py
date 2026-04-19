"""Spin up the computer-use MCP server as a subprocess and exercise it."""
from __future__ import annotations

import asyncio
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main() -> None:
    env = {
        **os.environ,
        "DISPLAY": ":99",
        "CU_DISPLAY": "99",
        "CU_WIDTH": "1440",
        "CU_HEIGHT": "900",
        "CU_STATE_DIR": "/tmp/hermes-computer-use",
    }
    env.pop("WAYLAND_DISPLAY", None)

    params = StdioServerParameters(
        command="/home/geunuk/.hermes/hermes-agent/venv/bin/python",
        args=["/home/geunuk/.hermes/integrations/computer-use/computer_use_mcp.py"],
        env=env,
    )

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as sess:
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
            print(f"screenshot: {len(img.data)} b64 chars ({txt.text if txt else ''})")

            r = await sess.call_tool("move", {"x": 720, "y": 450, "human": False})
            print("move:", r.content[0].text)

            r = await sess.call_tool("cursor_position", {})
            print("cursor:", r.content[0].text)


if __name__ == "__main__":
    asyncio.run(main())
