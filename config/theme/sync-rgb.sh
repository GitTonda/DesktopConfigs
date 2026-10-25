#!/usr/bin/env bash
# ==============================================================================
# PC Hardware RGB Lighting Synchronization
# Syncs Motherboard ARGB Fans, RAM, and GPU with active wallpaper accent color.
# ==============================================================================

COLOR="$1"
if [ -z "$COLOR" ]; then
    if [ -f "$HOME/.config/theme/accent.color" ]; then
        COLOR=$(cat "$HOME/.config/theme/accent.color" | tr -d ' \n\r')
    else
        COLOR="#51c1d2"
    fi
fi

# Clean hex format (strip leading #)
HEX="${COLOR#'#'}"

if command -v openrgb >/dev/null 2>&1; then
    # Device 3 is MSI PRO B660M-A Motherboard. Zone 1 (JRAINBOW1) & Zone 2 (JRAINBOW2)
    # control ARGB case fans. Sizing them to 40 LEDs enables full lighting addressability.
    (
        openrgb --noautoconnect --device 3 --zone 1 --size 40 --device 3 --zone 2 --size 40 --mode Static -c "$HEX" >/dev/null 2>&1
        openrgb --noautoconnect -c "$HEX" >/dev/null 2>&1
    ) &
    if command -v dunstify >/dev/null 2>&1 && [ -n "$DISPLAY" ]; then
        dunstify -a "Hardware RGB" -r 4455 -u normal -h string:x-dunst-stack-tag:rgb_sync \
            "󰸉 Hardware RGB Synchronized" "Applied accent color <span foreground='#${HEX}'><b>#${HEX}</b></span> to Fans, RAM, and GPU"
    fi
fi
