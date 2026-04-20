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
    # xdotool prints "No such key name" to stderr but exits 0 — treat as failure.
    if "No such key name" in err or "Unknown keysym" in err:
        raise RuntimeError(f"xdotool {args!r} invalid key: {err.strip()}")


def _ydo(*args: str, timeout: float = 10.0) -> None:
    rc, _, err = _run(["ydotool", *args], timeout=timeout)
    if rc != 0:
        raise RuntimeError(f"ydotool {args!r} failed: {err.strip()}")


# Map common/alternate key spellings to xdotool keysyms. Callers get to spell
# keys the way their agent or OS docs already spell them — we normalize.
_KEY_ALIASES = {
    "backspace": "BackSpace",
    "enter": "Return",
    "space": "space",
    "spacebar": "space",
    "esc": "Escape",
    "escape": "Escape",
    "tab": "Tab",
    "del": "Delete",
    "delete": "Delete",
    "ins": "Insert",
    "insert": "Insert",
    "home": "Home",
    "end": "End",
    "pageup": "Page_Up",
    "page_up": "Page_Up",
    "pgup": "Page_Up",
    "pagedown": "Page_Down",
    "page_down": "Page_Down",
    "pgdn": "Page_Down",
    "up": "Up",
    "down": "Down",
    "left": "Left",
    "right": "Right",
    "caps": "Caps_Lock",
    "capslock": "Caps_Lock",
    "meta": "super",   # on Linux "meta" usually means the Super/Windows key
    "win": "super",
    "windows": "super",
    "cmd": "super",    # Mac ergonomics — agents fluent in Cmd shortcuts
    "command": "super",
    "option": "alt",   # Mac ergonomics
    "opt": "alt",
    "ctl": "ctrl",
    "control": "ctrl",
    "return": "Return",
}


def _normalize_key(key: str) -> str:
    """Turn a chord like 'cmd-shift-backspace' into xdotool's 'super+shift+BackSpace'.

    Accepts '+' or '-' as the chord separator, arbitrary casing for modifier
    names, and the common aliases above. Multi-character tokens get alias
    lookup; single characters are passed through as-is (so 'a', 'A', '1', '/'
    all work untouched)."""
    if not key:
        return key
    # Known modifier tokens — case-fold them even when the alias table
    # doesn't rewrite them, so 'Ctrl+A' stays a chord rather than xdotool's
    # unknown keysym 'Ctrl'.
    _modifiers = {"ctrl", "shift", "alt", "super", "meta", "cmd", "command",
                  "option", "opt", "win", "windows", "ctl", "control"}

    parts = key.replace("-", "+").split("+")
    out = []
    for p in parts:
        token = p.strip()
        if not token:
            continue
        if len(token) == 1:
            out.append(token)
            continue
        low = token.lower()
        if low in _KEY_ALIASES:
            out.append(_KEY_ALIASES[low])
        elif low in _modifiers:
            out.append(low)
        else:
            out.append(token)
    return "+".join(out)


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
        "Operate a real browser in an Xvfb display via pixel-level input.\n\n"
        "MANDATORY WORKFLOW (do not skip any step):\n"
        "  1. ALWAYS call `screenshot` before the FIRST action of a turn. Never\n"
        "     act on 'what I remember the page looked like' — the page may have\n"
        "     changed, the window may have moved, a dialog may have opened.\n"
        "  2. Reason about pixel coordinates from THAT screenshot.\n"
        "  3. Execute ONE mutating action (click, type, scroll, drag, key).\n"
        "  4. Call `screenshot` AGAIN to verify the action had the expected\n"
        "     effect. If it did not, do NOT repeat the same action with the\n"
        "     same coordinates — re-screenshot and re-plan.\n"
        "  5. Coordinates are absolute pixels in the virtual display; 0,0 is\n"
        "     top-left. Screen size is reported by `screen_info`.\n\n"
        "KEYBOARD:\n"
        "  - For plain text use `type_text`.\n"
        "  - For any key that is NOT a printable character (Backspace, Delete,\n"
        "    arrows, Enter, Escape) or any modifier chord (ctrl+a, cmd+v,\n"
        "    alt+Tab) use `press_key`. `type_text` will type the literal word\n"
        "    'Backspace' into the page if you call it with that string — that\n"
        "    is almost never what you want.\n"
        "  - To replace a field's contents use `clear_field` then `type_text`.\n"
        "  - Convenience tools `select_all`, `copy`, `paste`, `cut`, `undo`,\n"
        "    `redo`, `clipboard_set`, `clipboard_get` exist — prefer them over\n"
        "    raw chords when the action matches.\n\n"
        "DOM FAST-PATH (optional):\n"
        "  If the stack was started with CU_ENABLE_CDP=1, the `dom_*` tools\n"
        "  let you click / type / read via CSS selector — much faster and more\n"
        "  accurate than pixel clicks on complex DOM-heavy sites. Using them\n"
        "  flips `navigator.webdriver=true` for the session, so only enable\n"
        "  them on sites where anti-bot fingerprinting is not a concern."
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
    """Press a single key or chord. Case-insensitive names + aliases are
    normalised automatically — `Backspace`, `backspace`, `BackSpace` all work;
    `cmd+a`, `command-a`, `ctrl+a` all resolve; `meta`/`win`/`windows`/`cmd`
    map to the Super key.

    Common examples:
      letters / digits : "a", "A", "1", "/"
      navigation       : "Return", "Escape", "Tab", "Backspace", "Delete",
                         "Home", "End", "PageUp", "PageDown",
                         "Up", "Down", "Left", "Right"
      chords           : "ctrl+a", "ctrl+c", "ctrl+v", "ctrl+x", "ctrl+z",
                         "ctrl+shift+t", "alt+Left", "alt+F4",
                         "ctrl+BackSpace"  (delete previous word)
    """
    normalized = _normalize_key(key)
    _xdo("key", "--clearmodifiers", "--delay", "20", normalized)
    return f"pressed {normalized}" + (f" (from '{key}')" if normalized != key else "")


@mcp.tool()
def hold_key(key: str, ms: int = 500) -> str:
    """Hold a key down for ms milliseconds, then release. Same key naming
    rules as `press_key`."""
    normalized = _normalize_key(key)
    _xdo("keydown", normalized)
    try:
        time.sleep(max(0, ms) / 1000.0)
    finally:
        _xdo("keyup", normalized)
    return f"held {normalized} {ms}ms"


@mcp.tool()
def clear_field() -> str:
    """Select all text in the focused widget and delete it. Handy before
    `type_text` when you need to replace a field's contents rather than append."""
    _xdo("key", "--clearmodifiers", "ctrl+a")
    time.sleep(0.05)
    _xdo("key", "--clearmodifiers", "Delete")
    return "cleared focused field"


@mcp.tool()
def select_all() -> str:
    """Select all content in the focused widget (ctrl+a)."""
    _xdo("key", "--clearmodifiers", "ctrl+a")
    return "selected all"


@mcp.tool()
def copy() -> str:
    """Copy the current selection to clipboard (ctrl+c)."""
    _xdo("key", "--clearmodifiers", "ctrl+c")
    return "copied"


@mcp.tool()
def paste() -> str:
    """Paste the clipboard into the focused widget (ctrl+v)."""
    _xdo("key", "--clearmodifiers", "ctrl+v")
    return "pasted"


@mcp.tool()
def cut() -> str:
    """Cut the current selection to clipboard (ctrl+x)."""
    _xdo("key", "--clearmodifiers", "ctrl+x")
    return "cut"


@mcp.tool()
def undo() -> str:
    """Undo the last edit in the focused widget (ctrl+z)."""
    _xdo("key", "--clearmodifiers", "ctrl+z")
    return "undo"


@mcp.tool()
def redo() -> str:
    """Redo the last undone edit (ctrl+shift+z)."""
    _xdo("key", "--clearmodifiers", "ctrl+shift+z")
    return "redo"


@mcp.tool()
def clipboard_set(text: str) -> str:
    """Put text on the system clipboard (useful when `type_text` would be too
    slow, or when inserting characters xdotool cannot synthesise).

    Uses xclip if available, otherwise xsel. Then paste with the `paste` tool."""
    for prog in (["xclip", "-selection", "clipboard"], ["xsel", "-b", "-i"]):
        if subprocess.run(["which", prog[0]], capture_output=True).returncode == 0:
            p = subprocess.Popen(prog, stdin=subprocess.PIPE, env=_env())
            p.communicate(text.encode("utf-8"))
            if p.returncode == 0:
                return f"clipboard_set {len(text)} char(s) via {prog[0]}"
    raise RuntimeError("neither xclip nor xsel is installed — run setup.sh again")


@mcp.tool()
def clipboard_get() -> str:
    """Read the current clipboard text."""
    for prog in (["xclip", "-selection", "clipboard", "-o"], ["xsel", "-b", "-o"]):
        if subprocess.run(["which", prog[0]], capture_output=True).returncode == 0:
            p = subprocess.run(prog, capture_output=True, env=_env(), timeout=5)
            if p.returncode == 0:
                return p.stdout.decode("utf-8", "replace")
    raise RuntimeError("neither xclip nor xsel is installed — run setup.sh again")


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


def _maybe_register_dom_tools() -> None:
    """If CU_ENABLE_CDP=1 and Chrome has a DevTools port reachable, register
    the `dom_*` tools. Silent no-op otherwise — no breakage on setups that
    never opted in."""
    if os.environ.get("CU_ENABLE_CDP", "").strip() not in ("1", "true", "yes"):
        return
    try:
        from hermes_computer_use import dom
        n = dom.register(mcp)
        _log(f"[OK] DOM fast-path enabled ({n} dom_* tools registered)")
    except Exception as e:
        _log(f"[WARN] CU_ENABLE_CDP set but DOM tools failed to register: {e}")


def main() -> None:
    """Entry point for `python -m hermes_computer_use` and the `hermes-computer-use` console script."""
    try:
        _require("xdotool")
        _require("Xvfb")
    except RuntimeError as e:
        _log(f"[FATAL] {e}")
        sys.exit(2)
    _maybe_register_dom_tools()
    _log(f"[OK] computer-use MCP ready (DISPLAY={DISPLAY}, {WIDTH}x{HEIGHT})")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
