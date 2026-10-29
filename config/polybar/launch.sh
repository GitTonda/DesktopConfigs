#!/usr/bin/env bash
# ==============================================================================
# Polybar Launcher with Dynamic Hardware Detection & Single-Instance Guarantee
# ==============================================================================

LOG_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/polybar"
mkdir -p "$LOG_DIR"

# Detect battery and adapter dynamically
BATTERY_NAME=$(ls -1 /sys/class/power_supply/ 2>/dev/null | grep -E '^BAT' | head -n 1)
ADAPTER_NAME=$(ls -1 /sys/class/power_supply/ 2>/dev/null | grep -vE '^BAT' | head -n 1)

export POLYBAR_BATTERY="${BATTERY_NAME:-BAT0}"
export POLYBAR_ADAPTER="${ADAPTER_NAME:-AC}"

# If systemd user service is available, let systemd manage lifecycle cleanly
if systemctl --user is-enabled polybar.service >/dev/null 2>&1 || [ -f "$HOME/.config/systemd/user/polybar.service" ]; then
    # Stop the systemd service first so it won't auto-revive while we clean up
    systemctl --user stop polybar.service 2>/dev/null || true

    # Terminate any rogue, unmanaged, or lingering polybar processes outside systemd
    polybar-msg cmd quit 2>/dev/null || true
    for i in {1..10}; do
        if ! pgrep -u "$UID" -x polybar >/dev/null; then
            break
        fi
        sleep 0.1
    done
    if pgrep -u "$UID" -x polybar >/dev/null; then
        killall -9 polybar 2>/dev/null || true
        while pgrep -u "$UID" -x polybar >/dev/null 2>&1; do sleep 0.05; done
    fi

    # Set dynamic hardware environment for the user systemd instance
    systemctl --user set-environment POLYBAR_BATTERY="$POLYBAR_BATTERY" POLYBAR_ADAPTER="$POLYBAR_ADAPTER" >/dev/null 2>&1 || true
    systemctl --user daemon-reload >/dev/null 2>&1 || true

    # Start the clean, single supervised service instance
    systemctl --user start polybar.service
    exit 0
fi

# Fallback: Manual Process Management (if systemd user session is not in use)
polybar-msg cmd quit 2>/dev/null || true
for i in {1..10}; do
    if ! pgrep -u "$UID" -x polybar >/dev/null; then
        break
    fi
    sleep 0.1
done

if pgrep -u "$UID" -x polybar >/dev/null; then
    killall -9 polybar 2>/dev/null || true
    while pgrep -u "$UID" -x polybar >/dev/null 2>&1; do sleep 0.05; done
fi

nohup polybar main >>"$LOG_DIR/polybar.log" 2>&1 &
disown
