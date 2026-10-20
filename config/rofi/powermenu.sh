#!/usr/bin/env bash

# Options
suspend="  Sleep"
reboot="  Reboot"
shutdown="  Power"
logout="  Logout"

options="$suspend\n$reboot\n$shutdown\n$logout"

chosen="$(echo -e "$options" | rofi -dmenu -i -p "󰐥 Power Menu" -theme ~/.config/rofi/powermenu.rasi)"

case "$chosen" in
    *"Sleep"*)
        systemctl suspend
        ;;
    *"Reboot"*)
        systemctl reboot
        ;;
    *"Power"*)
        systemctl poweroff
        ;;
    *"Logout"*)
        i3-msg exit
        ;;
esac
