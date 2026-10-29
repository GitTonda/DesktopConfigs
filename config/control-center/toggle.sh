#!/usr/bin/env bash
# Control Center Toggle Script

PID_FILE="$HOME/.cache/control_center.pid"

if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE" 2>/dev/null)
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        kill "$PID" 2>/dev/null
        rm -f "$PID_FILE"
        exit 0
    fi
    rm -f "$PID_FILE"
fi

python3 "$HOME/.config/control-center/control_center.py" </dev/null >/dev/null 2>&1 &
disown
