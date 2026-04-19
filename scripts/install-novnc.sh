#!/usr/bin/env bash
# Fetch noVNC static assets next to this repo and install websockify.
# `websockify` is pulled in by the `[novnc]` extra (`pip install ".[novnc]"`),
# but we still need the noVNC HTML/JS/CSS to serve. This script grabs them.
#
# Usage:
#   bash scripts/install-novnc.sh              # uses python3 / pip3 on PATH
#   PYTHON=.venv/bin/python bash scripts/install-novnc.sh
set -euo pipefail

PY="${PYTHON:-python3}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NOVNC_DIR="$REPO_ROOT/novnc"

echo "[1/2] pip install websockify via $PY"
"$PY" -m ensurepip --upgrade >/dev/null 2>&1 || true
"$PY" -m pip install --upgrade --quiet websockify

echo "[2/2] fetching noVNC assets into $NOVNC_DIR"
if [[ -d "$NOVNC_DIR/.git" ]]; then
    git -C "$NOVNC_DIR" pull --ff-only
else
    rm -rf "$NOVNC_DIR"
    git clone --depth 1 https://github.com/novnc/noVNC.git "$NOVNC_DIR"
fi

cat <<'MSG'

done. Next:
    cp systemd/novnc.service.example ~/.config/systemd/user/novnc.service
    # edit paths to match your install
    systemctl --user daemon-reload
    systemctl --user enable --now novnc.service
open http://localhost:6080/vnc.html in any browser.
MSG
