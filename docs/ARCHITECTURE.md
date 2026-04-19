# Architecture

```
 ┌─────────────────────────── hermes-agent (or any MCP client) ───────────────────────────┐
 │  gpt-5.4 via openai-codex                                                              │
 │    │                                                                                    │
 │    │  stdio MCP (JSON-RPC)                                                              │
 │    ▼                                                                                    │
 │  computer_use_mcp.py  ── 21 tools: screenshot / click / type / drag / scroll / ...      │
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

## What it doesn't do (by design)

- No CDP / DevTools Protocol
- No `navigator.webdriver` flag, no Selenium marker
- No DOM queries or CSS selectors — all grounding is via rendered pixels and optional vision models on the client
- No built-in anti-detection patches beyond clean Chrome defaults — the model of "zero abnormal signals" is what keeps detection rates low

## Failure modes

- **Xvfb crashes** → systemd restarts computer-use.service
- **Chrome crashes** → service reports active/exited but Chrome is gone. Restart with `systemctl --user restart computer-use.service`
- **Loopback port conflict** (e.g. WSL wslrelay) → `scripts/display.sh start` errors early with a clear message; change `CU_DISPLAY` + `CU_VNC_PORT`
- **Coordinate drift** → always screenshot + verify, never assume success
