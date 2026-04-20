#!/usr/bin/env bash
# Remove hermes-computer-use services and runtime state.
# Does NOT uninstall apt packages or Chrome — those are shared with the system.
# Does NOT delete the git clone.
set -euo pipefail

echo "[1/4] disabling systemd user services"
systemctl --user disable --now novnc.service 2>/dev/null || true
systemctl --user disable --now computer-use.service 2>/dev/null || true

echo "[2/4] removing unit files"
rm -f ~/.config/systemd/user/computer-use.service
rm -f ~/.config/systemd/user/novnc.service
systemctl --user daemon-reload

echo "[3/4] killing any leftover processes"
pkill -f 'Xvfb :99' 2>/dev/null || true
pkill -f fluxbox    2>/dev/null || true
pkill -f x11vnc     2>/dev/null || true
pkill -f websockify 2>/dev/null || true
pkill -f google-chrome 2>/dev/null || true

echo "[4/4] removing runtime state"
rm -rf /tmp/hermes-computer-use
rm -rf "${XDG_STATE_HOME:-$HOME/.local/state}/hermes-computer-use"
rm -rf "${XDG_DATA_HOME:-$HOME/.local/share}/hermes-computer-use"

echo
echo "done. The git clone and apt packages are untouched."
echo "To remove the git clone:      rm -rf $(cd "$(dirname "$0")/.." && pwd)"
echo "To remove Chrome + tools:     sudo apt remove google-chrome-stable xdotool ydotool scrot x11vnc fluxbox xvfb"
