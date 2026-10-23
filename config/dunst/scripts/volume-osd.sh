#!/usr/bin/env bash

# Query current volume before adjustment
current_vol=$(pactl get-sink-volume @DEFAULT_SINK@ 2>/dev/null | grep -o -E '[0-9]+%' | head -n 1 | tr -d '%')
current_vol=${current_vol:-50}

case "$1" in
    up)
        if [ "$current_vol" -ge 100 ]; then
            # Strictly cap at 100%
            pactl set-sink-volume @DEFAULT_SINK@ 100%
            new_vol=100
        else
            new_vol=$((current_vol + 5))
            if [ "$new_vol" -gt 100 ]; then
                new_vol=100
            fi
            pactl set-sink-volume @DEFAULT_SINK@ "${new_vol}%"
        fi
        ;;
    down)
        if [ "$current_vol" -gt 100 ]; then
            # If current volume was above 100%, bring immediately down into safe range
            new_vol=95
        else
            new_vol=$((current_vol - 5))
            if [ "$new_vol" -lt 0 ]; then
                new_vol=0
            fi
        fi
        pactl set-sink-volume @DEFAULT_SINK@ "${new_vol}%"
        ;;
    mute)
        pactl set-sink-mute @DEFAULT_SINK@ toggle
        ;;
esac

# Query state after adjustment
vol=$(pactl get-sink-volume @DEFAULT_SINK@ 2>/dev/null | grep -o -E '[0-9]+%' | head -n 1 | tr -d '%')
is_muted=$(pactl get-sink-mute @DEFAULT_SINK@ 2>/dev/null | grep -i "yes")

# Safety enforce: if still above 100%, clamp immediately
if [ -n "$vol" ] && [ "$vol" -gt 100 ]; then
    pactl set-sink-volume @DEFAULT_SINK@ 100%
    vol=100
fi

if [ -n "$is_muted" ]; then
    dunstify -a "OSD" -r 9991 -u normal -h string:x-dunst-stack-tag:volume_osd "󰝟 Volume: Muted" "Audio output is muted"
else
    vol=${vol:-0}
    if [ "$vol" -ge 65 ]; then
        icon="󰕾"
    elif [ "$vol" -ge 30 ]; then
        icon="󰖀"
    else
        icon="󰕿"
    fi
    dunstify -a "OSD" -r 9991 -u normal -h int:value:"$vol" -h string:x-dunst-stack-tag:volume_osd "$icon Volume: ${vol}%" ""
fi
