# WSL2 Setup

This project targets **WSL2 on Windows 11, Ubuntu 22.04 or 24.04**. Everything else is unsupported by design. If you need native Linux or macOS, consider forking — the Linux pieces (`Xvfb + xdotool + Chrome`) all work there, but the scripts, systemd units, and troubleshooting docs assume WSL-specific quirks (wslrelay port hijacking, WSLg env variables, interop PATH bleed, shutdown-on-last-session behavior).

## Why WSL-only

- **One well-tested surface.** WSL2 Ubuntu is consistent across hundreds of thousands of installs. Native distros diverge on systemd, sandboxing, display servers, and input devices in ways that double the maintenance burden.
- **WSL-specific pitfalls the code handles.** `WAYLAND_DISPLAY` leaking from WSLg, `wslrelay.exe` hijacking loopback ports, Windows PATH leaking into `bash -c`, WSL VM termination killing `setsid -f` children — the scripts in this repo were tuned for these.
- **Browser-observer pipeline.** `localhost:5900` and `localhost:6080` auto-forward to Windows because of WSL2 NAT + mirrored networking. On bare Linux you'd need explicit port forwarding.

## Prerequisites

1. Windows 11 (10 works but is not tested).
2. Virtualization enabled in BIOS.
3. Administrator PowerShell for the Windows-side steps.

## 1. Enable systemd

Check from inside WSL:

```bash
systemctl is-system-running
```

If it says `offline` or the command errors, edit `/etc/wsl.conf` inside WSL:

```ini
[boot]
systemd=true

[user]
default=<your-username>
```

Then from **PowerShell (administrator)**:

```powershell
wsl --shutdown
wsl
```

Re-verify `systemctl is-system-running` — should be `running`.

## 2. Install an Ubuntu distro (if you don't have one)

```powershell
wsl --install -d Ubuntu-24.04
```

Follow the prompt to create a user.

## 3. (Optional but recommended) Dedicate a distro to this project

Running an LLM with full desktop + shell access on your daily dev distro is a bad idea. Clone:

```powershell
wsl --export Ubuntu-24.04 C:\wsl\base.tar
wsl --import hermes-cu C:\wsl\hermes-cu C:\wsl\base.tar
wsl -d hermes-cu
```

Then run the project install inside the `hermes-cu` distro. Trash it at any time with `wsl --unregister hermes-cu`.

## 4. Install the project

Continue with the main [README — Install](../README.md#install).

## 5. Persistence across WSL shutdowns

WSL terminates VMs a few seconds after the last session closes. The included systemd user services handle this, but require **linger**:

```bash
sudo loginctl enable-linger "$USER"
loginctl show-user "$USER" | grep Linger   # Linger=yes
```

Without linger the stack dies every time you close every Windows terminal connected to WSL.

## 6. Viewing the browser

Three options, pick one:

| Method | Install | Access |
|---|---|---|
| **Native VNC viewer** | `winget install TigerVNC.TigerVNCViewer` on Windows | open `localhost:5900` |
| **Browser viewer** (noVNC) | `bash scripts/install-novnc.sh` inside WSL | open `http://localhost:6080/vnc.html` |
| **WSL IP direct** | — | `wsl hostname -I` → `http://<ip>:6080/vnc.html` (falls back when localhost forwarding glitches) |

## 7. Ports and firewall

WSL2 auto-forwards `localhost:<port>` from Windows to the WSL VM. If Windows Defender Firewall blocks it:

```powershell
New-NetFirewallRule -DisplayName "WSL noVNC" -Direction Inbound -LocalPort 6080 -Protocol TCP -Action Allow
New-NetFirewallRule -DisplayName "WSL x11vnc" -Direction Inbound -LocalPort 5900 -Protocol TCP -Action Allow
```

Only needed if you want to reach the viewer from another device on your LAN.

## 8. GPU acceleration (optional)

Xvfb is a software framebuffer. Heavy WebGL pages will crawl. If you have an NVIDIA GPU with CUDA on WSL2:

```bash
nvidia-smi            # should work inside WSL
# then swap Xvfb for Xorg-dummy in scripts/display.sh — out of scope for the default build
```

Most agent automation doesn't need this.

## 9. Known WSL quirks this project handles

- **`wslrelay.exe` binding `127.0.0.1:<port>`.** If your `CU_DISPLAY` port collides, display.sh's port probe fails fast with a clear message.
- **WSLg `WAYLAND_DISPLAY=wayland-0`.** x11vnc would otherwise attach to the WSLg Wayland session instead of our Xvfb. display.sh unsets it.
- **Windows PATH in bash -c.** Running bash `python --version` can fail with `C:/Program: not found` when PATH contains unescaped spaces. Use `exec` or explicit python paths.
- **`setsid -f` + VM shutdown.** setsid-detached processes still die when WSL VM stops. systemd user services + linger survive this.
- **Line endings.** Always clone via git (preserves LF). Creating files via `\\wsl.localhost\` from Windows with CRLF can break shell scripts.

If you hit any WSL-specific issue not listed here, open an issue — it probably belongs in this doc.
