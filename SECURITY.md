# Security considerations

This server gives an LLM the ability to move a real mouse, press real keys, and run arbitrary shell commands on the host. Treat it accordingly.

## Threat model

| Actor | Capability | Mitigation |
|---|---|---|
| The agent you trust | Full desktop + `run_shell` | Run the whole stack in an isolated WSL distro or VM |
| A compromised agent / prompt injection | Same as above | Remove or whitelist-limit `run_shell`; do not store real credentials in the persistent Chrome profile |
| Other users on the same machine | Can connect to `:5900` / `:6080` | Bind to `127.0.0.1` only, or firewall; use VNC password if exposing |
| Network attackers | Can connect to exposed ports | Keep ports localhost-only; put noVNC behind SSL + auth if remote access is needed |

## Hardening checklist

1. **Isolate the WSL distro.** Don't run this on your daily Ubuntu. `wsl --import hermes-cu Ubuntu-24.04` gives you a disposable instance.
2. **Strip `run_shell`** from the MCP tool list if the agent doesn't need filesystem / shell access. It's an escape hatch — remove it in production.
3. **Scrub the Chrome profile regularly.** `$CU_PROFILE_DIR` accumulates cookies, autofill, passwords. `rm -rf` between tenants.
4. **Restrict VNC exposure.**
   - `x11vnc` runs with `-nopw` by default. Add `-rfbauth /path/to/passwd` for production.
   - Bind noVNC to `127.0.0.1` by editing `systemd/novnc.service` (add `--listen-host=127.0.0.1`).
5. **Segment network access.** Use iptables or WSL mirrored networking with Windows Defender Firewall rules if the browser shouldn't reach internal services.
6. **Observe, don't trust.** Keep the noVNC tab open during long-running sessions. If the agent starts doing something unexpected, kill the service.

## Not included

- No built-in authentication between hermes-agent and this MCP server. stdio transport assumes the client process is trusted.
- No audit log of tool calls. Add one via `hermes` gateway logs or wrap `computer_use_mcp.py` with a logging proxy if you need SOC-level traceability.
- No anti-detection patches beyond stock Chrome flags. This project's thesis is that "no abnormal signals" > "sophisticated evasion." If you fight the fingerprinting arms race, you move outside this repo's scope.

## Reporting issues

Email the maintainer. Do not open public issues for security-sensitive findings.
