#!/usr/bin/env bash

# ==============================================================================
# Polybar GPU Performance Applet - Catppuccin Mocha Riced
# ==============================================================================

CLR_GREEN="#a6e3a1"
CLR_TEAL="#94e2d5"
CLR_BLUE="#89b4fa"
CLR_LAVENDER="#cba6f7"
CLR_YELLOW="#f9e2af"
CLR_PEACH="#fab387"
CLR_RED="#f38ba8"
CLR_TEXT="#cdd6f4"
CLR_DIM="#6c7086"

MODE_FILE="/tmp/polybar-gpu-mode"
[ -f "$MODE_FILE" ] || echo "0" > "$MODE_FILE"
MODE=$(cat "$MODE_FILE" 2>/dev/null || echo "0")

TOTAL_MODES=4

cycle_mode() {
    local dir="$1"
    local cur=$MODE
    local next=0
    if [ "$dir" = "prev" ]; then
        next=$(( (cur - 1 + TOTAL_MODES) % TOTAL_MODES ))
    else
        next=$(( (cur + 1) % TOTAL_MODES ))
    fi
    echo "$next" > "$MODE_FILE"

    local desc=""
    case "$next" in
        0) desc="Compact View (Load %)" ;;
        1) desc="Thermal View (Load % · Temp °C)" ;;
        2) desc="VRAM View (Load % · VRAM GB)" ;;
        3) desc="Pro Telemetry (Load · Temp · VRAM · Power)" ;;
    esac

    if command -v dunstify >/dev/null 2>&1; then
        dunstify -a "GPU Monitor" -r 9945 -t 1500 -u low -h string:x-dunst-stack-tag:gpu_mode \
            "󰢮 GPU Display Mode" "$desc"
    fi
    # Instantly trigger polybar update
    polybar-msg action "#gpu.hook.0" 2>/dev/null || true
    exit 0
}

if [ "$1" = "--toggle-mode" ] || [ "$1" = "--next-mode" ]; then
    cycle_mode "next"
elif [ "$1" = "--prev-mode" ]; then
    cycle_mode "prev"
fi

# Middle-click rich OSD notification
if [ "$1" = "--notify" ]; then
    if command -v nvidia-smi >/dev/null 2>&1; then
        INFO=$(nvidia-smi --query-gpu=name,driver_version,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw,power.limit,fan.speed,clocks.current.graphics,clocks.max.graphics --format=csv,noheader,nounits 2>/dev/null)
        if [ -n "$INFO" ]; then
            IFS=',' read -r NAME DRIVER TEMP UTIL VRAM_U VRAM_T POWER POWER_LIM FAN CLK CLK_MAX <<< "$INFO"
            NAME=$(echo "$NAME" | xargs)
            DRIVER=$(echo "$DRIVER" | xargs)
            TEMP=$(echo "$TEMP" | xargs)
            UTIL=$(echo "$UTIL" | xargs)
            VRAM_U=$(echo "$VRAM_U" | xargs)
            VRAM_T=$(echo "$VRAM_T" | xargs)
            POWER=$(echo "$POWER" | xargs)
            POWER_LIM=$(echo "$POWER_LIM" | xargs)
            FAN=$(echo "$FAN" | xargs)
            CLK=$(echo "$CLK" | xargs)
            CLK_MAX=$(echo "$CLK_MAX" | xargs)

            VRAM_GB=$(awk "BEGIN {printf \"%.1f\", $VRAM_U / 1024}")
            VRAM_TOT_GB=$(awk "BEGIN {printf \"%.1f\", $VRAM_T / 1024}")
            VRAM_PCT=$(awk "BEGIN {printf \"%d\", ($VRAM_U / $VRAM_T) * 100}")
            POWER_W=$(awk "BEGIN {printf \"%.0f\", $POWER}")
            POWER_MAX_W=$(awk "BEGIN {printf \"%.0f\", $POWER_LIM}")

            dunstify -a "GPU Monitor" -r 9944 -u normal -h int:value:"$UTIL" -h string:x-dunst-stack-tag:gpu_status \
                "󰢮 $NAME" "󰍛 Load: <b>${UTIL}%</b>  ·  󱤓 Temp: <b>${TEMP}°C</b>\n󰘚 VRAM: <b>${VRAM_GB}GB</b> / ${VRAM_TOT_GB}GB (${VRAM_PCT}%)\n󱐋 Power: <b>${POWER_W}W</b> / ${POWER_MAX_W}W  ·  󰈐 Fan: <b>${FAN}%</b>\n󰚥 Driver: <b>${DRIVER}</b>  ·  󰓅 Clock: <b>${CLK}MHz</b>"
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
            dunstify -a "GPU Monitor" -r 9944 -u normal -h int:value:"${UTIL:-0}" -h string:x-dunst-stack-tag:gpu_status \
                "󰢮 GPU Status" "<b>Load:</b> ${UTIL}%  ·  <b>Temp:</b> ${TEMP}"
            exit 0
        fi
    done

    dunstify -a "GPU Monitor" -r 9944 -u normal "󰢮 GPU Status" "No active GPU detected"
    exit 0
fi

UTIL=""
TEMP=""
VRAM=""
POWER=""

# 1. Check NVIDIA
if command -v nvidia-smi >/dev/null 2>&1; then
    NVIDIA_DATA=$(nvidia-smi --query-gpu=utilization.gpu,temperature.gpu,memory.used,power.draw --format=csv,noheader,nounits 2>/dev/null)
    if [ -n "$NVIDIA_DATA" ]; then
        IFS=',' read -r UTIL TEMP VRAM POWER <<< "$NVIDIA_DATA"
        UTIL=$(echo "$UTIL" | xargs)
        TEMP=$(echo "$TEMP" | xargs)
        VRAM=$(echo "$VRAM" | xargs)
        POWER=$(echo "$POWER" | xargs)
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

[ -z "$UTIL" ] && exit 0

# Dynamic colors based on thresholds
ICON="󰢮"
ICON_CLR="$CLR_GREEN"

if [ -n "$TEMP" ]; then
    if [ "$TEMP" -ge 80 ]; then
        ICON="󰈸"
        ICON_CLR="$CLR_RED"
        TEMP_CLR="$CLR_RED"
    elif [ "$TEMP" -ge 70 ]; then
        ICON_CLR="$CLR_PEACH"
        TEMP_CLR="$CLR_PEACH"
    elif [ "$TEMP" -ge 55 ]; then
        ICON_CLR="$CLR_YELLOW"
        TEMP_CLR="$CLR_YELLOW"
    elif [ "$TEMP" -ge 42 ]; then
        ICON_CLR="$CLR_BLUE"
        TEMP_CLR="$CLR_BLUE"
    else
        ICON_CLR="$CLR_GREEN"
        TEMP_CLR="$CLR_GREEN"
    fi
else
    TEMP_CLR="$CLR_GREEN"
fi

if [ "$UTIL" -ge 85 ]; then
    UTIL_CLR="$CLR_RED"
elif [ "$UTIL" -ge 65 ]; then
    UTIL_CLR="$CLR_PEACH"
elif [ "$UTIL" -ge 40 ]; then
    UTIL_CLR="$CLR_YELLOW"
else
    UTIL_CLR="$CLR_TEXT"
fi

case "$MODE" in
    1)
        # Load & Temperature
        if [ -n "$TEMP" ]; then
            printf "%%{F%s}%s%%{F-} %%{F%s}%2d%%%%{F-} %%{F%s}·%%{F-} %%{F%s}%d°C%%{F-}\n" "$ICON_CLR" "$ICON" "$UTIL_CLR" "$UTIL" "$CLR_DIM" "$TEMP_CLR" "$TEMP"
        else
            printf "%%{F%s}%s%%{F-} %%{F%s}%2d%%%%{F-}\n" "$ICON_CLR" "$ICON" "$UTIL_CLR" "$UTIL"
        fi
        ;;
    2)
        # Load & VRAM
        if [ -n "$VRAM" ]; then
            VRAM_GB=$(awk "BEGIN {printf \"%.1fG\", $VRAM / 1024}")
            printf "%%{F%s}%s%%{F-} %%{F%s}%2d%%%%{F-} %%{F%s}·%%{F-} %%{F%s}%s%%{F-}\n" "$ICON_CLR" "$ICON" "$UTIL_CLR" "$UTIL" "$CLR_DIM" "$CLR_LAVENDER" "$VRAM_GB"
        else
            printf "%%{F%s}%s%%{F-} %%{F%s}%2d%%%%{F-}\n" "$ICON_CLR" "$ICON" "$UTIL_CLR" "$UTIL"
        fi
        ;;
    3)
        # Pro Telemetry: Load · Temp · VRAM · Power
        VRAM_GB=$(awk "BEGIN {printf \"%.1fG\", ${VRAM:-0} / 1024}")
        POWER_W=$(awk "BEGIN {printf \"%.0fW\", ${POWER:-0}}")
        if [ -n "$TEMP" ] && [ -n "$VRAM" ] && [ -n "$POWER" ]; then
            printf "%%{F%s}%s%%{F-} %%{F%s}%2d%%%%{F-} %%{F%s}·%%{F-} %%{F%s}%d°C%%{F-} %%{F%s}·%%{F-} %%{F%s}%s%%{F-} %%{F%s}·%%{F-} %%{F%s}%s%%{F-}\n" "$ICON_CLR" "$ICON" "$UTIL_CLR" "$UTIL" "$CLR_DIM" "$TEMP_CLR" "$TEMP" "$CLR_DIM" "$CLR_LAVENDER" "$VRAM_GB" "$CLR_DIM" "$CLR_YELLOW" "$POWER_W"
        else
            printf "%%{F%s}%s%%{F-} %%{F%s}%2d%%%%{F-}\n" "$ICON_CLR" "$ICON" "$UTIL_CLR" "$UTIL"
        fi
        ;;
    *)
        # Default: Compact Load % with Dynamic Icon & Value Color
        printf "%%{F%s}%s%%{F-} %%{F%s}%2d%%%%{F-}\n" "$ICON_CLR" "$ICON" "$UTIL_CLR" "$UTIL"
        ;;
esac
