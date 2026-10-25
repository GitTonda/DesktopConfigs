#!/usr/bin/env bash
set -e

RULES_FILE="$HOME/.config/openrgb/60-openrgb.rules"

if [ ! -f "$RULES_FILE" ]; then
    openrgb --generate-udev-rules "$RULES_FILE"
fi

echo "==> Installing OpenRGB udev rules into /etc/udev/rules.d/..."
sudo cp "$RULES_FILE" /etc/udev/rules.d/60-openrgb.rules
echo "==> Reloading udev rules..."
sudo udevadm control --reload-rules
sudo udevadm trigger
echo "✔ Successfully authorized hardware RGB access for Fans, RAM, and GPU!"
