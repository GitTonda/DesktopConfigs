#!/usr/bin/env bash

# Adjust volume
case "$1" in
    up)
        pactl set-sink-volume @DEFAULT_SINK@ +5%
        ;;
    down)
        pactl set-sink-volume @DEFAULT_SINK@ -5%
        ;;
    mute)
        pactl set-sink-mute @DEFAULT_SINK@ toggle
        ;;
esac

# Query state
vol=$(pactl get-sink-volume @DEFAULT_SINK@ 2>/dev/null | grep -o -E '[0-9]+%' | head -n 1 | tr -d '%')
is_muted=$(pactl get-sink-mute @DEFAULT_SINK@ 2>/dev/null | grep -i "yes")

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
