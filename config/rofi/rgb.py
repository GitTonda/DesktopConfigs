#!/usr/bin/env python3
"""
Rofi Hardware RGB Lighting Dashboard
Synchronizes and controls Motherboard ARGB Fans, RAM, and GPU.
"""

import sys
import os
import subprocess
import shutil
import re


ROFI_THEME = os.path.expanduser("~/.config/rofi/rgb.rasi")


def get_current_accent():
    path = os.path.expanduser("~/.config/theme/accent.color")
    if os.path.exists(path):
        try:
            with open(path, "r") as f:
                return f.read().strip()
        except Exception:
            pass
    return "#51c1d2"


def notify(title, message, urgency="normal"):
    if shutil.which("dunstify"):
        subprocess.run([
            "dunstify", "-a", "RGB Controller",
            "-r", "4456",
            "-u", urgency,
            "-h", "string:x-dunst-stack-tag:rgb_status",
            title, message
        ], check=False)
    elif shutil.which("notify-send"):
        subprocess.run(["notify-send", "-u", urgency, title, message], check=False)


def run_rofi(prompt, items, preselect=None):
    cmd = ["rofi", "-dmenu", "-i", "-p", prompt, "-theme", ROFI_THEME]
    if preselect is not None:
        cmd.extend(["-selected-row", str(preselect)])
    input_str = "\n".join(items) if isinstance(items, list) else items
    res = subprocess.run(cmd, input=input_str, stdout=subprocess.PIPE, text=True, check=False)
    if res.returncode == 0:
        return res.stdout.strip()
    return None


def apply_color(hex_code, label="Custom Color"):
    clean_hex = hex_code.lstrip("#")
    script_path = os.path.expanduser("~/.config/theme/sync-rgb.sh")
    if os.path.exists(script_path):
        subprocess.run([script_path, f"#{clean_hex}"], check=False)
    else:
        subprocess.run(["openrgb", "--noautoconnect", "-m", "static", "-c", clean_hex], check=False)
    notify(f"󰸉 Hardware RGB: {label}", f"Applied color <span foreground='#{clean_hex}'><b>#{clean_hex}</b></span> to Fans, RAM, and GPU")


def main():
    accent = get_current_accent()

    items = [
        f"󰸉  Sync with Wallpaper Accent ({accent})",
        "────────────────────────────────────────────────────────────",
        "󰏘  Cyan          (#51c1d2)",
        "󰏘  Sky Blue      (#89b4fa)",
        "󰏘  Lavender      (#cba6f7)",
        "󰏘  Mint Green    (#a6e3a1)",
        "󰏘  Warm Peach    (#fab387)",
        "󰏘  Crimson Red   (#f38ba8)",
        "󰏘  Gold Yellow   (#f9e2af)",
        "󰏘  Pure White    (#ffffff)",
        "󰐥  Stealth Mode  (Turn LEDs OFF)",
        "────────────────────────────────────────────────────────────",
        "󰒓  Launch OpenRGB GUI Studio",
        "󰑐  Refresh RGB Status"
    ]

    choice = run_rofi("󰸉 rgb lights :~$", items)
    if not choice:
        return

    # Check if user typed a direct hex color e.g. "#ff0055" or "00ffcc"
    m = re.match(r"^#?([0-9a-fA-F]{6})$", choice.strip())
    if m:
        hex_val = m.group(1)
        apply_color(hex_val, f"#{hex_val}")
        return

    if "Sync with Wallpaper Accent" in choice:
        apply_color(accent, "System Wallpaper Accent")
    elif "Cyan" in choice:
        apply_color("51c1d2", "Cyan")
    elif "Sky Blue" in choice:
        apply_color("89b4fa", "Sky Blue")
    elif "Lavender" in choice:
        apply_color("cba6f7", "Lavender")
    elif "Mint Green" in choice:
        apply_color("a6e3a1", "Mint Green")
    elif "Warm Peach" in choice:
        apply_color("fab387", "Warm Peach")
    elif "Crimson Red" in choice:
        apply_color("f38ba8", "Crimson Red")
    elif "Gold Yellow" in choice:
        apply_color("f9e2af", "Gold Yellow")
    elif "Pure White" in choice:
        apply_color("ffffff", "Pure White")
    elif "Stealth Mode" in choice:
        apply_color("000000", "Stealth Mode (OFF)")
    elif "Launch OpenRGB GUI Studio" in choice:
        subprocess.Popen(["openrgb", "--gui"])
    elif "Refresh" in choice:
        main()


if __name__ == "__main__":
    main()
