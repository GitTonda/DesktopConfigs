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

# In parallel, focus the window corresponding to the notification
python3 -c "
import subprocess, json

try:
    hist = json.loads(subprocess.check_output(['dunstctl', 'history'], text=True))
    data = hist.get('data', [[]])[0]
    if data:
        latest = data[0]
        app = latest.get('appname', {}).get('data', '').strip()
        summary = latest.get('summary', {}).get('data', '').strip()
        body = latest.get('body', {}).get('data', '').strip()
        
        # Look up window in i3
        tree = json.loads(subprocess.check_output(['i3-msg', '-t', 'get_tree'], text=True))
        def find_win(node):
            if node.get('window') and node.get('window_properties'):
                c = (node.get('window_properties', {}).get('class') or '').lower()
                inst = (node.get('window_properties', {}).get('instance') or '').lower()
                t = (node.get('name') or '').lower()
                
                # Check app name
                if app and (app.lower() in c or app.lower() in inst or app.lower() in t):
                    return node['id']
                # Check keywords
                for kw in (summary + ' ' + body).lower().split():
                    if len(kw) > 3 and (kw in t or kw in c):
                        return node['id']
            for child in node.get('nodes', []) + node.get('floating_nodes', []):
                res = find_win(child)
                if res:
                    return res
            return None
            
        win_id = find_win(tree)
        if win_id:
            subprocess.run(['i3-msg', f'[con_id=\"{win_id}\"] focus'])
except Exception:
    pass
" &
