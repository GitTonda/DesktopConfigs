#!/usr/bin/env bash
set -e

WALLPAPER="$1"
if [ -z "$WALLPAPER" ] || [ ! -f "$WALLPAPER" ]; then
    echo "Usage: $0 /path/to/wallpaper.jpg"
    exit 1
fi

# 1. Extract dominant vibrant accent color using ffmpeg + python
ACCENT=$(ffmpeg -v error -i "$WALLPAPER" -vf "scale=32:32" -f rawvideo -pix_fmt rgb24 - 2>/dev/null | python3 -c '
import sys, colorsys

raw = sys.stdin.buffer.read()
if not raw:
    print("#89b4fa")
    sys.exit(0)

pixels = [tuple(raw[i:i+3]) for i in range(0, len(raw), 3)]
candidates = []
for r, g, b in pixels:
    h, l, s = colorsys.rgb_to_hls(r/255.0, g/255.0, b/255.0)
    # Filter for vibrant accent: saturation >= 0.25, lightness between 0.40 and 0.85
    if s >= 0.25 and 0.40 <= l <= 0.85:
        score = s * (1.0 - abs(l - 0.65))
        candidates.append((score, r, g, b))

if candidates:
    candidates.sort(reverse=True)
    best = candidates[0]
    print(f"#{best[1]:02x}{best[2]:02x}{best[3]:02x}")
else:
    print("#89b4fa")
' 2>/dev/null)

ACCENT=${ACCENT:-#89b4fa}

# 2. Persist central accent color
mkdir -p "$HOME/.config/theme"
echo "$ACCENT" > "$HOME/.config/theme/accent.color"

# 3. Apply Wallpaper with feh & persist ~/.fehbg
if [ -n "$DISPLAY" ]; then
    feh --no-fehbg --bg-fill "$WALLPAPER" 2>/dev/null || true
fi
cat << FEH > "$HOME/.fehbg"
#!/bin/sh
feh --no-fehbg --bg-fill '$WALLPAPER'
FEH
chmod +x "$HOME/.fehbg"

# 4. Update i3 Window Borders
mkdir -p "$HOME/.config/i3"
cat << I3CONF > "$HOME/.config/i3/colors.conf"
set \$accent $ACCENT
client.focused          \$accent #1e1e2e #cdd6f4 \$accent \$accent
client.focused_inactive #313244 #181825 #a6adc8 #313244 #313244
client.unfocused        #1e1e2e #11111b #6c7086 #181825 #181825
client.urgent           #f38ba8 #1e1e2e #f38ba8 #f38ba8 #f38ba8
client.placeholder      #181825 #11111b #cdd6f4 #181825 #181825
client.background       #11111b
I3CONF
if [ -n "$DISPLAY" ]; then
    i3-msg reload >/dev/null 2>&1 || true
fi

# 5. Update Polybar Accent
mkdir -p "$HOME/.config/polybar"
cat << PBAR > "$HOME/.config/polybar/colors.ini"
[colors]
accent = $ACCENT
PBAR
if [ -n "$DISPLAY" ]; then
    polybar-msg cmd restart >/dev/null 2>&1 || true
fi

# 6. Update Rofi Theme Accent
mkdir -p "$HOME/.config/rofi"
cat << ROFI > "$HOME/.config/rofi/colors.rasi"
* {
    accent: $ACCENT;
}
ROFI

# 7. Update Dunst Notification Frame
DUNST_CONFIG="$HOME/.config/dunst/dunstrc"
if [ -f "$DUNST_CONFIG" ]; then
    sed -i -E "s/(frame_color = \")[^\"]*(\")/\1$ACCENT\2/g" "$DUNST_CONFIG"
    sed -i -E "s/(highlight = \")[^\"]*(\")/\1$ACCENT\2/g" "$DUNST_CONFIG"
    if [ -n "$DISPLAY" ]; then
        dunstctl reload >/dev/null 2>&1 || true
    fi
fi

# 8. Update Alacritty Cursor & Selection
mkdir -p "$HOME/.config/alacritty"
cat << ALACRITTY > "$HOME/.config/alacritty/colors.toml"
[colors.cursor]
text = "#1e1e2e"
cursor = "$ACCENT"

[colors.selection]
text = "#1e1e2e"
background = "$ACCENT"
ALACRITTY

# 9. Notify user of change
WALL_NAME=$(basename "$WALLPAPER")
if command -v dunstify >/dev/null 2>&1 && [ -n "$DISPLAY" ]; then
    dunstify -r 4444 -u normal -h string:x-dunst-stack-tag:wallpaper \
        "󰸉 Theme Synchronized" "Wallpaper: ${WALL_NAME}\nAccent: <span foreground='${ACCENT}'><b>${ACCENT}</b></span>"
fi
