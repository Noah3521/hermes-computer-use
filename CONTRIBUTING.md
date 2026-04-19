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

## Scope guardrails (things that don't belong here)

- DOM/CSS selectors or CDP wrappers. Use Playwright.
- OCR. Pass the screenshot to a vision model and let it reason.
- Anti-detection patches beyond stock Chrome flags. The thesis is "no abnormal signals" > "evasion".
- OS support other than Linux. macOS/Windows have very different input APIs; those deserve their own repo.

## Reporting security issues

Do not file public issues for anything that could let an attacker escape the agent sandbox or leak the user's data. Email the maintainer (see `pyproject.toml`).
