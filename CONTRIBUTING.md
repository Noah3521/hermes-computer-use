# Contributing

Thanks for considering a contribution. This project intentionally stays small and unopinionated — before opening a large PR please file an issue describing the idea.

## Development setup

```bash
git clone https://github.com/Noah3521/hermes-computer-use.git
cd hermes-computer-use

# Install the package + dev tools in editable mode
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev,novnc]"

# Install the runtime pieces (Xvfb, xdotool, Chrome) if you want to test end-to-end
bash scripts/setup.sh
```

Run the MCP server locally (requires Xvfb on `:99`):
```bash
bash scripts/display.sh start
python -m hermes_computer_use      # stdio MCP, stays attached
```

Verify with the smoke script:
```bash
python examples/smoke_test.py
```

## Code style

- `ruff check .` must pass.
- Keep tool functions **pure and small** — one action, one side-effect. The LLM loop handles orchestration.
- No new dependencies without a justification in the PR description.
- Docstrings on every `@mcp.tool()` — they become the agent-facing documentation.

## Testing

- `pytest` runs unit tests that don't need a display.
- End-to-end tests (screenshots, clicks) require Xvfb and are not run in CI by default. Label them `@pytest.mark.e2e` and skip by default.

## Scope

### Welcome

- **New MCP tools** that cover legitimate browser/desktop operations not yet represented (audio routing, file drag-drop, multi-monitor, clipboard, etc.).
- **Hybrid fast paths.** Pixel automation is the default, but a PR that exposes an opt-in DOM / CDP helper — e.g. `dom_fast_click(selector)` — is fine when it is *additive* and users can still fall back to the pixel tools on sites where the DOM path is risky or fingerprintable. The interesting design question is *which sites can safely use the fast path*; a heuristic or per-site toggle around that belongs here.
- Accessibility tree (AT-SPI) side channels for more reliable grounding.
- Recording / replay tooling, better observability, Docker packaging, alternative display backends.
- **Docs, translations, and examples.** The README is already mirrored in 日本語 / 中文 / 한국어 — keep them honest if you change the canonical English.

### Think twice

- **`navigator.webdriver=true` or a live CDP port by default.** The repo's selling point is emitting no abnormal signals. Anything that flips those flags globally needs a clear off-by-default design. Opt-in is fine; default-on defeats the core thesis.
- OCR bundled in the server. The agent's vision model is the OCR; shipping an extra engine usually adds weight without improving outcomes.
- Anti-detection arms-race patches. Stock Chrome + stock X input is deliberately boring — PRs that start tracking and patching specific detectors will sprawl quickly.
- **OS support beyond WSL2 Ubuntu.** macOS / native Linux / Windows all need their own input stacks; a best-effort port is usually worse than a dedicated fork.

## Reporting security issues

Do not file public issues for anything that could let an attacker escape the agent sandbox or leak the user's data. Email the maintainer (see `pyproject.toml`).
