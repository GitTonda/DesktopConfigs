#!/usr/bin/env bash
# Dunst action & window focus handler

lines=()
while IFS= read -r line; do
    [ -n "$line" ] && lines+=("$line")
done

if [ ${#lines[@]} -gt 0 ]; then
    # Return the first/default action to dunst
    echo "${lines[0]}"
fi

# In parallel, focus the window corresponding to the notification using the unified helper
python3 -c "
import sys, os, subprocess, json
sys.path.insert(0, os.path.expanduser('~/.config/control-center'))
import control_center

try:
    hist = json.loads(subprocess.check_output(['dunstctl', 'history'], text=True))
    data = hist.get('data', [[]])[0]
    if data:
        latest = data[0]
        app = latest.get('appname', {}).get('data', '').strip()
        summary = latest.get('summary', {}).get('data', '').strip()
        body = latest.get('body', {}).get('data', '').strip()
        control_center.focus_notification_target(app, summary, body)
except Exception:
    pass
" &
