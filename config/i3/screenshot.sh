#!/usr/bin/env bash
set -o pipefail

notify() {
    if command -v dunstify >/dev/null 2>&1; then
        dunstify -t 1500 "$1" "$2"
    elif command -v notify-send >/dev/null 2>&1; then
        notify-send -t 1500 "$1" "$2"
    fi
}

if [ "$1" = "full" ]; then
    if maim -u | xclip -selection clipboard -t image/png; then
        notify 'Screenshot' 'Fullscreen copied to clipboard'
    fi
else
    # Release grace time for X11 grab
    sleep 0.15
    if maim -s -u | xclip -selection clipboard -t image/png; then
        notify 'Screenshot' 'Cropped area copied to clipboard'
    fi
fi
