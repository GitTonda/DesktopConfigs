#!/usr/bin/env bash
# Rofi Clipboard Selector

CACHE_FILE="$HOME/.cache/rofi_clipboard.json"
ROFI_THEME="$HOME/.config/rofi/config.rasi"

if [ ! -f "$CACHE_FILE" ]; then
    # Ensure daemon is running if not already
    if ! pgrep -f "clip_daemon.py" >/dev/null; then
        python3 "$HOME/.config/rofi/clip_daemon.py" &
    fi
    dunstify -a "Clipboard" -r 9944 "📋 Clipboard Empty" "Copy some text first!"
    exit 0
fi

python3 -c '
import json, os, subprocess

cache_file = os.path.expanduser("~/.cache/rofi_clipboard.json")
try:
    with open(cache_file, "r", encoding="utf-8") as f:
        history = json.load(f)
except Exception:
    history = []

if not history:
    subprocess.run(["dunstify", "-a", "Clipboard", "-r", "9944", "📋 Clipboard Empty", "Copy some text first!"])
    exit(0)

# Build map from index or numbered display
lines = []
for idx, item in enumerate(history):
    preview = item.get("preview", "").replace("\n", " ")
    lines.append(f"[{idx:02d}]  {preview}")

input_str = "\n".join(lines)
res = subprocess.run(
    ["rofi", "-dmenu", "-i", "-p", "󰅌 clip :~$", "-theme", os.path.expanduser("~/.config/rofi/clipboard.rasi")],
    input=input_str,
    text=True,
    stdout=subprocess.PIPE
)

selected = res.stdout.strip()
if selected and selected.startswith("["):
    try:
        idx_str = selected[1:3]
        idx = int(idx_str)
        raw_text = history[idx]["raw"]
        
        # Set clipboard & primary
        p1 = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE, text=True)
        p1.communicate(input=raw_text)
        p2 = subprocess.Popen(["xclip", "-selection", "primary"], stdin=subprocess.PIPE, text=True)
        p2.communicate(input=raw_text)
        
        # Dunst confirmation
        short_preview = raw_text.strip().splitlines()[0] if raw_text.strip() else ""
        if len(short_preview) > 40:
            short_preview = short_preview[:37] + "..."
        subprocess.run([
            "dunstify", "-a", "Clipboard", "-r", "9944", "-t", "2000",
            "📋 Copied to Clipboard", short_preview
        ])
    except Exception:
        pass
'
