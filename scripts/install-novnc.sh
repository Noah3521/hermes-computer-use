#!/usr/bin/env bash
# Install noVNC static assets + websockify into a Python env so the viewer is
# available at http://localhost:6080/vnc.html
#
# Usage:
#   PYTHON=/path/to/venv/bin/python bash scripts/install-novnc.sh
# or (uses `python3`):
#   bash scripts/install-novnc.sh
set -euo pipefail

PY="${PYTHON:-python3}"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
NOVNC_DIR="$REPO_ROOT/novnc"

echo "[1/2] pip install websockify into $($PY -c 'import sys; print(sys.executable)')"
"$PY" -m ensurepip --upgrade >/dev/null 2>&1 || true
"$PY" -m pip install --upgrade --quiet websockify

echo "[2/2] cloning noVNC assets into $NOVNC_DIR"
if [[ -d "$NOVNC_DIR/.git" ]]; then
    git -C "$NOVNC_DIR" pull --ff-only
else
    rm -rf "$NOVNC_DIR"
    git clone --depth 1 https://github.com/novnc/noVNC.git "$NOVNC_DIR"
fi

echo
echo "done."
echo "Enable the service with:"
echo "  systemctl --user daemon-reload"
echo "  systemctl --user enable --now novnc.service"
echo "Then open http://localhost:6080/vnc.html"
