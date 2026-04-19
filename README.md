# hermes-computer-use

**Pixel-level browser automation MCP server.** Gives an LLM client (hermes-agent, Claude Code, Codex, or any MCP-speaking agent) 21 tools to drive a real Chrome browser running in an Xvfb display — screenshots as vision input, OS-level mouse/keyboard as output. No CDP. No `navigator.webdriver`. No DOM shortcuts.

Mirrors the architecture of [anthropic-quickstarts/computer-use-demo](https://github.com/anthropics/anthropic-quickstarts) but exposes the primitives over stdio MCP so you can pair it with any agent runtime and any vision-capable model. Originally built to wire into [hermes-agent](https://github.com/rossgray/hermes-agent) running `openai-codex` as its brain.

## Highlights

- **21 tools**: screenshot, click/drag/scroll, type, chords, browser nav, shell.
- **Clean Chrome**: no Selenium/Playwright markers. Passes `bot.sannysoft.com`.
- **Human-like pointer**: eased-cubic interpolation + jitter on `move`/`drag`.
- **Live observer**: x11vnc on `:5900` for native VNC clients + noVNC on `:6080` for any browser.
- **systemd user services**: boot-persistent, crash-recovering, linger-aware.
- **~900 LOC** of Python for the MCP server. Easy to audit, easy to fork.

## Architecture

```
hermes-agent ──stdio MCP──▶ computer_use_mcp.py ──subprocess──▶ xdotool / scrot
                                                                       │
                                                                       ▼
                                                                   Xvfb :99
                                                                       │
                                                   ┌───────────────────┼────────────────┐
                                                   ▼                                    ▼
                                             x11vnc :5900                    websockify + noVNC :6080
                                        (native VNC clients)              (browser at /vnc.html)
```

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Requirements

- WSL2 Ubuntu 22.04+ (or any Linux with systemd-user sessions)
- Python 3.11+ with the `mcp` package importable
- apt packages (installed by `scripts/setup.sh`): `xvfb fluxbox x11vnc xdotool ydotool scrot imagemagick fonts-noto-cjk google-chrome-stable`

## Install

```bash
git clone https://github.com/<you>/hermes-computer-use.git ~/hermes-computer-use
cd ~/hermes-computer-use

# 1. System packages + Chrome (sudo required)
bash scripts/setup.sh

# 2. (Optional) Browser-based viewer
PYTHON=/path/to/your/agent/venv/bin/python bash scripts/install-novnc.sh

# 3. Install systemd user services
mkdir -p ~/.config/systemd/user
cp systemd/*.service ~/.config/systemd/user/
# Edit the ExecStart paths if you cloned somewhere other than ~/hermes-computer-use
sudo loginctl enable-linger $USER        # survive logout
systemctl --user daemon-reload
systemctl --user enable --now computer-use.service
systemctl --user enable --now novnc.service   # if step 2 was done
```

Verify:
```bash
systemctl --user status computer-use.service --no-pager
curl -I http://localhost:6080/vnc.html   # expect 200
```

## Wire to hermes-agent

Paste [`config/hermes.yaml.snippet`](config/hermes.yaml.snippet) into your `~/.hermes/config.yaml` under `mcp_servers:`, then:

```bash
hermes gateway run --replace
```

Hermes will expose the 21 tools to the model.

## Tools

| Category | Tools |
|---|---|
| Status | `screen_info`, `cursor_position` |
| Capture | `screenshot` (base64 PNG) |
| Pointer | `move`, `left_click`, `right_click`, `double_click`, `middle_click`, `drag`, `scroll` |
| Keyboard | `type_text`, `press_key`, `hold_key` |
| Timing | `wait` |
| Browser | `open_url`, `new_tab`, `close_tab`, `back`, `forward`, `reload` |
| Escape hatch | `run_shell` |

See [`computer_use_mcp.py`](computer_use_mcp.py) for signatures and semantics.

## Demo prompts

[`examples/demo_prompts.md`](examples/demo_prompts.md) ships ten prompts from smoke test to a 5-hop Google → external-site → SSO login flow that passes without any captcha. Open noVNC in a browser while the agent runs one and watch it work.

## Environment variables

| Var | Default | Meaning |
|---|---|---|
| `CU_DISPLAY` | `99` | X display number (Xvfb binds `:${CU_DISPLAY}`) |
| `CU_WIDTH` / `CU_HEIGHT` | `1440` / `900` | Virtual screen size |
| `CU_VNC_PORT` | `5900` | x11vnc listen port |
| `CU_STATE_DIR` | `/tmp/hermes-computer-use` | Logs, PID files, Chrome profile |
| `CU_PROFILE_DIR` | `$CU_STATE_DIR/chrome-profile` | Persistent Chrome profile dir |
| `CU_START_URL` | `about:blank` | First URL Chrome opens |
| `CU_INPUT` | `xdotool` | Set to `ydotool` for `/dev/uinput` input |
| `CU_KEY_DELAY_MS` | `25` | Inter-keystroke delay for `type_text` |
| `CU_MOVE_STEPS` | `18` | Interpolation steps for `move(human=True)` and `drag` |

## Troubleshooting

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md). Common gotchas:

- **`scrot: Can't open X display`** → Xvfb died; `systemctl --user restart computer-use.service`.
- **Chrome immediately exits** → check `chrome.log` for zygote errors; ensure `--no-sandbox --disable-dev-shm-usage` are both present.
- **Stack dies on logout** → `sudo loginctl enable-linger $USER`.
- **Google flags "unusual traffic"** → IP reputation, not behavioural. Prewarm cookies or use a residential proxy.

## Security

This is an LLM with hands. Read [docs/SECURITY.md](docs/SECURITY.md) before pointing it at anything you care about. Quick rules:

- Run in an isolated WSL distro.
- Strip `run_shell` if the agent doesn't need it.
- Don't persist real credentials in `$CU_PROFILE_DIR`.

## Why this vs Playwright?

| | Playwright/CDP | This |
|---|---|---|
| `navigator.webdriver` | `true` (detectable) | `undefined` |
| CDP endpoint open | Yes | No |
| DOM access | Direct (fast) | Screenshot only |
| Anti-bot bypass | Hard | Often passes by default |
| Brittleness to UI changes | Selector-bound | Pixel-grounded (drifts with layout, but not with selector renames) |
| Use case | Reliable known-DOM flows | Agents operating unfamiliar sites like a human |

Use Playwright when you own the site. Use this when you don't.

## License

MIT. See [LICENSE](LICENSE).
