# Changelog

All notable changes to this project will be documented in this file. The format
follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- `examples/demo_prompts.md` — ten graduated test prompts including a 5-hop
  Google → external-site → SSO-login flow.
- `docs/ARCHITECTURE.md`, `docs/TROUBLESHOOTING.md`, `docs/SECURITY.md`.

[Unreleased]: https://github.com/Noah3521/hermes-computer-use/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Noah3521/hermes-computer-use/releases/tag/v0.1.0
