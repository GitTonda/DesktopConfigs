#!/usr/bin/env bash

# Terminate already running bar instances cleanly via IPC
polybar-msg cmd quit 2>/dev/null || killall -q polybar

# Wait until the processes have been shut down
while pgrep -u $UID -x polybar >/dev/null; do sleep 0.1; done

# Brief pause to allow X11 to clear tray window claims
sleep 0.2

# Launch Polybar
polybar main >>/tmp/polybar.log 2>&1 &
