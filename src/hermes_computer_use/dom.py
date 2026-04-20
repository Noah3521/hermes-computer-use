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
    """Pick the most relevant page target exposed by Chrome's DevTools.

    Skip internal `chrome://` / `devtools://` targets (omnibox popups, the
    DevTools UI itself, extension pages) — they are type=page but not what
    the user means. Prefer a target that is marked `attached=false` (i.e.
    no other DevTools client is already in control)."""
    with urllib.request.urlopen(f"http://127.0.0.1:{CDP_PORT}/json", timeout=2) as r:
        targets = json.loads(r.read())
    pages = [t for t in targets if t.get("type") == "page"]
    if not pages:
        raise RuntimeError("no page target exposed by Chrome DevTools")
    externals = [
        t for t in pages
        if not t.get("url", "").startswith(("chrome://", "chrome-extension://",
                                              "devtools://", "edge://"))
    ]
    candidates = externals or pages
    # A non-attached target is a fresh client slot — prefer those to avoid
    # fighting an existing DevTools session over the same socket.
    candidates.sort(key=lambda t: t.get("attached", False))
    return candidates[0]["webSocketDebuggerUrl"]


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


def _capture_events(
    enable_commands: list[tuple[str, dict]],
    event_methods: set[str],
    duration_ms: int,
    body_url_filter=None,
    max_body_bytes: int = 65_536,
) -> tuple[list[dict], dict[str, str]]:
    """Hold a CDP WebSocket open for `duration_ms`, enable the requested
    domains, and collect every event whose `method` is in `event_methods`.

    If `body_url_filter` is a callable `(url: str) -> bool`, track each
    request's URL (from `Network.requestWillBeSent`) and — when its
    `Network.loadingFinished` arrives — fire `Network.getResponseBody` on
    the same WS session for every request whose URL matches the filter.
    Bodies larger than `max_body_bytes` are dropped.

    Returns `(events, bodies_by_request_id)`."""
    try:
        from websocket import create_connection
    except ImportError as e:
        raise RuntimeError("install websocket-client: pip install websocket-client") from e

    import time as _t

    ws_url = _active_target_ws()
    ws = create_connection(ws_url, timeout=5)
    captured: list[dict] = []
    bodies: dict[str, str] = {}
    pending_body_calls: dict[int, str] = {}
    url_by_rid: dict[str, str] = {}
    try:
        next_id = 1000
        for method, params in enable_commands:
            ws.send(json.dumps({"id": next_id, "method": method, "params": params}))
            next_id += 1

        deadline = _t.time() + duration_ms / 1000.0
        ws.settimeout(0.25)
        # Drain a bit after the window so late body replies arrive.
        extra_drain = 1.0
        while _t.time() < deadline + extra_drain:
            if _t.time() > deadline and not pending_body_calls:
                break
            try:
                raw = ws.recv()
            except Exception:
                continue
            try:
                msg = json.loads(raw)
            except Exception:
                continue

            if "id" in msg and msg["id"] in pending_body_calls:
                rid = pending_body_calls.pop(msg["id"])
                res = msg.get("result", {})
                body = res.get("body", "")
                if res.get("base64Encoded"):
                    import base64 as _b64
                    try:
                        body = _b64.b64decode(body).decode("utf-8", errors="replace")
                    except Exception:
                        body = f"[binary body, {len(body)} base64 chars]"
                if len(body) <= max_body_bytes:
                    bodies[rid] = body
                continue
            if "id" in msg:
                continue  # response to enable commands

            method_name = msg.get("method")

            # Track URLs so we can decide whether to fetch bodies.
            if body_url_filter is not None and method_name == "Network.requestWillBeSent":
                rid = msg["params"].get("requestId")
                url = msg["params"].get("request", {}).get("url", "")
                if rid and url:
                    url_by_rid[rid] = url

            if method_name in event_methods:
                captured.append(msg)
                if (body_url_filter is not None
                        and method_name == "Network.loadingFinished"
                        and _t.time() < deadline):
                    rid = msg["params"].get("requestId")
                    url = url_by_rid.get(rid, "")
                    if rid and url and body_url_filter(url):
                        ws.send(json.dumps({
                            "id": next_id,
                            "method": "Network.getResponseBody",
                            "params": {"requestId": rid},
                        }))
                        pending_body_calls[next_id] = rid
                        next_id += 1
    finally:
        ws.close()
    return captured, bodies


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

    @mcp.tool()
    def network_capture(
        duration_ms: int = 5000,
        url_contains: str = "",
        include_bodies: bool = False,
        max_body_bytes: int = 65_536,
    ) -> str:
        """Capture Chrome's HTTP traffic for duration_ms milliseconds.

        Returns a JSON array of request summaries with the shape
            {request_id, method, url, status, mime_type, size_bytes,
             duration_ms, body?}

        Set `url_contains` to filter by substring (e.g. "api/" to only see
        your app's XHR/fetch calls, not pixels). Empty = every request.

        Set `include_bodies=True` to fetch response bodies for matching
        requests during the same CDP session — required because Chrome's
        requestIds are session-scoped and cannot be resolved from a later
        call. Bodies larger than `max_body_bytes` (default 64 KB) are
        omitted from the result. Binary content is base64-decoded with
        `errors='replace'`.

        Trigger the page action that should produce the requests AFTER
        calling this tool — the capture window is synchronous."""
        url_filter_fn = (lambda u: url_contains in u) if url_contains else (lambda u: True)

        events, bodies = _capture_events(
            enable_commands=[("Network.enable", {})],
            event_methods={
                "Network.requestWillBeSent",
                "Network.responseReceived",
                "Network.loadingFinished",
                "Network.loadingFailed",
            },
            duration_ms=max(100, duration_ms),
            body_url_filter=url_filter_fn if include_bodies else None,
            max_body_bytes=max_body_bytes,
        )

        # Correlate events by requestId first.
        reqs: dict[str, dict] = {}
        for ev in events:
            p = ev["params"]
            rid = p.get("requestId")
            if not rid:
                continue
            r = reqs.setdefault(rid, {})
            method = ev["method"]
            if method == "Network.requestWillBeSent":
                req = p.get("request", {})
                r["method"] = req.get("method", "?")
                r["url"] = req.get("url", "")
                r["resource_type"] = p.get("type", "Other")
                r["_start"] = p.get("timestamp", 0)
            elif method == "Network.responseReceived":
                resp = p.get("response", {})
                r["status"] = resp.get("status")
                r["mime_type"] = resp.get("mimeType")
                r["from_cache"] = resp.get("fromDiskCache", False)
            elif method == "Network.loadingFinished":
                if "_start" in r:
                    r["duration_ms"] = int((p.get("timestamp", 0) - r["_start"]) * 1000)
                r["size_bytes"] = int(p.get("encodedDataLength", 0))
            elif method == "Network.loadingFailed":
                r["error"] = p.get("errorText", "unknown")

        out = []
        for rid, r in reqs.items():
            if "url" not in r:
                continue
            if url_contains and url_contains not in r["url"]:
                continue
            r.pop("_start", None)
            r["request_id"] = rid
            if include_bodies and rid in bodies:
                r["body"] = bodies[rid]
            out.append(r)
        out.sort(key=lambda x: (x.get("resource_type", ""), x.get("url", "")))
        return json.dumps(out, ensure_ascii=False, indent=2)

    @mcp.tool()
    def console_messages(duration_ms: int = 3000) -> str:
        """Capture console.log / warn / error / info and uncaught exceptions
        from the page for duration_ms milliseconds. Returns JSON array of
            {level, text, source?, line?, url?}

        Useful for diagnosing page-side errors without attaching a human to
        DevTools."""
        events, _ = _capture_events(
            enable_commands=[("Runtime.enable", {}), ("Log.enable", {})],
            event_methods={
                "Runtime.consoleAPICalled",
                "Log.entryAdded",
                "Runtime.exceptionThrown",
            },
            duration_ms=max(100, duration_ms),
        )

        out = []
        for ev in events:
            p = ev["params"]
            if ev["method"] == "Runtime.consoleAPICalled":
                args = [
                    str(a.get("value", a.get("description", "")))
                    for a in p.get("args", [])
                ]
                out.append({"level": "console." + p.get("type", "log"),
                            "text": " ".join(args)})
            elif ev["method"] == "Log.entryAdded":
                e = p.get("entry", {})
                out.append({"level": e.get("level", "log"),
                            "source": e.get("source"),
                            "text": e.get("text"),
                            "url": e.get("url")})
            elif ev["method"] == "Runtime.exceptionThrown":
                ed = p.get("exceptionDetails", {})
                ex = ed.get("exception", {}) or {}
                out.append({"level": "exception",
                            "text": ed.get("text", "") + " " + ex.get("description", ""),
                            "line": ed.get("lineNumber"),
                            "url": ed.get("url")})
        return json.dumps(out, ensure_ascii=False, indent=2)

    return 8
