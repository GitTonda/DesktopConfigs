#!/usr/bin/env bash

# Check if hardware backlight exists (laptops)
HAS_BACKLIGHT=false
if [ -d "/sys/class/backlight" ] && [ -n "$(ls -A /sys/class/backlight 2>/dev/null)" ]; then
    HAS_BACKLIGHT=true
fi

if [ "$HAS_BACKLIGHT" = "true" ] && command -v brightnessctl >/dev/null 2>&1; then
    case "$1" in
        up)   brightnessctl set +10% -q ;;
        down) brightnessctl set 10%- -q ;;
    esac
    percent=$(brightnessctl -m 2>/dev/null | cut -d, -f4 | tr -d '%')
    percent=${percent:-100}
else
    # Fallback to xrandr software brightness for external desktop monitors
    curr=$(xrandr --verbose 2>/dev/null | grep -m1 -i "Brightness:" | awk '{print $2}')
    curr=${curr:-1.0}

    case "$1" in
        up)
            new=$(python3 -c "print(min(1.0, round($curr + 0.1, 2)))")
            ;;
        down)
            new=$(python3 -c "print(max(0.2, round($curr - 0.1, 2)))")
            ;;
        *)
            new="$curr"
            ;;
    esac

    for mon in $(xrandr 2>/dev/null | grep " connected" | awk '{print $1}'); do
        xrandr --output "$mon" --brightness "$new" 2>/dev/null || true
    done

    percent=$(python3 -c "print(int(float('$new') * 100))")
fi

if [ "$percent" -ge 65 ]; then
    icon="󰃠"
elif [ "$percent" -ge 30 ]; then
    icon="󰃟"
else
    icon="󰃞"
fi

dunstify -a "OSD" -r 9992 -u normal -h int:value:"$percent" -h string:x-dunst-stack-tag:brightness_osd "$icon Brightness: ${percent}%" ""
