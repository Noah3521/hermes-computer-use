# Changelog

All notable changes to this project will be documented in this file. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed

- **Silent backspace / keyboard-shortcut failures.** `xdotool key Backspace`
  exits with code 0 and a `"No such key name"` warning on stderr, so the
  previous `_xdo` wrapper reported success while the key was silently
  dropped. `_xdo` now inspects stderr for that warning and raises; users
  see an explicit error instead of a mystery no-op.
- **Key-name case sensitivity.** `press_key` / `hold_key` now normalise
  common spellings via `_normalize_key`: `Backspace` → `BackSpace`,
  `ctrl-a` → `ctrl+a`, `cmd+c` / `win+r` / `meta+l` → `super+*`,
  `option+Left` → `alt+Left`, `Ctrl+A` → `ctrl+A`.

### Added

- **Keyboard convenience tools** — `clear_field`, `select_all`, `copy`,
  `paste`, `cut`, `undo`, `redo`, `clipboard_set`, `clipboard_get`.
  Removes the need for agents to remember raw chords or get the key-
  naming right.
- **`clipboard_set` / `clipboard_get`** use xclip or xsel (installed by
  `setup.sh`). Useful for injecting text faster than `type_text` can
  synthesise, or for characters xdotool cannot produce.
- **Optional DOM fast-path** — gated behind `CU_ENABLE_CDP=1`, exposes
  eight new tools: `dom_click`, `dom_type`, `dom_query`, `dom_exists`,
  `dom_wait`, `dom_eval`, `network_capture`, `console_messages`. Uses
  Chrome's DevTools Protocol via `websocket-client` (new `[dom]` extra).
  Off by default because it flips `navigator.webdriver=true`.
- **`network_capture(duration_ms, url_contains, include_bodies, max_body_bytes)`**
  — synchronously records every HTTP request Chrome makes during the window
  and returns JSON summaries with method / url / status / mime / size /
  duration. With `include_bodies=True`, response bodies matching
  `url_contains` are inlined (fetched on the same CDP session to avoid
  the requestId-session-scope problem where bodies cannot be retrieved
  from a later call).
- **`console_messages(duration_ms)`** — captures `console.log/warn/error/info`
  and uncaught JS exceptions into a structured list.
- **Tool-surface guard test** (`tests/test_import.py`) expanded to cover
  the new keyboard tools; new `tests/test_key_normalize.py` parameterises
  the alias table against real-world misspellings.
- **Server instructions strengthened** — the FastMCP `instructions`
  string now enforces a screenshot-before-action / screenshot-after-
  action loop, documents the keyboard rules, and explains when to reach
  for the DOM fast-path instead of pixel clicks.

### Changed

- `scripts/setup.sh` now installs `xclip` and `xsel` for clipboard tools.
- `scripts/display.sh` accepts `CU_ENABLE_CDP=1` and passes
  `--remote-debugging-port=$CU_CDP_PORT` (default 9222),
  `--remote-allow-origins=*` (required by Chrome 123+ to accept our
  WebSocket handshake), and `--remote-debugging-address=127.0.0.1`
  (keep the port localhost-only even with wildcard origins) to Chrome.
- `_active_target_ws` skips `chrome://` / `chrome-extension://` /
  `devtools://` targets (omnibox popups, DevTools UI) and prefers
  unattached pages so DOM tools land on the real tab.
- CONTRIBUTING scope: hybrid DOM / CDP paths are welcome when they are
  additive and opt-in; blanket "no DOM" rule removed.

## [0.1.0] - 2026-04-20

### Added
- Initial public release.
- `hermes_computer_use.server` MCP server with 21 tools: screenshot, click
  family, drag, scroll, type, press/hold key, wait, browser nav, run_shell.
- Human-like mouse interpolation (eased cubic + jitter) on `move(human=True)`
  and `drag`.
- `CU_INPUT=ydotool` opt-in for kernel-level (`/dev/uinput`) input injection.
- `scripts/setup.sh` — one-shot Linux dependency installer (Xvfb, xdotool,
  ydotool, Chrome, CJK fonts, uinput enablement).
- `scripts/display.sh` — `start|stop|restart|status` lifecycle for the Xvfb
  stack, `setsid`-detached so it survives WSL session teardown.
- `scripts/install-novnc.sh` — optional browser-based viewer on `:6080`.
- `systemd/` user services for `computer-use` and `novnc` with `RemainAfterExit`
  + `Restart=on-failure` + proper `After`/`Requires` ordering.
- `examples/smoke_test.py` — verifies the MCP server end-to-end over stdio.
- `examples/demo_prompts.md` — ten graduated test prompts, headlined by a
  Google search demo (type `snp500`, read the live index card).
- Documentation: `README.md`, `SECURITY.md`, `CONTRIBUTING.md`,
  `CODE_OF_CONDUCT.md`, `docs/WSL_SETUP.md`, `docs/ARCHITECTURE.md`,
  `docs/TROUBLESHOOTING.md`, `docs/FAQ.md`, `docs/CAPTCHA.md`.
- Hero asset: `docs/assets/demo-snp500.gif` — actual recording of the
  headline demo. Fingerprint evidence: `docs/assets/demo-sannysoft.png`.
- GitHub plumbing: CI (ruff + pytest on 3.11/3.12), PyPI Trusted Publisher
  workflow, issue/PR templates.

[Unreleased]: https://github.com/Noah3521/hermes-computer-use/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Noah3521/hermes-computer-use/releases/tag/v0.1.0

