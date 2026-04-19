# Troubleshooting

## `scrot: Can't open X display. It is running, yeah? [:99]`

Xvfb died. Check and restart:

```bash
systemctl --user status computer-use.service
systemctl --user restart computer-use.service
bash scripts/display.sh status
```

If `display.sh status` shows everything down even after restart, tail the log:
```bash
journalctl --user -u computer-use.service -n 50
cat /tmp/hermes-computer-use/xvfb.log
```

Common cause: another process is bound to `127.0.0.1:8765` (or your `CU_DISPLAY` port). WSL's `wslrelay` is the usual culprit. Change `CU_DISPLAY` or kill the offender.

## Chrome immediately dies after `display.sh start`

Look for `zygote_communication_linux.cc:291` in `chrome.log`. Fix in order:

1. Make sure `--no-sandbox --disable-dev-shm-usage` are both present (they are by default).
2. Wipe the profile: `rm -rf $CU_STATE_DIR/chrome-profile`.
3. If you use nohup-style launchers, replace with `setsid -f`. WSL's default shell teardown kills nohup children.

## Chrome window invisible in VNC but `xdotool search` sees it

x11vnc is probably connected to a WSLg Wayland session, not Xvfb :99. Fix:

```bash
unset WAYLAND_DISPLAY XDG_RUNTIME_DIR XDG_SESSION_TYPE
```

`scripts/display.sh` already does this. If you start x11vnc manually, unset first.

## `bash: line 1: C:/Program: No such file or directory`

Windows PATH leaking into WSL subshell. Use `exec` or prefix with `PATH=/usr/bin:/bin`:
```bash
exec /path/to/python script.py
```

## Stack dies when you close the WSL terminal

Enable linger so systemd user services survive logout:
```bash
sudo loginctl enable-linger $USER
loginctl show-user $USER | grep Linger   # Linger=yes
```

## Coordinates off by 10–20 pixels

Vision model grounding error. Not a bug in the stack. Mitigations:

- Ask the model to re-screenshot and verify before committing the click.
- Prefer larger click targets early in an automation.
- For tiny sliders, use `drag` with `steps=40` so intermediate positions stabilize.
- Consider adding AT-SPI accessibility tree as a side channel (not included here).

## Google flags traffic as "unusual"

The Google result is IP-based reputation, not behavioural. Your WSL NAT IP is shared with other cloud tenants. Mitigations:

- Run the request through a residential proxy.
- Prewarm cookies: interactively log in via VNC once, then let the persisted Chrome profile (`CU_PROFILE_DIR`) carry cookies.

## Cloudflare "Verify you are human"

Harder than Google. Try:

1. Switch input: `CU_INPUT=ydotool` — kernel-level HID usually passes.
2. Let the page idle for 3–5 seconds before any action (CF looks at first-paint interaction timing).
3. Avoid absolute-instant cursor moves: keep `human=True`.

## noVNC browser tab blank after clicking "Connect"

- Confirm the service is up: `systemctl --user status novnc.service`.
- Confirm port from WSL: `curl -I http://localhost:6080/vnc.html` → 200 expected.
- From Windows, try `http://<wsl-ip>:6080/vnc.html` if `localhost` refuses (firewall edge cases).
- Canvas scaling: open the noVNC gear icon → **Scaling Mode → Local Scaling**.

## How do I know the automation isn't Selenium-detected?

Open `https://bot.sannysoft.com` via the stack and screenshot. WebDriver, Chrome runtime, permissions, plugins, languages — should all be green. If any flip red compared to a vanilla headed Chrome, that's a leak to investigate.
