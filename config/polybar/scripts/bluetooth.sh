#!/usr/bin/env bash
# Polybar Bluetooth Widget Display Script

CONF_FILE="$HOME/.config/polybar/bluetooth.conf"
if [ -f "$CONF_FILE" ]; then
    # shellcheck source=/dev/null
    source "$CONF_FILE"
fi

SHOW_NAME="${SHOW_NAME:-true}"
SHOW_BATTERY="${SHOW_BATTERY:-true}"
DEVICE_ICONS="${DEVICE_ICONS:-true}"
HIDE_WHEN_OFF="${HIDE_WHEN_OFF:-false}"
MAX_NAME_LEN="${MAX_NAME_LEN:-14}"

ACCENT="#89b4fa"
if [ -f "$HOME/.config/theme/accent.color" ]; then
    ACCENT=$(cat "$HOME/.config/theme/accent.color" | tr -d ' \n\r')
fi

# Handle toggle action
if [ "$1" = "--toggle" ]; then
    if bluetoothctl show 2>/dev/null | grep -q "Powered: yes"; then
        bluetoothctl power off >/dev/null 2>&1 || true
        rfkill block bluetooth 2>/dev/null || true
        if command -v dunstify >/dev/null 2>&1; then
            dunstify -r 5566 -u normal -h string:x-dunst-stack-tag:bluetooth \
                "󰂲 Bluetooth Disabled" "Controller powered off"
        fi
    else
        rfkill unblock bluetooth 2>/dev/null || true
        sleep 0.15
        bluetoothctl power on >/dev/null 2>&1 || true
        if command -v dunstify >/dev/null 2>&1; then
            dunstify -r 5566 -u normal -h string:x-dunst-stack-tag:bluetooth \
                "󰂯 Bluetooth Enabled" "Controller powered on"
        fi
    fi
    exit 0
fi

# Check if controller exists and is powered on
if ! bluetoothctl show 2>/dev/null | grep -q "Powered: yes"; then
    if [ "$HIDE_WHEN_OFF" = "true" ]; then
        echo ""
    else
        echo "%{F#6c7086}󰂲%{F-} %{F#6c7086}off%{F-}"
    fi
    exit 0
fi

# Check connected devices
CONNECTED=$(bluetoothctl devices Connected 2>/dev/null | grep "^Device ")

if [ -z "$CONNECTED" ]; then
    # Powered on, but no active connection
    echo "%{F#89b4fa}󰂯%{F-} %{F#a6adc8}on%{F-}"
    exit 0
fi

# Count connected devices
COUNT=$(echo "$CONNECTED" | wc -l)

if [ "$COUNT" -eq 1 ]; then
    MAC=$(echo "$CONNECTED" | awk '{print $2}')
    NAME=$(echo "$CONNECTED" | cut -d' ' -f3-)

    ICON="󰂱"
    BAT=""

    if [ "$DEVICE_ICONS" = "true" ] || [ "$SHOW_BATTERY" = "true" ]; then
        DEV_INFO=$(bluetoothctl info "$MAC" 2>/dev/null)
        if [ "$DEVICE_ICONS" = "true" ]; then
            DEV_TYPE=$(echo "$DEV_INFO" | grep -m1 "Icon:" | awk '{print $2}')
            case "$DEV_TYPE" in
                *headset*|*audio*|*headphones*) ICON="󰋋" ;;
                *keyboard*)                     ICON="󰌌" ;;
                *mouse*)                        ICON="󰍽" ;;
                *gamepad*|*gaming*)             ICON="󰊴" ;;
                *phone*)                        ICON="󰏲" ;;
                *)                              ICON="󰂱" ;;
            esac
        fi
        if [ "$SHOW_BATTERY" = "true" ]; then
            BAT=$(echo "$DEV_INFO" | grep -i "Battery Percentage:" | grep -oE '\([0-9]+%\)' | tr -d '()%')
            if [ -z "$BAT" ]; then
                BAT=$(echo "$DEV_INFO" | grep -i "Battery Percentage:" | awk -F'0x' '{print $2}' | awk '{print $1}')
            fi
        fi
    fi

    if [ "$SHOW_NAME" = "true" ]; then
        if [ "${#NAME}" -gt "$MAX_NAME_LEN" ]; then
            NAME="${NAME:0:$((MAX_NAME_LEN - 1))}…"
        fi
        if [ -n "$BAT" ]; then
            echo "%{F${ACCENT}}$ICON%{F-} %{F#cdd6f4}${NAME} (${BAT}%)%{F-}"
        else
            echo "%{F${ACCENT}}$ICON%{F-} %{F#cdd6f4}${NAME}%{F-}"
        fi
    else
        if [ -n "$BAT" ]; then
            echo "%{F${ACCENT}}$ICON%{F-} %{F#cdd6f4}${BAT}%%{F-}"
        else
            echo "%{F${ACCENT}}$ICON%{F-}"
        fi
    fi
else
    echo "%{F${ACCENT}}󰂱%{F-} %{F#cdd6f4}${COUNT} devs%{F-}"
fi
