#!/usr/bin/env bash
# ==============================================================================
# Polybar Launcher with Systemd Supervised Watchdog
# Ensures the status bar starts cleanly and auto-revives if ever terminated.
# ==============================================================================

LOG_DIR="${XDG_STATE_HOME:-$HOME/.local/state}/polybar"
mkdir -p "$LOG_DIR"

# If systemd user service is available, let systemd manage lifecycle & auto-restart
if systemctl --user is-enabled polybar.service >/dev/null 2>&1 || [ -f "$HOME/.config/systemd/user/polybar.service" ]; then
    systemctl --user daemon-reload >/dev/null 2>&1 || true
    systemctl --user restart polybar.service
    exit 0
fi

# Fallback: Manual Process Management
polybar-msg cmd quit 2>/dev/null || true
for i in {1..10}; do
    if ! pgrep -u "$UID" -x polybar >/dev/null; then
        break
    fi
    sleep 0.1
done

if pgrep -u "$UID" -x polybar >/dev/null; then
    killall -9 polybar 2>/dev/null || true
    sleep 0.2
fi

nohup polybar main >>"$LOG_DIR/polybar.log" 2>&1 &
disown
