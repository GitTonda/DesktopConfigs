#!/usr/bin/env bash

# Terminate already running bar instances cleanly via IPC
polybar-msg cmd quit 2>/dev/null || killall -q polybar

# Wait until the processes have been shut down
while pgrep -u $UID -x polybar >/dev/null; do sleep 0.1; done

# Detect battery and adapter dynamically
BATTERY_NAME=$(ls -1 /sys/class/power_supply/ 2>/dev/null | grep -E '^BAT' | head -n 1)
ADAPTER_NAME=$(ls -1 /sys/class/power_supply/ 2>/dev/null | grep -vE '^BAT' | head -n 1)

if [ -n "$BATTERY_NAME" ]; then
    export POLYBAR_BATTERY_MODULE="battery"
    export POLYBAR_BATTERY="$BATTERY_NAME"
    export POLYBAR_ADAPTER="${ADAPTER_NAME:-AC}"
else
    export POLYBAR_BATTERY_MODULE=""
    export POLYBAR_BATTERY="BAT0"
    export POLYBAR_ADAPTER="AC"
fi

# Secure user-scoped logging path (avoids symlink attacks in /tmp)
LOG_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/polybar"
mkdir -p "$LOG_DIR"

# Brief pause to allow X11 to clear tray window claims
sleep 0.2

# Launch Polybar detached from the script shell
nohup polybar main >>"$LOG_DIR/polybar.log" 2>&1 & disown
