"""Optional DOM fast-path tools via Chrome DevTools Protocol.

Registered only when `CU_ENABLE_CDP=1` is set at server start. Using any of
these tools causes Chrome to attach a DevTools client; this sets
`navigator.webdriver=true` for the duration of the session, which defeats the
main selling point of this project on sites that fingerprint Chrome.

Trade-off: on DOM-heavy pages where vision grounding is slow or fragile
(SPA dashboards with dynamic layouts, long forms, deeply nested shadow roots)
these tools are an order of magnitude faster and more accurate. On sites
guarded by Cloudflare / Kasada / reCAPTCHA v3, leave them off.

Enable by starting Chrome with --remote-debugging-port=9222 (see
scripts/display.sh for a commented example) and exporting
CU_ENABLE_CDP=1 before running the MCP server.
"""
from __future__ import annotations

import json
import os
import urllib.request
from typing import Any

CDP_PORT = int(os.environ.get("CU_CDP_PORT", "9222"))


def _cdp_available() -> bool:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json/version", timeout=1) as r:
            return r.status == 200
    except Exception:
        return False


def _active_target_ws() -> str:
    with urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json", timeout=2) as r:
        targets = json.loads(r.read())
    pages = [t for t in targets if t.get("type") == "page"]
    if not pages:
        raise RuntimeError("no page target exposed by Chrome DevTools")
    return pages[0]["webSocketDebuggerUrl"]


def _send(method: str, params: dict | None = None) -> Any:
    """Send a single CDP command and return the result. One call per request —
    we open/close the WS each time to keep this small."""
    try:
        from websocket import create_connection  # websocket-client
    except ImportError as e:
        raise RuntimeError(
            "The DOM fast-path requires `websocket-client`. "
            "Install with: pip install websocket-client"
        ) from e

    ws_url = _active_target_ws()
    ws = create_connection(ws_url, timeout=5)
    try:
        msg = {"id": 1, "method": method, "params": params or {}}
        ws.send(json.dumps(msg))
        reply = json.loads(ws.recv())
        if "error" in reply:
            raise RuntimeError(f"CDP error on {method}: {reply['error']}")
        return reply.get("result", {})
    finally:
        ws.close()


def _eval(expression: str) -> Any:
    result = _send("Runtime.evaluate", {
        "expression": expression,
        "returnByValue": True,
        "awaitPromise": True,
    })
    r = result.get("result", {})
    if r.get("subtype") == "error":
        raise RuntimeError(f"page JS error: {r.get('description', '?')}")
    return r.get("value")


def register(mcp) -> int:
    """Add dom_* tools to the given FastMCP instance. Returns the number of
    tools registered (0 if CDP is unreachable)."""
    if not _cdp_available():
        return 0

    @mcp.tool()
    def dom_click(selector: str) -> str:
        """Click the element matching the CSS selector. Faster and more
        reliable than pixel clicks on DOM-heavy pages — at the cost of
        flipping `navigator.webdriver=true` for the session. Fails if no
        element matches or more than one matches."""
        js = f"""
        (() => {{
            const els = document.querySelectorAll({json.dumps(selector)});
            if (els.length === 0) throw new Error("no match for " + {json.dumps(selector)});
            if (els.length > 1) throw new Error("multiple matches: " + els.length);
            els[0].scrollIntoView({{behavior: 'instant', block: 'center'}});
            els[0].click();
            return "ok";
        }})()
        """
        _eval(js)
        return f"dom_click {selector!r}"

    @mcp.tool()
    def dom_type(selector: str, text: str) -> str:
        """Set the value of an input / textarea / contenteditable matching the
        selector, then fire a proper input + change event so React/Vue/Svelte
        see the update."""
        js = f"""
        (() => {{
            const el = document.querySelector({json.dumps(selector)});
            if (!el) throw new Error("no match for " + {json.dumps(selector)});
            el.focus();
            if ('value' in el) {{
                const setter = Object.getOwnPropertyDescriptor(
                    el.tagName === 'TEXTAREA' ? HTMLTextAreaElement.prototype
                                              : HTMLInputElement.prototype,
                    'value'
                ).set;
                setter.call(el, {json.dumps(text)});
            }} else {{
                el.textContent = {json.dumps(text)};
            }}
            el.dispatchEvent(new Event('input', {{bubbles: true}}));
            el.dispatchEvent(new Event('change', {{bubbles: true}}));
            return "ok";
        }})()
        """
        _eval(js)
        return f"dom_type {selector!r} ← {len(text)} chars"

    @mcp.tool()
    def dom_query(selector: str, attribute: str | None = None) -> str:
        """Read text content (default) or a named attribute from the first
        element matching the selector. Useful for verifying page state
        without a screenshot round-trip."""
        if attribute:
            js = f"""
            (() => {{
                const el = document.querySelector({json.dumps(selector)});
                return el ? el.getAttribute({json.dumps(attribute)}) : null;
            }})()
            """
        else:
            js = f"""
            (() => {{
                const el = document.querySelector({json.dumps(selector)});
                return el ? (el.innerText || el.textContent || "") : null;
            }})()
            """
        val = _eval(js)
        if val is None:
            raise RuntimeError(f"no element matches {selector!r}")
        return str(val)

    @mcp.tool()
    def dom_exists(selector: str) -> bool:
        """True if at least one element matches the selector. Zero-round-trip
        way to check whether a modal, toast, or flash message has appeared."""
        return bool(_eval(f"document.querySelectorAll({json.dumps(selector)}).length > 0"))

    @mcp.tool()
    def dom_wait(selector: str, timeout_ms: int = 5000) -> str:
        """Poll until the selector matches at least one visible element, or
        time out. Cheaper than screenshot-polling for 'wait until the save
        button enables'-style flows."""
        js = f"""
        new Promise((resolve, reject) => {{
            const deadline = Date.now() + {timeout_ms};
            const tick = () => {{
                const el = document.querySelector({json.dumps(selector)});
                if (el && el.offsetParent !== null) return resolve("ready");
                if (Date.now() > deadline) return reject(new Error("timeout"));
                setTimeout(tick, 50);
            }};
            tick();
        }})
        """
        _eval(js)
        return f"dom_wait {selector!r} ready"

    @mcp.tool()
    def dom_eval(expression: str) -> str:
        """Evaluate arbitrary JavaScript in the page context and return the
        stringified result. Powerful and correspondingly dangerous — strip
        this tool when exposing the MCP to an untrusted agent."""
        val = _eval(expression)
        return json.dumps(val, ensure_ascii=False)

    return 6
