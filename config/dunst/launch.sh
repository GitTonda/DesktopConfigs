#!/usr/bin/env bash

# Dynamic Dunst Geometry & Lifecycle Daemon
# Adapts notification position dynamically to any screen resolution, DPI, Polybar height, and i3 gaps.

sleep 0.2

# 1. Dynamically detect Polybar height from X11 window tree
POLY_H=35
if command -v xdotool >/dev/null 2>&1 && command -v xwininfo >/dev/null 2>&1; then
    POLY_WINS=$(xdotool search --class polybar 2>/dev/null || true)
    for win in $POLY_WINS; do
        h=$(xwininfo -id "$win" 2>/dev/null | grep -i "Height:" | awk '{print $2}')
        if [ -n "$h" ] && [ "$h" -gt 10 ]; then
            POLY_H="$h"
            break
        fi
    done
fi

# 2. Dynamically parse i3 gaps and border settings
I3_CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/i3/config"
GAPS_INNER=5
GAPS_OUTER=2
BORDER_PX=2

if [ -f "$I3_CONFIG" ]; then
    val_inner=$(grep -E '^\s*gaps\s+inner' "$I3_CONFIG" | head -n 1 | awk '{print $3}')
    val_outer=$(grep -E '^\s*gaps\s+outer' "$I3_CONFIG" | head -n 1 | awk '{print $3}')
    val_border=$(grep -E '^\s*default_border\s+pixel' "$I3_CONFIG" | head -n 1 | awk '{print $3}')

    [ -n "$val_inner" ] && GAPS_INNER="$val_inner"
    [ -n "$val_outer" ] && GAPS_OUTER="$val_outer"
    [ -n "$val_border" ] && BORDER_PX="$val_border"
fi

# 3. Calculate margin dynamically:
# Window edge = inner_gap + outer_gap + border
TOTAL_EDGE=$(( GAPS_INNER + GAPS_OUTER + BORDER_PX ))
PADDING=8

OFFSET_X=$(( TOTAL_EDGE + PADDING ))
OFFSET_Y=$(( POLY_H + TOTAL_EDGE + PADDING ))

DUNST_CONFIG="${XDG_CONFIG_HOME:-$HOME/.config}/dunst/dunstrc"
if [ -f "$DUNST_CONFIG" ]; then
    sed -i -E "s/^\s*offset\s*=\s*[0-9]+x[0-9]+/    offset = ${OFFSET_X}x${OFFSET_Y}/" "$DUNST_CONFIG"
fi

# 4. Start or reload Dunst
if pgrep -u "$UID" -x dunst >/dev/null 2>&1; then
    dunstctl reload 2>/dev/null || (killall -q dunst 2>/dev/null; nohup dunst >/dev/null 2>&1 & disown)
else
    nohup dunst >/dev/null 2>&1 & disown
fi
