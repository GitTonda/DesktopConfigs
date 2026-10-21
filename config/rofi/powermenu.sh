#!/usr/bin/env bash

# Terminal-styled Power Actions
opt_sleep="[1]  󰤄  sleep      · suspend session to RAM"
opt_reboot="[2]  󰑓  reboot     · reboot operating system"
opt_shutdown="[3]  󰐥  poweroff   · shutdown and turn off PC"
opt_logout="[4]  󰍃  logout     · terminate current session"

options="${opt_sleep}\n${opt_reboot}\n${opt_shutdown}\n${opt_logout}"

chosen="$(echo -e "$options" | rofi -dmenu -i -p "󰐥 systemctl :~$" -theme ~/.config/rofi/powermenu.rasi)"

case "$chosen" in
    *"sleep"*|*"Sleep"*|*"[1]"*)
        systemctl suspend
        ;;
    *"reboot"*|*"Reboot"*|*"[2]"*)
        systemctl reboot
        ;;
    *"poweroff"*|*"Power"*|*"shutdown"*|*"[3]"*)
        systemctl poweroff
        ;;
    *"logout"*|*"Logout"*|*"exit"*|*"[4]"*)
        i3-msg exit
        ;;
esac
