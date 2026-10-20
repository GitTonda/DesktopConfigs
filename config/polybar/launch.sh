#!/usr/bin/env bash

# Terminate already running bar instances
killall -q polybar

# Wait until the processes have been shut down
while pgrep -u $UID -x polybar >/dev/null; do sleep 0.1; done

# Detect battery on laptops
if ls /sys/class/power_supply/BAT* 1> /dev/null 2>&1; then
    export HAS_BATTERY="battery"
else
    export HAS_BATTERY=""
fi

# Launch Polybar
nohup polybar main >/tmp/polybar.log 2>&1 &
