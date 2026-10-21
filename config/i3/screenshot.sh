#!/usr/bin/env bash
set -o pipefail

if [ "$1" = "full" ]; then
    if maim -u | xclip -selection clipboard -t image/png; then
        notify-send -t 1500 'Screenshot' 'Fullscreen copied to clipboard'
    fi
else
    # Release grace time for X11 grab
    sleep 0.15
    if maim -s -u | xclip -selection clipboard -t image/png; then
        notify-send -t 1500 'Screenshot' 'Cropped area copied to clipboard'
    fi
fi
