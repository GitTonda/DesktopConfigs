#!/usr/bin/env bash

MODE_FILE="/tmp/polybar-gpu-mode"
[ -f "$MODE_FILE" ] || echo "0" > "$MODE_FILE"
MODE=$(cat "$MODE_FILE" 2>/dev/null || echo "0")

if [ "$1" = "--toggle-mode" ]; then
    NEXT_MODE=$(( (MODE + 1) % 3 ))
    echo "$NEXT_MODE" > "$MODE_FILE"
    case "$NEXT_MODE" in
        0) dunstify -a "GPU Monitor" -r 9945 -t 1500 -u low "󰢮 GPU Display" "Modalità: Carico (%)" ;;
        1) dunstify -a "GPU Monitor" -r 9945 -t 1500 -u low "󰢮 GPU Display" "Modalità: Carico e Temp (% °C)" ;;
        2) dunstify -a "GPU Monitor" -r 9945 -t 1500 -u low "󰢮 GPU Display" "Modalità: Carico e VRAM (% GB)" ;;
    esac
    exit 0
fi

if [ "$1" = "--notify" ]; then
    if command -v nvidia-smi >/dev/null 2>&1; then
        INFO=$(nvidia-smi --query-gpu=name,driver_version,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw,fan.speed --format=csv,noheader,nounits 2>/dev/null)
        if [ -n "$INFO" ]; then
            IFS=',' read -r NAME DRIVER TEMP UTIL VRAM_U VRAM_T POWER FAN <<< "$INFO"
            NAME=$(echo "$NAME" | xargs)
            TEMP=$(echo "$TEMP" | xargs)
            UTIL=$(echo "$UTIL" | xargs)
            VRAM_U=$(echo "$VRAM_U" | xargs)
            VRAM_T=$(echo "$VRAM_T" | xargs)
            POWER=$(echo "$POWER" | xargs)
            FAN=$(echo "$FAN" | xargs)

            VRAM_GB=$(awk "BEGIN {printf \"%.1f\", $VRAM_U / 1024}")
            VRAM_TOT_GB=$(awk "BEGIN {printf \"%.1f\", $VRAM_T / 1024}")
            POWER_W=$(awk "BEGIN {printf \"%.0f\", $POWER}")

            dunstify -a "GPU Monitor" -r 9944 -u normal -h string:x-dunst-stack-tag:gpu_status \
                "󰢮 $NAME" "Carico: <b>${UTIL}%</b>  ·  Temp: <b>${TEMP}°C</b>  ·  Ventola: <b>${FAN}%</b>\nVRAM: <b>${VRAM_GB}GB</b> / ${VRAM_TOT_GB}GB  ·  Potenza: <b>${POWER_W}W</b>"
            exit 0
        fi
    fi

    # Fallback to AMD/Intel DRM
    for card in /sys/class/drm/card*/device/gpu_busy_percent; do
        if [ -f "$card" ]; then
            UTIL=$(cat "$card" 2>/dev/null)
            TEMP="N/A"
            for t in $(dirname "$card")/hwmon/hwmon*/temp1_input; do
                if [ -f "$t" ]; then
                    RAW_TEMP=$(cat "$t" 2>/dev/null)
                    TEMP="$((RAW_TEMP / 1000))°C"
                    break
                fi
            done
            dunstify -a "GPU Monitor" -r 9944 -u normal -h string:x-dunst-stack-tag:gpu_status \
                "󰢮 GPU Status" "Carico: <b>${UTIL}%</b>  ·  Temp: <b>${TEMP}</b>"
            exit 0
        fi
    done

    dunstify -a "GPU Monitor" -r 9944 -u normal "󰢮 GPU Status" "Nessuna GPU rilevata"
    exit 0
fi

UTIL=""
TEMP=""
VRAM=""

# 1. Check NVIDIA
if command -v nvidia-smi >/dev/null 2>&1; then
    NVIDIA_DATA=$(nvidia-smi --query-gpu=utilization.gpu,temperature.gpu,memory.used --format=csv,noheader,nounits 2>/dev/null)
    if [ -n "$NVIDIA_DATA" ]; then
        IFS=',' read -r UTIL TEMP VRAM <<< "$NVIDIA_DATA"
        UTIL=$(echo "$UTIL" | xargs)
        TEMP=$(echo "$TEMP" | xargs)
        VRAM=$(echo "$VRAM" | xargs)
    fi
fi

# 2. Fallback to AMD sysfs
if [ -z "$UTIL" ]; then
    for card in /sys/class/drm/card*/device/gpu_busy_percent; do
        if [ -f "$card" ]; then
            UTIL=$(cat "$card" 2>/dev/null)
            for t in $(dirname "$card")/hwmon/hwmon*/temp1_input; do
                if [ -f "$t" ]; then
                    RAW_TEMP=$(cat "$t" 2>/dev/null)
                    TEMP=$((RAW_TEMP / 1000))
                    break
                fi
            done
            break
        fi
    done
fi

if [ -z "$UTIL" ]; then
    exit 0
fi

case "$MODE" in
    1)
        if [ -n "$TEMP" ]; then
            printf "%2d%% %d°C\n" "$UTIL" "$TEMP"
        else
            printf "%2d%%\n" "$UTIL"
        fi
        ;;
    2)
        if [ -n "$VRAM" ]; then
            VRAM_GB=$(awk "BEGIN {printf \"%.1fG\", $VRAM / 1024}")
            printf "%2d%% %s\n" "$UTIL" "$VRAM_GB"
        else
            printf "%2d%%\n" "$UTIL"
        fi
        ;;
    *)
        printf "%2d%%\n" "$UTIL"
        ;;
esac
