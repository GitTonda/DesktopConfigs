#!/usr/bin/env bash

# Prevent duplicate lock instances
pidof i3lock >/dev/null && exit 0

# Retrieve dynamic theme colors
ACCENT_HEX="#ffaa45"
BG_HEX="#171411"
[ -f "$HOME/.config/theme/accent.color" ] && ACCENT_HEX="$(cat "$HOME/.config/theme/accent.color" | tr -d ' \r\n')"
[ -f "$HOME/.config/theme/bg.color" ] && BG_HEX="$(cat "$HOME/.config/theme/bg.color" | tr -d ' \r\n')"

ACCENT="${ACCENT_HEX#'#'}"
BG="${BG_HEX#'#'}"

# Ensure lockscreen background image cache exists
CACHE_IMG="$HOME/.cache/lockscreen.png"
if [ ! -f "$CACHE_IMG" ]; then
    mkdir -p "$HOME/.cache"
    WALLPAPER=""
    if [ -f "$HOME/.fehbg" ]; then
        WALLPAPER="$(grep -o "'.*'" "$HOME/.fehbg" 2>/dev/null | head -n 1 | tr -d "'")"
    fi
    if [ -f "$WALLPAPER" ]; then
        magick "$WALLPAPER" -filter Gaussian -resize 1920x1080^ -gravity center -extent 1920x1080 -blur 0x8 -fill "#11111b" -colorize 25% "$CACHE_IMG" 2>/dev/null || true
    fi
fi

IMG_ARGS=()
if [ -f "$CACHE_IMG" ]; then
    IMG_ARGS=(-i "$CACHE_IMG" -F)
else
    IMG_ARGS=(-B 5)
fi

exec i3lock -n "${IMG_ARGS[@]}" \
  --clock \
  --indicator \
  --radius=125 \
  --ring-width=7 \
  --inside-color=181825cc \
  --ring-color=31324488 \
  --keyhl-color="${ACCENT}ff" \
  --bshl-color=f38ba8ff \
  --insidever-color=89b4facc \
  --ringver-color=89b4faff \
  --insidewrong-color=f38ba8cc \
  --ringwrong-color=f38ba8ff \
  --line-color=00000000 \
  --separator-color=00000000 \
  --time-color=cdd6f4ff \
  --date-color=a6adc8ff \
  --layout-color=cdd6f4ff \
  --verif-color=89b4faff \
  --wrong-color=f38ba8ff \
  --modif-color=fab387ff \
  --time-font="JetBrainsMono Nerd Font" \
  --date-font="JetBrainsMono Nerd Font" \
  --verif-font="JetBrainsMono Nerd Font" \
  --wrong-font="JetBrainsMono Nerd Font" \
  --time-size=30 \
  --date-size=12 \
  --verif-size=13 \
  --wrong-size=13 \
  --time-str="%H:%M:%S" \
  --date-str="%A, %d %B %Y" \
  --verif-text="Verifying..." \
  --wrong-text="Wrong Password" \
  --noinput-text="" \
  --lock-text="Locking..." \
  --lockfailed-text="Lock Failed" \
  --ind-pos="x+w/2:y+h/2" \
  --time-pos="ix:iy-18" \
  --date-pos="ix:iy+22" \
  --ignore-empty-password \
  --show-failed-attempts \
  --pass-media-keys \
  --pass-volume-keys \
  --pass-screen-keys \
  --pass-power-keys
