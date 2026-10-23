#!/usr/bin/env bash
set -e

WALLPAPER="$1"
if [ -z "$WALLPAPER" ] || [ ! -f "$WALLPAPER" ]; then
    echo "Usage: $0 /path/to/wallpaper.jpg"
    exit 1
fi

# 1. Extract dominant vibrant accent and wallpaper-matched dark background
read -r ACCENT BG_DARK < <(ffmpeg -v error -i "$WALLPAPER" -vf "scale=32:32" -f rawvideo -pix_fmt rgb24 - 2>/dev/null | python3 -c '
import sys, colorsys

raw = sys.stdin.buffer.read()
if not raw:
    print("#89b4fa #181825")
    sys.exit(0)

pixels = [tuple(raw[i:i+3]) for i in range(0, len(raw), 3)]
candidates = []
for r, g, b in pixels:
    h, l, s = colorsys.rgb_to_hls(r/255.0, g/255.0, b/255.0)
    # Filter for vibrant accent: saturation >= 0.25, lightness between 0.40 and 0.85
    if s >= 0.25 and 0.40 <= l <= 0.85:
        score = s * (1.0 - abs(l - 0.65))
        candidates.append((score, r, g, b, h, l, s))

if candidates:
    candidates.sort(reverse=True)
    accent_rgb = candidates[0][1:4]
    accent_h = candidates[0][4]
    accent_hex = f"#{accent_rgb[0]:02x}{accent_rgb[1]:02x}{accent_rgb[2]:02x}"
else:
    accent_h = 0.6
    accent_hex = "#89b4fa"

# Derive matching dark background:
# Target lightness 0.08, subtle saturation 0.16 derived from accent hue
r, g, b = colorsys.hls_to_rgb(accent_h, 0.08, 0.16)
bg_hex = f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"

print(f"{accent_hex} {bg_hex}")
' 2>/dev/null)

ACCENT=${ACCENT:-#89b4fa}
BG_DARK=${BG_DARK:-#181825}

# 2. Persist central colors
mkdir -p "$HOME/.config/theme"
echo "$ACCENT" > "$HOME/.config/theme/accent.color"
echo "$BG_DARK" > "$HOME/.config/theme/bg.color"

# 3. Apply Wallpaper with feh & persist ~/.fehbg
if [ -n "$DISPLAY" ]; then
    feh --no-fehbg --bg-fill "$WALLPAPER" 2>/dev/null || true
fi
cat << FEH > "$HOME/.fehbg"
#!/bin/sh
feh --no-fehbg --bg-fill '$WALLPAPER'
FEH
chmod +x "$HOME/.fehbg"

# 4. Update i3 Window Borders & Background
mkdir -p "$HOME/.config/i3"
cat << I3CONF > "$HOME/.config/i3/colors.conf"
set \$accent $ACCENT
set \$bg $BG_DARK
client.focused          \$accent \$bg #cdd6f4 \$accent \$accent
client.focused_inactive #313244 \$bg #a6adc8 #313244 #313244
client.unfocused        \$bg #11111b #6c7086 \$bg \$bg
client.urgent           #f38ba8 \$bg #f38ba8 #f38ba8 #f38ba8
client.placeholder      \$bg #11111b #cdd6f4 \$bg \$bg
client.background       #11111b
I3CONF
if [ -n "$DISPLAY" ]; then
    i3-msg reload >/dev/null 2>&1 || true
fi

# 5. Update Polybar Accent & Base
mkdir -p "$HOME/.config/polybar"
cat << PBAR > "$HOME/.config/polybar/colors.ini"
[colors]
accent = $ACCENT
base = $BG_DARK
PBAR
if [ -n "$DISPLAY" ]; then
    polybar-msg cmd restart >/dev/null 2>&1 || true
fi

# 6. Update Rofi Theme Accent & Background
mkdir -p "$HOME/.config/rofi"
cat << ROFI > "$HOME/.config/rofi/colors.rasi"
* {
    accent: $ACCENT;
    bg:     $BG_DARK;
}
ROFI

# 7. Update Dunst Notification Frame & Background
DUNST_CONFIG="$HOME/.config/dunst/dunstrc"
if [ -f "$DUNST_CONFIG" ]; then
    sed -i -E "s/(frame_color = \")[^\"]*(\")/\1$ACCENT\2/g" "$DUNST_CONFIG"
    sed -i -E "s/(highlight = \")[^\"]*(\")/\1$ACCENT\2/g" "$DUNST_CONFIG"
    sed -i -E "/\[urgency_normal\]/,/\[/ s/(background = \")[^\"]*(\")/\1$BG_DARK\2/" "$DUNST_CONFIG"
    if [ -n "$DISPLAY" ]; then
        dunstctl reload >/dev/null 2>&1 || true
    fi
fi

# 8. Update Alacritty Accent & Background Colorway directly
ALACRITTY_CONF="$HOME/.config/alacritty/alacritty.toml"
if [ -f "$ALACRITTY_CONF" ]; then
    python3 -c "
import re, sys
path = sys.argv[1]
accent = sys.argv[2]
bg_dark = sys.argv[3]
try:
    with open(path, 'r') as f:
        c = f.read()
    c = re.sub(r'(\[colors\.primary\][^\[]*?background\s*=\s*\")[^\"]*(\")', rf'\g<1>{bg_dark}\2', c, flags=re.DOTALL)
    c = re.sub(r'(\[colors\.cursor\][^\[]*?text\s*=\s*\")[^\"]*(\")', rf'\g<1>{bg_dark}\2', c, flags=re.DOTALL)
    c = re.sub(r'(\[colors\.cursor\][^\[]*?cursor\s*=\s*\")[^\"]*(\")', rf'\g<1>{accent}\2', c, flags=re.DOTALL)
    c = re.sub(r'(\[colors\.vi_mode_cursor\][^\[]*?text\s*=\s*\")[^\"]*(\")', rf'\g<1>{bg_dark}\2', c, flags=re.DOTALL)
    c = re.sub(r'(\[colors\.vi_mode_cursor\][^\[]*?cursor\s*=\s*\")[^\"]*(\")', rf'\g<1>{accent}\2', c, flags=re.DOTALL)
    c = re.sub(r'(\[colors\.selection\][^\[]*?text\s*=\s*\")[^\"]*(\")', rf'\g<1>{bg_dark}\2', c, flags=re.DOTALL)
    c = re.sub(r'(\[colors\.selection\][^\[]*?background\s*=\s*\")[^\"]*(\")', rf'\g<1>{accent}\2', c, flags=re.DOTALL)
    c = re.sub(r'(\[colors\.search\.focused_match\][^\[]*?foreground\s*=\s*\")[^\"]*(\")', rf'\g<1>{bg_dark}\2', c, flags=re.DOTALL)
    c = re.sub(r'(\[colors\.search\.focused_match\][^\[]*?background\s*=\s*\")[^\"]*(\")', rf'\g<1>{accent}\2', c, flags=re.DOTALL)
    c = re.sub(r'(\[colors\.normal\][^\[]*?blue\s*=\s*\")[^\"]*(\")', rf'\g<1>{accent}\2', c, flags=re.DOTALL)
    c = re.sub(r'(\[colors\.bright\][^\[]*?blue\s*=\s*\")[^\"]*(\")', rf'\g<1>{accent}\2', c, flags=re.DOTALL)
    with open(path, 'w') as f:
        f.write(c)
except Exception:
    pass
" "$ALACRITTY_CONF" "$ACCENT" "$BG_DARK" 2>/dev/null || true
fi

# 9. Notify user of change
WALL_NAME=$(basename "$WALLPAPER")
if command -v dunstify >/dev/null 2>&1 && [ -n "$DISPLAY" ]; then
    dunstify -r 4444 -u normal -h string:x-dunst-stack-tag:wallpaper \
        "󰸉 Theme Synchronized" "Wallpaper: ${WALL_NAME}\nAccent: <span foreground='${ACCENT}'><b>${ACCENT}</b></span> | BG: <span foreground='${BG_DARK}'><b>${BG_DARK}</b></span>"
fi
