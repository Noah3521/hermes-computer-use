#!/usr/bin/env bash
# Record a demo of the agent driving the browser.
#
# Usage:
#   ./scripts/record-demo.sh              # record 30s, produce docs/demo.mp4 + docs/demo.gif
#   DURATION=60 ./scripts/record-demo.sh  # longer run
#   FORMAT=mp4 ./scripts/record-demo.sh   # skip GIF conversion
#
# Requirements: ffmpeg (apt install ffmpeg). For GIF: gifsicle optional, otherwise ffmpeg palette.

set -euo pipefail

DISPLAY_NUM="${CU_DISPLAY:-99}"
WIDTH="${CU_WIDTH:-1440}"
HEIGHT="${CU_HEIGHT:-900}"
DURATION="${DURATION:-30}"
FORMAT="${FORMAT:-gif}"
OUT_DIR="${OUT_DIR:-docs}"
STAMP="$(date +%Y%m%d-%H%M%S)"
MP4="$OUT_DIR/demo-$STAMP.mp4"
GIF="$OUT_DIR/demo-$STAMP.gif"
PALETTE="$OUT_DIR/.palette-$STAMP.png"

command -v ffmpeg >/dev/null || { echo "ffmpeg not found. sudo apt install ffmpeg"; exit 1; }
xdpyinfo -display ":$DISPLAY_NUM" >/dev/null 2>&1 \
    || { echo "Xvfb :$DISPLAY_NUM not reachable — run display.sh start first."; exit 1; }

mkdir -p "$OUT_DIR"

echo "[rec] $DURATION s from :$DISPLAY_NUM -> $MP4"
ffmpeg -y -loglevel warning \
    -video_size "${WIDTH}x${HEIGHT}" \
    -framerate 24 \
    -f x11grab -i ":$DISPLAY_NUM" \
    -t "$DURATION" \
    -c:v libx264 -preset veryfast -pix_fmt yuv420p \
    "$MP4"

if [[ "$FORMAT" == "gif" ]]; then
    echo "[gif] converting via palette pass -> $GIF"
    ffmpeg -y -loglevel warning -i "$MP4" \
        -vf "fps=12,scale=960:-1:flags=lanczos,palettegen" "$PALETTE"
    ffmpeg -y -loglevel warning -i "$MP4" -i "$PALETTE" \
        -lavfi "fps=12,scale=960:-1:flags=lanczos [x]; [x][1:v] paletteuse" "$GIF"
    rm -f "$PALETTE"
    echo
    echo "done:"
    echo "  mp4 : $MP4"
    echo "  gif : $GIF ($(du -h "$GIF" | cut -f1))"
else
    echo
    echo "done: $MP4 ($(du -h "$MP4" | cut -f1))"
fi
