#!/usr/bin/env bash
# One-shot installer for hermes-computer-use (WSL2 Ubuntu target).
# Installs Xvfb + fluxbox + VNC + xdotool + ydotool + Chrome + fonts.
set -euo pipefail

# -- Guardrail: WSL2 Ubuntu is the only supported target.
if ! grep -qiE 'microsoft|wsl' /proc/version 2>/dev/null; then
    echo "[!] This installer targets WSL2 Ubuntu only. Detected kernel:" >&2
    uname -a >&2
    echo "    Set HCU_ALLOW_ANY_LINUX=1 to bypass at your own risk." >&2
    [[ "${HCU_ALLOW_ANY_LINUX:-0}" != "1" ]] && exit 2
fi
if command -v lsb_release >/dev/null 2>&1; then
    _distro=$(lsb_release -is 2>/dev/null || echo unknown)
    if [[ "$_distro" != "Ubuntu" && "${HCU_ALLOW_ANY_LINUX:-0}" != "1" ]]; then
        echo "[!] Non-Ubuntu distro ($_distro) — not tested. Set HCU_ALLOW_ANY_LINUX=1 to try." >&2
        exit 2
    fi
fi

SUDO=$(command -v sudo || true)

echo "[1/4] apt packages"
$SUDO apt-get update
$SUDO apt-get install -y --no-install-recommends \
    xvfb fluxbox x11vnc xdotool ydotool scrot imagemagick \
    xclip xsel \
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
