"""Computer-use MCP server.

Exposes screen capture + keyboard/mouse primitives to hermes-agent so its
openai-codex loop can operate a real browser inside WSL's Xvfb display,
mirroring the anthropic-quickstarts/computer-use-demo architecture but
reachable over stdio MCP instead of a direct Anthropic call.
"""
from __future__ import annotations

import base64
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Literal

from mcp.server.fastmcp import Context, FastMCP
from mcp.types import ImageContent, TextContent

DISPLAY = os.environ.get("CU_DISPLAY_ENV", f":{os.environ.get('CU_DISPLAY', '99')}")
WIDTH = int(os.environ.get("CU_WIDTH", "1440"))
HEIGHT = int(os.environ.get("CU_HEIGHT", "900"))
STATE_DIR = Path(os.environ.get("CU_STATE_DIR", "/tmp/hermes-computer-use"))
SHOT_PATH = STATE_DIR / "last.png"
INPUT_BACKEND = os.environ.get("CU_INPUT", "xdotool")  # xdotool | ydotool
KEY_DELAY_MS = int(os.environ.get("CU_KEY_DELAY_MS", "25"))
MOVE_STEPS = int(os.environ.get("CU_MOVE_STEPS", "18"))


def _log(msg: str) -> None:
    print(msg, file=sys.stderr, flush=True)


def _env() -> dict:
    e = os.environ.copy()
    e["DISPLAY"] = DISPLAY
    return e


def _run(cmd: list[str], timeout: float = 10.0) -> tuple[int, str, str]:
    p = subprocess.run(cmd, env=_env(), capture_output=True, timeout=timeout)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def _require(tool: str) -> None:
    rc, _, _ = _run(["which", tool])
    if rc != 0:
        raise RuntimeError(f"missing binary: {tool} — did you run setup.sh?")


def _capture_png() -> bytes:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    # scrot is lightweight; falls back to ImageMagick `import` if unavailable.
    if subprocess.run(["which", "scrot"], capture_output=True).returncode == 0:
        rc, _, err = _run(["scrot", "-o", str(SHOT_PATH)], timeout=10)
        if rc != 0:
            raise RuntimeError(f"scrot failed: {err.strip()}")
    else:
        rc, _, err = _run(["import", "-window", "root", str(SHOT_PATH)], timeout=15)
        if rc != 0:
            raise RuntimeError(f"import failed: {err.strip()}")
    return SHOT_PATH.read_bytes()


def _xdo(*args: str, timeout: float = 10.0) -> None:
    rc, _, err = _run(["xdotool", *args], timeout=timeout)
    if rc != 0:
        raise RuntimeError(f"xdotool {args!r} failed: {err.strip()}")


def _ydo(*args: str, timeout: float = 10.0) -> None:
    rc, _, err = _run(["ydotool", *args], timeout=timeout)
    if rc != 0:
        raise RuntimeError(f"ydotool {args!r} failed: {err.strip()}")


def _humanlike_move(x1: int, y1: int, x2: int, y2: int, steps: int) -> None:
    """Interpolate the cursor with light jitter so Xvfb sees smooth movement."""
    import random

    steps = max(2, steps)
    for i in range(1, steps + 1):
        t = i / steps
        # Ease-in-out cubic.
        e = 3 * t * t - 2 * t * t * t
        x = int(x1 + (x2 - x1) * e + (random.random() - 0.5) * 2)
        y = int(y1 + (y2 - y1) * e + (random.random() - 0.5) * 2)
        _xdo("mousemove", str(x), str(y))
        time.sleep(0.008 + random.random() * 0.008)


# ─── MCP server ────────────────────────────────────────────────────────────

mcp = FastMCP(
    name="computer-use",
    instructions=(
        "Operate a real browser in an Xvfb display via pixel-level input. "
        "Workflow: call `screenshot` → reason about pixel coordinates → call "
        "`left_click`/`type_text`/`drag`/`scroll`/etc. → repeat. Coordinates "
        "are absolute pixels in the virtual display. Never assume DOM state; "
        "always re-screenshot after an action to verify."
    ),
)


@mcp.tool()
def screen_info() -> str:
    """Return the virtual display geometry and backend settings."""
    return (
        f"display={DISPLAY} size={WIDTH}x{HEIGHT} input_backend={INPUT_BACKEND} "
        f"state_dir={STATE_DIR}"
    )


@mcp.tool()
def screenshot(ctx: Context) -> list:
    """Capture the current Xvfb screen and return it as a PNG image."""
    png = _capture_png()
    b64 = base64.b64encode(png).decode("ascii")
    return [
        ImageContent(type="image", data=b64, mimeType="image/png"),
        TextContent(type="text", text=f"{len(png)} bytes; {WIDTH}x{HEIGHT}"),
    ]


@mcp.tool()
def cursor_position() -> str:
    """Return the current mouse cursor (x,y)."""
    rc, out, err = _run(["xdotool", "getmouselocation", "--shell"])
    if rc != 0:
        raise RuntimeError(err)
    kv = dict(line.split("=", 1) for line in out.strip().splitlines() if "=" in line)
    return f"x={kv.get('X','?')} y={kv.get('Y','?')} screen={kv.get('SCREEN','?')}"


@mcp.tool()
def move(x: int, y: int, human: bool = True) -> str:
    """Move the cursor to (x,y). Set human=False for an instant jump."""
    if human:
        rc, out, _ = _run(["xdotool", "getmouselocation", "--shell"])
        cx, cy = 0, 0
        if rc == 0:
            kv = dict(line.split("=", 1) for line in out.strip().splitlines() if "=" in line)
            cx, cy = int(kv.get("X", 0)), int(kv.get("Y", 0))
        _humanlike_move(cx, cy, x, y, MOVE_STEPS)
    else:
        _xdo("mousemove", str(x), str(y))
    return f"cursor at ({x},{y})"


@mcp.tool()
def left_click(x: int, y: int, human: bool = True) -> str:
    """Move to (x,y) then single left-click."""
    move(x, y, human=human)
    _xdo("click", "1")
    return f"left_click ({x},{y})"


@mcp.tool()
def right_click(x: int, y: int, human: bool = True) -> str:
    """Move to (x,y) then single right-click."""
    move(x, y, human=human)
    _xdo("click", "3")
    return f"right_click ({x},{y})"


@mcp.tool()
def double_click(x: int, y: int, human: bool = True) -> str:
    """Move to (x,y) then double left-click."""
    move(x, y, human=human)
    _xdo("click", "--repeat", "2", "--delay", "80", "1")
    return f"double_click ({x},{y})"


@mcp.tool()
def middle_click(x: int, y: int, human: bool = True) -> str:
    """Move to (x,y) then single middle-click (typically opens link in new tab)."""
    move(x, y, human=human)
    _xdo("click", "2")
    return f"middle_click ({x},{y})"


@mcp.tool()
def drag(x1: int, y1: int, x2: int, y2: int, steps: int = 25) -> str:
    """Press-and-hold left button at (x1,y1), drag to (x2,y2), release."""
    _xdo("mousemove", str(x1), str(y1))
    time.sleep(0.05)
    _xdo("mousedown", "1")
    try:
        _humanlike_move(x1, y1, x2, y2, steps)
    finally:
        _xdo("mouseup", "1")
    return f"drag ({x1},{y1}) -> ({x2},{y2})"


@mcp.tool()
def scroll(
    direction: Literal["up", "down", "left", "right"] = "down",
    amount: int = 3,
    x: int | None = None,
    y: int | None = None,
) -> str:
    """Scroll wheel at cursor (or at given x/y if provided). amount = click count."""
    if x is not None and y is not None:
        move(x, y, human=False)
    btn = {"up": "4", "down": "5", "left": "6", "right": "7"}[direction]
    _xdo("click", "--repeat", str(max(1, amount)), "--delay", "40", btn)
    return f"scroll {direction} x{amount}"


@mcp.tool()
def type_text(text: str, delay_ms: int = KEY_DELAY_MS) -> str:
    """Type unicode text into whatever widget currently has focus."""
    _xdo("type", "--delay", str(max(0, delay_ms)), "--", text)
    return f"typed {len(text)} char(s)"


@mcp.tool()
def press_key(key: str) -> str:
    """Press a single key or chord. Examples: 'Return', 'Escape', 'Tab',
    'ctrl+c', 'ctrl+shift+t', 'alt+Left'."""
    _xdo("key", "--delay", "20", key)
    return f"pressed {key}"


@mcp.tool()
def hold_key(key: str, ms: int = 500) -> str:
    """Hold a key down for ms milliseconds, then release."""
    _xdo("keydown", key)
    try:
        time.sleep(max(0, ms) / 1000.0)
    finally:
        _xdo("keyup", key)
    return f"held {key} {ms}ms"


@mcp.tool()
def wait(ms: int) -> str:
    """Sleep for ms milliseconds (useful to wait for page loads/animations)."""
    time.sleep(max(0, ms) / 1000.0)
    return f"waited {ms}ms"


@mcp.tool()
def open_url(url: str) -> str:
    """Focus Chrome's address bar and load a URL."""
    _xdo("search", "--onlyvisible", "--name", "Chrome", "windowactivate", "--sync")
    time.sleep(0.15)
    _xdo("key", "ctrl+l")
    time.sleep(0.1)
    _xdo("type", "--delay", "8", "--", url)
    _xdo("key", "Return")
    return f"navigated to {url}"


@mcp.tool()
def new_tab(url: str = "about:blank") -> str:
    """Open a new Chrome tab to url."""
    _xdo("search", "--onlyvisible", "--name", "Chrome", "windowactivate", "--sync")
    time.sleep(0.1)
    _xdo("key", "ctrl+t")
    time.sleep(0.15)
    if url and url != "about:blank":
        _xdo("type", "--delay", "8", "--", url)
        _xdo("key", "Return")
    return f"new tab -> {url}"


@mcp.tool()
def close_tab() -> str:
    """Close the active Chrome tab (ctrl+w)."""
    _xdo("search", "--onlyvisible", "--name", "Chrome", "windowactivate", "--sync")
    _xdo("key", "ctrl+w")
    return "tab closed"


@mcp.tool()
def back() -> str:
    """Browser back (alt+Left)."""
    _xdo("key", "alt+Left")
    return "back"


@mcp.tool()
def forward() -> str:
    """Browser forward (alt+Right)."""
    _xdo("key", "alt+Right")
    return "forward"


@mcp.tool()
def reload(hard: bool = False) -> str:
    """Reload page. hard=True for ctrl+shift+R."""
    _xdo("key", "ctrl+shift+r" if hard else "ctrl+r")
    return "reloaded" + (" (hard)" if hard else "")


@mcp.tool()
def run_shell(cmd: str, timeout: int = 30) -> str:
    """Run a shell command inside WSL (for ops like `ls`, `curl`, file ops).

    Intentionally unrestricted — hermes-agent is trusted. Returns combined stdout/stderr.
    """
    p = subprocess.run(
        cmd, shell=True, capture_output=True, timeout=timeout,
        env=_env(),
    )
    out = p.stdout.decode("utf-8", "replace")
    err = p.stderr.decode("utf-8", "replace")
    return f"exit={p.returncode}\n--- stdout ---\n{out}--- stderr ---\n{err}"


def main() -> None:
    """Entry point for `python -m hermes_computer_use` and the `hermes-computer-use` console script."""
    try:
        _require("xdotool")
        _require("Xvfb")
    except RuntimeError as e:
        _log(f"[FATAL] {e}")
        sys.exit(2)
    _log(f"[OK] computer-use MCP ready (DISPLAY={DISPLAY}, {WIDTH}x{HEIGHT})")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
