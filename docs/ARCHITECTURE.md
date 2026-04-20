# Architecture

```
 ┌─────────────────────────── hermes-agent  (or any MCP client) ───────────────────────────┐
 │  gpt-5.4 via openai-codex                                                              │
 │    │                                                                                    │
 │    │  stdio MCP (JSON-RPC)                                                              │
 │    ▼                                                                                    │
 │  hermes_computer_use.server  ── 21 tools: screenshot / click / type / drag / scroll /... │
 │    │                                                                                    │
 │    │  subprocess                                                                        │
 │    ▼                                                                                    │
 │  xdotool · scrot · google-chrome          ← OS-level input + capture, no CDP            │
 │    │                                                                                    │
 │    ▼                                                                                    │
 │  Xvfb :99  (1440x900 software framebuffer)                                              │
 │    ▲                                                                                    │
 │    │   RFB                                                                              │
 │    │                                                                                    │
 │  x11vnc :5900 ─── native VNC clients (TigerVNC, RealVNC)                                │
 │    ▲                                                                                    │
 │    │   WebSocket                                                                        │
 │    │                                                                                    │
 │  websockify/noVNC :6080 ── http://localhost:6080/vnc.html  ← browser-based viewer       │
 └────────────────────────────────────────────────────────────────────────────────────────┘
```

## Why this stack

| Layer | Chosen | Rejected | Why |
|---|---|---|---|
| Display | **Xvfb** | WSLg, Xorg-dummy | Fully headless, reproducible, no GPU dependency |
| Input | **xdotool** (default), ydotool optional | Playwright, CDP, Selenium | OS-level — `navigator.webdriver=undefined`, no JS hooks |
| Capture | **scrot** (fallback ImageMagick) | Chrome screencast API | No need for CDP; any X11 window |
| WM | **fluxbox** | none, dwm | Lightweight, gives Chrome proper focus handling |
| Observer | **x11vnc + noVNC** | vnc only | Browser reachable from anywhere (6080) AND native client (5900) |
| Lifecycle | **systemd user services** | nohup, bash scripts | Crash recovery, boot persistence, clean shutdown |

## Tool surface (21)

| Category | Tools |
|---|---|
| Status | `screen_info`, `cursor_position` |
| Capture | `screenshot` (base64 PNG) |
| Pointer | `move`, `left_click`, `right_click`, `double_click`, `middle_click`, `drag`, `scroll` |
| Keyboard | `type_text`, `press_key`, `hold_key` |
| Timing | `wait` |
| Browser | `open_url`, `new_tab`, `close_tab`, `back`, `forward`, `reload` |
| Escape hatch | `run_shell` |

## Human-likeness knobs

- `CU_MOVE_STEPS` — number of interpolation steps for `move(human=True)` and `drag` (default 18)
- `CU_KEY_DELAY_MS` — inter-keystroke delay for `type_text` (default 25)
- Internal eased-cubic interpolation with jitter to avoid straight-line mouse paths
- `CU_INPUT=ydotool` switches input to `/dev/uinput` kernel layer for stronger HID fidelity

## DOM fast-path (optional, off by default)

Pixel automation is the default because it makes the browser fingerprint-indistinguishable from stock Chrome. There are tasks where that is wasteful — operating a known-good SPA dashboard, filling a long form, asserting on nested DOM state — and the `screenshot → vision → click` round trip dominates wall time.

Set `CU_ENABLE_CDP=1` before `scripts/display.sh` start and the server registers `dom_click(selector)`, `dom_type(selector, text)`, `dom_query(selector)`, `dom_exists(selector)`, `dom_wait(selector, ms)`, `dom_eval(js)` via Chrome's DevTools Protocol. These are often 5–50× faster than the equivalent pixel flow on a dynamic SPA.

**The trade-off is real**: attaching a CDP client sets `navigator.webdriver=true` for the session. On Cloudflare Bot Fight Mode / Kasada / reCAPTCHA-v3-fingerprinted sites that is enough to get flagged. The intended model is "use pixel mode by default; enable CDP per-site for flows you know aren't fingerprinted, then turn it off again." Not "leave CDP on forever."

## What it doesn't do by default

- No CDP / DevTools Protocol unless `CU_ENABLE_CDP=1` is explicitly set.
- No `navigator.webdriver` flag, no Selenium marker, no CDP port open.
- DOM queries and CSS selectors are available via the opt-in `dom_*` tools only — everything else is pixel-grounded.
- No built-in anti-detection patches beyond clean Chrome defaults — "zero abnormal signals" is what keeps detection rates low; OCR, CAPTCHA solvers, and evasion patches live in the agent, not the server.

## Failure modes

- **Xvfb crashes** → systemd restarts computer-use.service
- **Chrome crashes** → service reports active/exited but Chrome is gone. Restart with `systemctl --user restart computer-use.service`
- **Loopback port conflict** (e.g. WSL wslrelay) → `scripts/display.sh start` errors early with a clear message; change `CU_DISPLAY` + `CU_VNC_PORT`
- **Coordinate drift** → always screenshot + verify, never assume success
