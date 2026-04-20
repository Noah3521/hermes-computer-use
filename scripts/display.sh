#!/usr/bin/env bash
# Lifecycle manager for the virtual display stack.
#   ./display.sh start     - boot Xvfb + fluxbox + x11vnc + chrome
#   ./display.sh stop      - kill all
#   ./display.sh status    - show pids
#   ./display.sh restart
set -euo pipefail

DISPLAY_NUM="${CU_DISPLAY:-99}"
export DISPLAY=":${DISPLAY_NUM}"
# WSLg injects WAYLAND_DISPLAY + its own X socket; unset so our stack uses pure Xvfb.
unset WAYLAND_DISPLAY XDG_RUNTIME_DIR XDG_SESSION_TYPE PULSE_SERVER
W="${CU_WIDTH:-1440}"
H="${CU_HEIGHT:-900}"
VNC_PORT="${CU_VNC_PORT:-5900}"
STATE_DIR="${CU_STATE_DIR:-/tmp/hermes-computer-use}"
PROFILE_DIR="${CU_PROFILE_DIR:-$STATE_DIR/chrome-profile}"
START_URL="${CU_START_URL:-about:blank}"

mkdir -p "$STATE_DIR" "$PROFILE_DIR"

pidfile() { echo "$STATE_DIR/$1.pid"; }

_running() {
    local pf; pf=$(pidfile "$1")
    [[ -f "$pf" ]] && kill -0 "$(cat "$pf")" 2>/dev/null
}

_start_bg() {
    local name=$1; shift
    local pf; pf=$(pidfile "$name")
    if _running "$name"; then
        echo "[=] $name already running (pid=$(cat "$pf"))"
        return 0
    fi
    # setsid fully detaches so WSL parent-shell teardown doesn't kill the service.
    setsid -f "$@" >"$STATE_DIR/$name.log" 2>&1 </dev/null
    sleep 0.4
    # setsid -f doesn't print the pid; resolve via pgrep.
    local pid
    pid=$(pgrep -n -f "$(printf '%q ' "$@" | awk '{print $1}')" | head -1)
    [[ -z "$pid" ]] && pid=$(pgrep -n -f "${1##*/}" | head -1)
    if [[ -n "$pid" ]]; then
        echo "$pid" >"$pf"
        echo "[+] started $name pid=$pid"
    else
        echo "[?] started $name (pid unknown)"
    fi
}

start() {
    _start_bg xvfb    Xvfb "$DISPLAY" -screen 0 "${W}x${H}x24" -ac -nolisten tcp
    sleep 0.4
    _start_bg fluxbox fluxbox
    sleep 0.3
    _start_bg x11vnc  x11vnc -display "$DISPLAY" -forever -shared \
                        -rfbport "$VNC_PORT" -nopw -noxdamage
    sleep 0.3
    # Opt-in DOM fast-path: export CU_ENABLE_CDP=1 before calling `display.sh
    # start` to expose Chrome's DevTools port (default 9222, localhost-only).
    # This is off by default because it flips navigator.webdriver=true for
    # the session, which defeats the anti-bot posture.
    local cdp_flag=""
    if [[ "${CU_ENABLE_CDP:-0}" == "1" ]]; then
        cdp_flag="--remote-debugging-port=${CU_CDP_PORT:-9222}"
        echo "[i] DOM fast-path ENABLED — Chrome will expose CDP on $cdp_flag"
    fi
    _start_bg chrome  google-chrome \
        --no-sandbox --disable-gpu --disable-dev-shm-usage \
        --no-first-run --no-default-browser-check \
        --user-data-dir="$PROFILE_DIR" \
        --window-size="$W,$H" $cdp_flag "$START_URL"
    echo
    status
}

stop() {
    for name in chrome x11vnc fluxbox xvfb; do
        local pf; pf=$(pidfile "$name")
        if [[ -f "$pf" ]]; then
            local pid; pid=$(cat "$pf")
            kill "$pid" 2>/dev/null || true
            sleep 0.2
            kill -9 "$pid" 2>/dev/null || true
            rm -f "$pf"
            echo "[-] stopped $name"
        fi
    done
    pkill -f "Xvfb $DISPLAY" 2>/dev/null || true
}

status() {
    echo "DISPLAY=$DISPLAY  size=${W}x${H}  vnc=$VNC_PORT  state=$STATE_DIR"
    for name in xvfb fluxbox x11vnc chrome; do
        if _running "$name"; then
            echo "  [ok]   $name pid=$(cat "$(pidfile "$name")")"
        else
            echo "  [down] $name"
        fi
    done
}

case "${1:-start}" in
    start)   start ;;
    stop)    stop ;;
    restart) stop; sleep 0.5; start ;;
    status)  status ;;
    *) echo "usage: $0 {start|stop|restart|status}"; exit 2 ;;
esac
