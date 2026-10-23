#!/usr/bin/env bash

# Merge Xresources and keymaps if present
[ -f /etc/X11/xinit/.Xresources ] && xrdb -merge /etc/X11/xinit/.Xresources
[ -f /etc/X11/xinit/.Xmodmap ] && xmodmap /etc/X11/xinit/.Xmodmap
[ -f "$HOME/.Xresources" ] && xrdb -merge "$HOME/.Xresources"
[ -f "$HOME/.Xmodmap" ] && xmodmap "$HOME/.Xmodmap"

# Restore wallpaper
[ -f "$HOME/.fehbg" ] && "$HOME/.fehbg" &

# Start i3 Window Manager
exec i3
