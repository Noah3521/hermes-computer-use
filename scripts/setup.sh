#!/usr/bin/env bash
# One-shot installer for computer-use integration.
# Installs Xvfb + fluxbox + VNC + xdotool + ydotool + Chrome + fonts.
set -euo pipefail

SUDO=$(command -v sudo || true)

echo "[1/4] apt packages"
$SUDO apt-get update
$SUDO apt-get install -y --no-install-recommends \
    xvfb fluxbox x11vnc xdotool ydotool scrot imagemagick \
    fonts-noto-cjk fonts-noto-color-emoji \
    ca-certificates curl wget gnupg xdg-utils \
    libnss3 libatk-bridge2.0-0 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 libasound2t64 \
    libpango-1.0-0 libcairo2 libcups2

echo "[2/4] Chrome"
if ! command -v google-chrome >/dev/null 2>&1; then
    TMP=$(mktemp -d)
    wget -qO "$TMP/chrome.deb" \
        https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
    $SUDO apt-get install -y "$TMP/chrome.deb"
    rm -rf "$TMP"
fi
google-chrome --version

echo "[3/4] Python deps into hermes venv"
VENV="/home/geunuk/.hermes/hermes-agent/venv"
"$VENV/bin/python" -m pip install --upgrade --quiet mcp Pillow 2>/dev/null \
    || echo "pip install skipped (mcp already importable or network restricted)"

echo "[4/4] uinput (optional, for ydotool)"
if [[ ! -e /dev/uinput ]]; then
    $SUDO modprobe uinput || echo "modprobe uinput failed; ydotool will fall back to xdotool"
fi
if [[ -e /dev/uinput ]]; then
    $SUDO chgrp input /dev/uinput 2>/dev/null || true
    $SUDO chmod 660 /dev/uinput 2>/dev/null || true
    echo "/dev/uinput ready."
fi

echo "done."
