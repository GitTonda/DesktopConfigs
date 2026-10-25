#!/usr/bin/env python3
"""
Rofi Mouse Cursor Theme Selector
Instantly switch between sleek, minimalist, and system-styled cursor sets.
"""

import sys
import os
import subprocess
import shutil


ROFI_THEME = os.path.expanduser("~/.config/rofi/cursor.rasi")

PRESETS = [
    {
        "id": "Bibata-Modern-Classic",
        "name": "Bibata Modern Classic",
        "desc": "Minimalist Material Dark with crisp white outline (Recommended)",
        "icon": "󰍽"
    },
    {
        "id": "Bibata-Modern-Ice",
        "name": "Bibata Modern Ice",
        "desc": "Minimalist Material White with sharp dark outline",
        "icon": "󰍽"
    },
    {
        "id": "Nordzy-cursors",
        "name": "Nordzy Dark",
        "desc": "Geometric Nordic Dark minimalist cursor",
        "icon": "󰍽"
    },
    {
        "id": "Qogir-Cursors",
        "name": "Qogir Dark",
        "desc": "Streamlined modern curvature with subtle drop shadow",
        "icon": "󰍽"
    },
    {
        "id": "catppuccin-mocha-dark-cursors",
        "name": "Catppuccin Mocha Dark",
        "desc": "Neutral dark Mocha palette without bright pastel colors",
        "icon": "󰍽"
    },
    {
        "id": "catppuccin-mocha-teal-cursors",
        "name": "Catppuccin Mocha Teal",
        "desc": "Mocha dark with Cyan / Teal glowing accent",
        "icon": "󰍽"
    },
    {
        "id": "catppuccin-mocha-blue-cursors",
        "name": "Catppuccin Mocha Blue",
        "desc": "Mocha dark with Sky Blue accent",
        "icon": "󰍽"
    },
    {
        "id": "catppuccin-mocha-lavender-cursors",
        "name": "Catppuccin Mocha Lavender",
        "desc": "Mocha dark with Lavender / Purple accent",
        "icon": "󰍽"
    },
    {
        "id": "Adwaita",
        "name": "Adwaita Default",
        "desc": "Standard GNOME system default cursor",
        "icon": "󰍽"
    }
]


def notify(title, message, urgency="normal"):
    if shutil.which("dunstify"):
        subprocess.run([
            "dunstify", "-a", "Cursor Settings",
            "-r", "4488",
            "-u", urgency,
            "-h", "string:x-dunst-stack-tag:cursor_theme",
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


def get_current_theme():
    # Check ~/.icons/default/index.theme
    idx_path = os.path.expanduser("~/.icons/default/index.theme")
    if os.path.exists(idx_path):
        try:
            with open(idx_path, "r") as f:
                for line in f:
                    if line.startswith("Inherits="):
                        return line.split("=", 1)[1].strip()
        except Exception:
            pass

    try:
        out = subprocess.check_output(
            ["gsettings", "get", "org.gnome.desktop.interface", "cursor-theme"],
            text=True, stderr=subprocess.DEVNULL
        ).strip().strip("'\"")
        if out:
            return out
    except Exception:
        pass
    return "Bibata-Modern-Classic"


def apply_cursor_theme(theme_id, theme_name):
    home = os.path.expanduser("~")

    # 1. Update index.theme in ~/.icons and ~/.local/share/icons
    for p in [f"{home}/.icons/default/index.theme", f"{home}/.local/share/icons/default/index.theme"]:
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w") as f:
            f.write(f"[Icon Theme]\nName=Default\nComment=Default Cursor Theme\nInherits={theme_id}\n")

    # 2. Update ~/.Xresources
    xres_path = f"{home}/.Xresources"
    with open(xres_path, "w") as f:
        f.write(f"Xcursor.theme: {theme_id}\nXcursor.size: 24\n")
    subprocess.run(["xrdb", "-merge", xres_path], check=False)

    # 3. Update GTK 3 & GTK 4
    for gtk_ver in ["gtk-3.0", "gtk-4.0"]:
        gtk_path = f"{home}/.config/{gtk_ver}/settings.ini"
        os.makedirs(os.path.dirname(gtk_path), exist_ok=True)
        with open(gtk_path, "w") as f:
            f.write(
                f"[Settings]\n"
                f"gtk-theme-name=Adwaita-dark\n"
                f"gtk-icon-theme-name=Papirus-Dark\n"
                f"gtk-cursor-theme-name={theme_id}\n"
                f"gtk-cursor-theme-size=24\n"
                f"gtk-font-name=JetBrainsMono Nerd Font 10\n"
                f"gtk-application-prefer-dark-theme=1\n"
            )

    # 4. GSettings (Portal / Flatpaks / GNOME apps)
    subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "cursor-theme", theme_id], check=False)
    subprocess.run(["gsettings", "set", "org.gnome.desktop.interface", "cursor-size", "24"], check=False)

    # 5. X11 root window pointer update
    subprocess.run(["xsetroot", "-cursor_name", "left_ptr"], check=False)

    notify("󰍽 Cursor Theme Applied", f"Active Cursor: <b>{theme_name}</b>\n(Changes take effect immediately)")


def main():
    curr = get_current_theme()
    items = []
    preselect_idx = 0

    for idx, p in enumerate(PRESETS):
        is_active = p["id"] == curr
        status_prefix = "󰄬 " if is_active else "  "
        if is_active:
            preselect_idx = idx
        items.append(f"{status_prefix}{p['icon']}  {p['name']:<24} {p['desc']}")

    choice = run_rofi("󰍽 cursor theme :~$", items, preselect=preselect_idx)
    if not choice:
        return

    for p in PRESETS:
        if p["name"] in choice or p["id"] in choice:
            apply_cursor_theme(p["id"], p["name"])
            break


if __name__ == "__main__":
    main()
