"""Unit tests that don't require a running X display."""
from __future__ import annotations


def test_version_exposed():
    import hermes_computer_use

    assert isinstance(hermes_computer_use.__version__, str)
    parts = hermes_computer_use.__version__.split(".")
    assert len(parts) >= 2
    assert all(p.isdigit() for p in parts[:2])


def test_server_imports_and_registers_tools():
    """Import should succeed even if xdotool/Xvfb are missing — those are
    runtime deps checked in `main()`, not at import time."""
    from hermes_computer_use import server

    assert hasattr(server, "mcp"), "FastMCP instance must be exported as `mcp`"
    assert hasattr(server, "main"), "entry point `main` must be defined"


def test_tool_surface_expected():
    """Guard against accidental tool removal. Add new tools here when you add them."""
    from hermes_computer_use import server

    # Each @mcp.tool() leaves a module-level function.
    expected = {
        "back",
        "close_tab",
        "cursor_position",
        "double_click",
        "drag",
        "forward",
        "hold_key",
        "left_click",
        "middle_click",
        "move",
        "new_tab",
        "open_url",
        "press_key",
        "reload",
        "right_click",
        "run_shell",
        "screen_info",
        "screenshot",
        "scroll",
        "type_text",
        "wait",
    }
    actual = {name for name in dir(server) if not name.startswith("_") and callable(getattr(server, name))}
    missing = expected - actual
    assert not missing, f"tools removed without changelog entry: {missing}"
