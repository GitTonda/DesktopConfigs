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

# 3. Apply Wallpaper with feh & persist ~/.fehbg (guaranteeing desktop cursor persistence)
if [ -n "$DISPLAY" ]; then
    feh --no-fehbg --bg-fill "$WALLPAPER" 2>/dev/null || true
    if [ -f "$HOME/.icons/Bibata-Modern-Classic/cursors/left_ptr" ]; then
        xsetroot -xcf "$HOME/.icons/Bibata-Modern-Classic/cursors/left_ptr" 24 2>/dev/null || xsetroot -cursor_name left_ptr 2>/dev/null || true
    else
        xsetroot -cursor_name left_ptr 2>/dev/null || true
    fi
fi
cat << 'FEH' > "$HOME/.fehbg"
#!/bin/sh
feh --no-fehbg --bg-fill 'WALLPAPER_PATH_PLACEHOLDER'
THEME="Bibata-Modern-Classic"
if [ -f "$HOME/.icons/default/index.theme" ]; then
    DETECTED=$(grep -E '^Inherits=' "$HOME/.icons/default/index.theme" | cut -d= -f2 | tr -d ' \r\n')
    [ -n "$DETECTED" ] && THEME="$DETECTED"
fi
export XCURSOR_THEME="$THEME"
export XCURSOR_SIZE="24"
CURSOR_FILE=""
for p in "$HOME/.icons/$THEME/cursors/left_ptr" "$HOME/.local/share/icons/$THEME/cursors/left_ptr" "/usr/share/icons/$THEME/cursors/left_ptr"; do
    if [ -f "$p" ]; then
        CURSOR_FILE="$p"
        break
    fi
done
if [ -n "$CURSOR_FILE" ]; then
    xsetroot -xcf "$CURSOR_FILE" 24 2>/dev/null || xsetroot -cursor_name left_ptr
else
    xsetroot -cursor_name left_ptr
fi
FEH
sed -i "s|WALLPAPER_PATH_PLACEHOLDER|$WALLPAPER|g" "$HOME/.fehbg"
chmod +x "$HOME/.fehbg"

# 3b. Cache blurred lockscreen background asynchronously (cached: only if wallpaper changed)
if command -v magick >/dev/null 2>&1; then
    (
        mkdir -p "$HOME/.cache"
        if [ ! -f "$HOME/.cache/lockscreen.png" ] || [ "$WALLPAPER" -nt "$HOME/.cache/lockscreen.png" ]; then
            magick "$WALLPAPER" -filter Gaussian -resize 1920x1080^ -gravity center -extent 1920x1080 -blur 0x8 -fill "#11111b" -colorize 25% "$HOME/.cache/lockscreen.png" 2>/dev/null || true
        fi
    ) &
fi

# 3c. Update Fastfetch dynamic accent color
if [ -f "$HOME/.config/fastfetch/config.jsonc" ]; then
    HEX_CLEAN="${ACCENT#'#'}"
    R=$((16#${HEX_CLEAN:0:2}))
    G=$((16#${HEX_CLEAN:2:2}))
    B=$((16#${HEX_CLEAN:4:2}))
    sed -i -E "s/38;2;[0-9]+;[0-9]+;[0-9]+/38;2;${R};${G};${B}/g" "$HOME/.config/fastfetch/config.jsonc" 2>/dev/null || true
fi

# 4. Update i3 Window Borders & Background
mkdir -p "$HOME/.config/i3"
cat << I3CONF > "$HOME/.config/i3/colors.conf"
set \$accent $ACCENT
set \$bg $BG_DARK
set \$border_focused #6c7086
client.focused          \$border_focused \$bg #cdd6f4 \$border_focused \$border_focused
client.focused_inactive #313244 \$bg #a6adc8 #313244 #313244
client.unfocused        \$bg #11111b #45475a \$bg \$bg
client.urgent           #f38ba8 \$bg #f38ba8 #f38ba8 #f38ba8
client.placeholder      \$bg #11111b #cdd6f4 \$bg \$bg
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
    "$HOME/.config/polybar/launch.sh" >/dev/null 2>&1 || true
fi

# 6. Update Rofi Theme Accent & Background (Uniform Frosted Transparency)
mkdir -p "$HOME/.config/rofi"
cat << ROFI > "$HOME/.config/rofi/colors.rasi"
* {
    accent:     $ACCENT;
    bg:         rgba(17, 17, 27, 0.60);
    bg-alt:     rgba(24, 24, 37, 0.52);
    bg-frosted: rgba(17, 17, 27, 0.60);
    bg-header:  rgba(24, 24, 37, 0.52);
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

# 10. Synchronize Hardware RGB Lights (Fans, RAM, GPU) via OpenRGB
if [ -f "$HOME/.config/theme/sync-rgb.sh" ]; then
    "$HOME/.config/theme/sync-rgb.sh" "$ACCENT" >/dev/null 2>&1 &
fi

# 11. Update Cursor Theme (preserves user preference if set to Bibata/Nordzy/Qogir)
python3 -c "
import colorsys, subprocess, os

home = os.path.expanduser('~')
idx_path = f'{home}/.icons/default/index.theme'
current_theme = 'Bibata-Modern-Classic'
if os.path.exists(idx_path):
    try:
        with open(idx_path, 'r') as f:
            for line in f:
                if line.startswith('Inherits='):
                    current_theme = line.split('=', 1)[1].strip()
    except Exception:
        pass

# Only auto-shift if user is using a dynamic catppuccin theme
if current_theme.startswith('catppuccin-mocha'):
    accent = '$ACCENT'.lstrip('#')
    try:
        r, g, b = int(accent[0:2], 16)/255.0, int(accent[2:4], 16)/255.0, int(accent[4:6], 16)/255.0
        h, l, s = colorsys.rgb_to_hls(r, g, b)
        if 0.42 <= h <= 0.54:
            theme = 'catppuccin-mocha-teal-cursors'
        elif 0.54 < h <= 0.68:
            theme = 'catppuccin-mocha-blue-cursors'
        elif 0.68 < h <= 0.82:
            theme = 'catppuccin-mocha-lavender-cursors'
        else:
            theme = 'catppuccin-mocha-dark-cursors'

        # Match Catppuccin Mocha folder icon color
        if 0.04 <= h < 0.12:
            fcolor = 'cat-mocha-peach'
        elif 0.12 <= h < 0.18:
            fcolor = 'cat-mocha-yellow'
        elif 0.18 <= h < 0.42:
            fcolor = 'cat-mocha-green'
        elif 0.42 <= h < 0.52:
            fcolor = 'cat-mocha-teal'
        elif 0.52 <= h < 0.60:
            fcolor = 'cat-mocha-sapphire'
        elif 0.60 <= h < 0.68:
            fcolor = 'cat-mocha-blue'
        elif 0.68 <= h < 0.82:
            fcolor = 'cat-mocha-mauve'
        elif 0.82 <= h < 0.94:
            fcolor = 'cat-mocha-pink'
        else:
            fcolor = 'cat-mocha-red'
        subprocess.run(['sudo', '-n', 'papirus-folders', '-C', fcolor, '-t', 'Papirus-Dark'], check=False)
    except Exception:
        theme = current_theme
else:
    theme = current_theme

for p in [idx_path, f'{home}/.local/share/icons/default/index.theme']:
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w') as f:
        f.write(f'[Icon Theme]\nName=Default\nComment=Default Cursor Theme\nInherits={theme}\n')

xres_path = f'{home}/.Xresources'
with open(xres_path, 'w') as f:
    f.write(f'Xcursor.theme: {theme}\nXcursor.size: 24\n')

with open(f'{home}/.gtkrc-2.0', 'w') as f:
    f.write(f'gtk-theme-name="Adwaita-dark"\ngtk-icon-theme-name="Papirus-Dark"\ngtk-cursor-theme-name="{theme}"\ngtk-cursor-theme-size=24\ngtk-font-name="JetBrainsMono Nerd Font 10"\n')

for gtk_ver in ['gtk-3.0', 'gtk-4.0']:
    gtk_path = f'{home}/.config/{gtk_ver}/settings.ini'
    os.makedirs(os.path.dirname(gtk_path), exist_ok=True)
    with open(gtk_path, 'w') as f:
        f.write(f'[Settings]\ngtk-theme-name=Adwaita-dark\ngtk-icon-theme-name=Papirus-Dark\ngtk-cursor-theme-name={theme}\ngtk-cursor-theme-size=24\ngtk-font-name=JetBrainsMono Nerd Font 10\ngtk-application-prefer-dark-theme=1\n')

    # Update GTK CSS accent & background colors
    for base_d in [f'{home}/.config/{gtk_ver}', f'{home}/DesktopConfigs/config/{gtk_ver}']:
        css_path = f'{base_d}/gtk.css'
        if os.path.exists(css_path):
            try:
                import re
                with open(css_path, 'r', encoding='utf-8') as f:
                    c = f.read()
                c = re.sub(r'@define-color\s+accent_color\s+#[0-9a-fA-F]{6};', f'@define-color accent_color $ACCENT;', c)
                c = re.sub(r'@define-color\s+mantle_bg\s+#[0-9a-fA-F]{6};', f'@define-color mantle_bg $BG_DARK;', c)
                with open(css_path, 'w', encoding='utf-8') as f:
                    f.write(c)
            except Exception:
                pass

xprof_path = f'{home}/.xprofile'
with open(xprof_path, 'w') as f:
    f.write(f'#!/bin/sh\nexport XCURSOR_THEME="{theme}"\nexport XCURSOR_SIZE="24"\nxrdb -merge "$HOME/.Xresources" 2>/dev/null || true\nxsetroot -cursor_name left_ptr 2>/dev/null || true\n')
os.chmod(xprof_path, 0o755)

subprocess.run(['flatpak', 'override', '--user', '--filesystem=~/.icons:ro', '--filesystem=~/.local/share/icons:ro', f'--env=XCURSOR_THEME={theme}', '--env=XCURSOR_SIZE=24'], check=False)
subprocess.run(['systemctl', '--user', 'set-environment', f'XCURSOR_THEME={theme}', 'XCURSOR_SIZE=24'], check=False)
subprocess.run(['dbus-update-activation-environment', '--systemd', f'XCURSOR_THEME={theme}', 'XCURSOR_SIZE=24'], check=False)
subprocess.run(['xrdb', '-merge', xres_path], check=False)
subprocess.run(['gsettings', 'set', 'org.gnome.desktop.interface', 'cursor-theme', theme], check=False)
subprocess.run(['gsettings', 'set', 'org.gnome.desktop.interface', 'cursor-size', '24'], check=False)
subprocess.run(['xsetroot', '-cursor_name', 'left_ptr'], check=False)
" 2>/dev/null || true

# 9. Update Zen Browser Theme Colors (userChrome.css / userContent.css / user.js)
ACCENT="$ACCENT" BG_DARK="$BG_DARK" python3 - << 'PYEOF'
import os, sys, re

accent = os.environ.get('ACCENT', '#89b4fa')
bg = os.environ.get('BG_DARK', '#181825')

# Base locations for Zen configurations
zen_bases = [
    os.path.expanduser('~/.zen'),
    os.path.expanduser('~/.var/app/app.zen_browser.zen/.zen'),
]

# Source template folders
template_dirs = [
    os.path.expanduser('~/.config/zen'),
    os.path.expanduser('~/DesktopConfigs/config/zen')
]

target_dirs = []
for t in template_dirs:
    if os.path.isdir(t):
        target_dirs.append(t)

for base in zen_bases:
    if os.path.isdir(base):
        for entry in os.listdir(base):
            p = os.path.join(base, entry)
            if os.path.isdir(p) and any(kw in entry.lower() for kw in ['default', 'release', 'profile']):
                target_dirs.append(p)

for d in target_dirs:
    # 1. Update userChrome.css
    chrome_file = os.path.join(d, 'chrome', 'userChrome.css')
    if os.path.exists(chrome_file):
        try:
            with open(chrome_file, 'r', encoding='utf-8') as f:
                content = f.read()
            content = re.sub(r'--zen-primary-color:\s*#[0-9a-fA-F]{6}', f'--zen-primary-color: {accent}', content)
            content = re.sub(r'--zen-colors-border:\s*#[0-9a-fA-F]{6}', f'--zen-colors-border: {accent}', content)
            content = re.sub(r'--toolbarbutton-icon-fill:\s*#[0-9a-fA-F]{6}', f'--toolbarbutton-icon-fill: {accent}', content)
            content = re.sub(r'--identity-tab-color:\s*#[0-9a-fA-F]{6}', f'--identity-tab-color: {accent}', content)
            content = re.sub(r'--identity-icon-color:\s*#[0-9a-fA-F]{6}', f'--identity-icon-color: {accent}', content)
            content = re.sub(r'(\.zen-library-tab\[active\]::before\s*\{\s*background:\s*)#[0-9a-fA-F]{6}', r'\g<1>' + accent, content)
            content = re.sub(r'(\.zen-library-group h3\s*\{\s*color:\s*)#[0-9a-fA-F]{6}', r'\g<1>' + accent, content)
            with open(chrome_file, 'w', encoding='utf-8') as f:
                f.write(content)
        except Exception:
            pass

    # 2. Update userContent.css
    content_file = os.path.join(d, 'chrome', 'userContent.css')
    if os.path.exists(content_file):
        try:
            with open(content_file, 'r', encoding='utf-8') as f:
                c = f.read()
            c = re.sub(r'--color-accent-primary:\s*#[0-9a-fA-F]{6}', f'--color-accent-primary: {accent}', c)
            c = re.sub(r'--newtab-primary-action-background:\s*#[0-9a-fA-F]{6}', f'--newtab-primary-action-background: {accent}', c)
            c = re.sub(r'--link-color:\s*#[0-9a-fA-F]{6}', f'--link-color: {accent}', c)
            c = re.sub(r'--zen-primary-color:\s*#[0-9a-fA-F]{6}', f'--zen-primary-color: {accent}', c)
            c = re.sub(r'(\.icon\s*\{\s*color:\s*)#[0-9a-fA-F]{6}', r'\g<1>' + accent, c)
            with open(content_file, 'w', encoding='utf-8') as f:
                f.write(c)
        except Exception:
            pass

    # 3. Update user.js
    ujs_file = os.path.join(d, 'user.js')
    if os.path.exists(ujs_file):
        try:
            with open(ujs_file, 'r', encoding='utf-8') as f:
                ujs = f.read()
            if 'zen.theme.accent-color' in ujs:
                ujs = re.sub(r'user_pref\("zen\.theme\.accent-color",\s*"[^"]*"\);', f'user_pref("zen.theme.accent-color", "{accent}");', ujs)
            else:
                ujs += f'\nuser_pref("zen.theme.accent-color", "{accent}");\n'
            with open(ujs_file, 'w', encoding='utf-8') as f:
                f.write(ujs)
        except Exception:
            pass

    # 4. Update prefs.js if present
    prefs_file = os.path.join(d, 'prefs.js')
    if os.path.exists(prefs_file):
        try:
            with open(prefs_file, 'r', encoding='utf-8') as f:
                pjs = f.read()
            if 'zen.theme.accent-color' in pjs:
                pjs = re.sub(r'user_pref\("zen\.theme\.accent-color",\s*"[^"]*"\);', f'user_pref("zen.theme.accent-color", "{accent}");', pjs)
            else:
                pjs += f'\nuser_pref("zen.theme.accent-color", "{accent}");\n'
            with open(prefs_file, 'w', encoding='utf-8') as f:
                f.write(pjs)
        except Exception:
            pass
PYEOF

# 10. Notify user of change
WALL_NAME=$(basename "$WALLPAPER")
if command -v dunstify >/dev/null 2>&1 && [ -n "$DISPLAY" ]; then
    dunstify -r 4444 -u normal -h string:x-dunst-stack-tag:wallpaper \
        "󰸉 Theme Synchronized" "Wallpaper: ${WALL_NAME}\nAccent: <span foreground='${ACCENT}'><b>${ACCENT}</b></span> | BG: <span foreground='${BG_DARK}'><b>${BG_DARK}</b></span>"
fi
