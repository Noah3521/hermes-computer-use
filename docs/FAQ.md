# FAQ

### Why not just use Playwright?

You should, when you own the site. Playwright is faster, has a stable API, and is great for CI. **This project is for the other case**: when the site actively resists automation. Playwright launches Chrome with CDP attached and exposes `navigator.webdriver=true`, `window.cdc_*`, and dozens of other fingerprintable signals. That makes it a one-line fingerprint for any modern anti-bot stack (Cloudflare Bot Fight Mode, Kasada, Akamai, DataDome). This project launches stock Chrome and drives it via the X server — the browser is indistinguishable from one a human is using.

### Does it *really* bypass anti-bot?

For "nuisance" tiers (basic bot-detection scripts, Cloudflare Bot Fight Mode, reCAPTCHA v3 heuristics): **yes, in most cases**, because the stack emits no abnormal fingerprints. For "aggressive" tiers (hCaptcha enterprise, Kasada, residential-IP reputation checks on places like Ticketmaster): **not alone**. IP reputation dominates there, and no client-side stack fixes that — you need a residential proxy.

### Why is it macOS / native-Linux hostile?

The core Python (`server.py`) works anywhere Python + X11 + xdotool exist. The **scripts, systemd units, and docs** are tuned for WSL2's quirks (wslrelay, WSLg, interop PATH, VM teardown). Supporting every Linux + macOS doubles the maintenance. If you need macOS, look at Anthropic's Claude Desktop computer-use or Codex Computer Use — they use native macOS APIs.

### Why `--no-sandbox`?

Chrome's sandbox needs either `CLONE_NEWUSER` privileges or `CAP_SYS_ADMIN` to bootstrap its setuid/namespace sandbox. Inside WSL2 that's fragile. `--no-sandbox` is the documented workaround for sandboxed-container/WSL environments. The agent stack itself is your outer sandbox — run it in a disposable WSL distro (see [WSL_SETUP.md](WSL_SETUP.md#3-optional-but-recommended-dedicate-a-distro-to-this-project)).

### Can I run multiple browsers in parallel?

Yes. Give each its own display number and VNC port:
```bash
CU_DISPLAY=100 CU_VNC_PORT=5901 bash scripts/display.sh start
CU_DISPLAY=101 CU_VNC_PORT=5902 bash scripts/display.sh start
```
Each MCP server pointed at a different `CU_DISPLAY` will see its own Chrome.

### How accurate is the vision grounding?

Depends entirely on the model's vision capability. Large multimodal models (GPT-5 class, Claude Sonnet 4.6+) typically pinpoint buttons within ~5 pixels. Small inputs like radio buttons or 12px icons get missed ~10–20% of the time. The `screenshot → act → screenshot → verify` loop in prompts makes this self-correcting.

### Can I use a different model / client?

Yes. Anything that speaks [MCP](https://modelcontextprotocol.io/) over stdio works: Claude Desktop, Claude Code, Codex, `mcp-inspector`, custom runners. The examples reference hermes-agent because that's the test bed, not because of any coupling.

### Why ship `run_shell` if it's a liability?

Debugging. An agent that can't `ls /tmp/hermes-computer-use/chrome.log` when something misbehaves is nearly useless to iterate on. The convention is: **remove `run_shell` before production deployment**. See `SECURITY.md`.

### Will the ~5 min Chrome profile lock cause problems in parallel runs?

Yes, Chrome holds an exclusive lock on `$CU_PROFILE_DIR`. Use separate profiles per display:
```bash
CU_PROFILE_DIR=/tmp/hcu/profile-100 CU_DISPLAY=100 bash scripts/display.sh start
```

### Does the Chrome profile save passwords?

Yes, by default. **Do not store real credentials in `CU_PROFILE_DIR`.** Either use a throwaway account, or scrub the profile between runs:
```bash
rm -rf "$CU_PROFILE_DIR"
systemctl --user restart computer-use.service
```

### How do I see what the agent is doing, live?

Open `http://localhost:6080/vnc.html` in any browser while the agent runs. It's a real-time canvas of the Xvfb display.

### Can I record automation runs to video?

Not built in. Run `ffmpeg -y -video_size 1440x900 -f x11grab -i :99 out.mp4` in a side process. PRs welcome if someone wants a `recording` MCP tool.

### What happens if Chrome crashes mid-run?

The agent's next `screenshot` will return a blank frame. Chrome does not auto-restart by default. Wrap it in a supervisor or use `systemctl --user restart computer-use.service` before the next attempt.

### Is this affected by WSL's "mirrored" networking mode?

It works in both NAT and mirrored modes. Mirrored tends to be friendlier for reaching `localhost:6080` from Windows without quirks. Both supported.

### Do I need a GPU?

No. Xvfb is purely software. Canvas-heavy sites feel slow but function.

### Why is the project called "hermes-computer-use" if it's agent-agnostic?

It was built alongside [hermes-agent](https://github.com/rossgray/hermes-agent) and that's the primary tested client. The name stuck. Any MCP client works.
