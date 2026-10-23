#!/usr/bin/env bash

# Adjust brightness
case "$1" in
    up)
        brightnessctl set +10% -q
        ;;
    down)
        brightnessctl set 10%- -q
        ;;
esac

# Query state
percent=$(brightnessctl -m 2>/dev/null | cut -d, -f4 | tr -d '%')
percent=${percent:-0}

if [ "$percent" -ge 65 ]; then
    icon="󰃠"
elif [ "$percent" -ge 30 ]; then
    icon="󰃟"
else
    icon="󰃞"
fi

dunstify -a "OSD" -r 9992 -u normal -h int:value:"$percent" -h string:x-dunst-stack-tag:brightness_osd "$icon Brightness: ${percent}%" ""
