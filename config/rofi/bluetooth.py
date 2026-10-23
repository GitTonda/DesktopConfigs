#!/usr/bin/env python3
"""
Rofi Bluetooth Manager & Widget Customizer
Catppuccin Mocha minimal terminal-style Bluetooth controller.
"""

import subprocess
import sys
import os
import time
import re

ROFI_THEME = os.path.expanduser("~/.config/rofi/bluetooth.rasi")
CONF_FILE = os.path.expanduser("~/.config/polybar/bluetooth.conf")


def notify(summary, body="", urgency="normal"):
    cmd = [
        "dunstify",
        "-r", "5566",
        "-u", urgency,
        "-h", "string:x-dunst-stack-tag:bluetooth",
        summary,
        body
    ]
    subprocess.run(cmd, check=False)


def run_rofi(prompt, items):
    cmd = ["rofi", "-dmenu", "-i", "-p", prompt, "-theme", ROFI_THEME]
    input_str = "\n".join(items) if isinstance(items, list) else items
    res = subprocess.run(cmd, input=input_str, stdout=subprocess.PIPE, text=True, check=False)
    if res.returncode == 0:
        return res.stdout.strip()
    return None


def is_powered_on():
    try:
        out = subprocess.check_output(["bluetoothctl", "show"], text=True, stderr=subprocess.DEVNULL)
        return "Powered: yes" in out
    except Exception:
        return False


def set_power(on=True):
    if on:
        subprocess.run(["rfkill", "unblock", "bluetooth"], check=False, stderr=subprocess.DEVNULL)
        time.sleep(0.15)
        subprocess.run(["bluetoothctl", "power", "on"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        notify("󰂯 Bluetooth Enabled", "Controller powered on")
    else:
        subprocess.run(["bluetoothctl", "power", "off"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["rfkill", "block", "bluetooth"], check=False, stderr=subprocess.DEVNULL)
        notify("󰂲 Bluetooth Disabled", "Controller powered off")


def load_config():
    defaults = {
        "SHOW_NAME": "true",
        "SHOW_BATTERY": "true",
        "DEVICE_ICONS": "true",
        "HIDE_WHEN_OFF": "false",
        "MAX_NAME_LEN": "14",
    }
    if not os.path.exists(CONF_FILE):
        return defaults

    with open(CONF_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                defaults[k.strip()] = v.strip().strip('"\'')
    return defaults


def save_config(cfg):
    with open(CONF_FILE, "w") as f:
        f.write("# Polybar Bluetooth Widget Configuration\n")
        f.write("# Editable manually or via Rofi Bluetooth Customizer\n\n")
        for k, v in cfg.items():
            f.write(f"{k}={v}\n")


def customize_menu():
    """
    Widget Customizer Menu.
    Returns:
        'back'  - User explicitly clicked 'Back to Bluetooth Menu'
        'close' - User pressed Escape to close Rofi
    """
    while True:
        cfg = load_config()
        show_name = cfg.get("SHOW_NAME", "true") == "true"
        show_bat = cfg.get("SHOW_BATTERY", "true") == "true"
        dev_icons = cfg.get("DEVICE_ICONS", "true") == "true"
        hide_off = cfg.get("HIDE_WHEN_OFF", "false") == "true"

        items = [
            f"[{'ON' if show_name else 'OFF'}]  Show Device Name",
            f"[{'ON' if dev_icons else 'OFF'}]  Device-Specific Icons (󰋋 󰌌 󰍽)",
            f"[{'ON' if show_bat else 'OFF'}]  Show Battery Percentage",
            f"[{'ON' if hide_off else 'OFF'}]  Hide Widget When Powered Off",
            "󰁞  Back to Bluetooth Menu",
        ]

        choice = run_rofi("󰒓 widget :~$", items)
        if choice is None:
            # User pressed Escape -> dismiss completely
            return "close"

        if "Back to Bluetooth" in choice:
            # User explicitly requested to navigate to the Bluetooth menu
            return "back"

        if "Show Device Name" in choice:
            cfg["SHOW_NAME"] = "false" if show_name else "true"
        elif "Device-Specific Icons" in choice:
            cfg["DEVICE_ICONS"] = "false" if dev_icons else "true"
        elif "Show Battery" in choice:
            cfg["SHOW_BATTERY"] = "false" if show_bat else "true"
        elif "Hide Widget" in choice:
            cfg["HIDE_WHEN_OFF"] = "false" if hide_off else "true"

        save_config(cfg)
        notify("󰒓 Widget Config Saved", "Polybar Bluetooth display updated")


def get_device_details(mac):
    try:
        out = subprocess.check_output(["bluetoothctl", "info", mac], text=True, stderr=subprocess.DEVNULL)
        info = {"name": mac, "icon_type": "generic", "connected": False, "battery": None}
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("Name:"):
                info["name"] = line.split(":", 1)[1].strip()
            elif line.startswith("Icon:"):
                t = line.split(":", 1)[1].strip().lower()
                if any(x in t for x in ["headset", "audio", "headphones"]):
                    info["icon_type"] = "audio"
                elif "keyboard" in t:
                    info["icon_type"] = "keyboard"
                elif "mouse" in t:
                    info["icon_type"] = "mouse"
                elif "gamepad" in t or "gaming" in t:
                    info["icon_type"] = "gamepad"
                elif "phone" in t:
                    info["icon_type"] = "phone"
            elif line.startswith("Connected:"):
                info["connected"] = "yes" in line.lower()
            elif "Battery Percentage:" in line:
                m = re.search(r"\((\d+)%\)", line)
                if m:
                    info["battery"] = m.group(1)
        return info
    except Exception:
        return {"name": mac, "icon_type": "generic", "connected": False, "battery": None}


def get_icon(icon_type, connected=False):
    if icon_type == "audio":
        return "󰋋"
    elif icon_type == "keyboard":
        return "󰌌"
    elif icon_type == "mouse":
        return "󰍽"
    elif icon_type == "gamepad":
        return "󰊴"
    elif icon_type == "phone":
        return "󰏲"
    return "󰂱" if connected else "󰂯"


def scan_devices():
    notify("󰑐 Bluetooth Scanning", "Scanning for nearby discoverable devices (5s)...")
    try:
        proc = subprocess.Popen(["bluetoothctl", "scan", "on"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(4.5)
        subprocess.run(["bluetoothctl", "scan", "off"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        proc.kill()
    except Exception:
        pass

    try:
        out = subprocess.check_output(["bluetoothctl", "devices"], text=True)
        paired_out = subprocess.check_output(["bluetoothctl", "devices", "Paired"], text=True)
        paired_macs = set()
        for line in paired_out.splitlines():
            parts = line.strip().split()
            if len(parts) >= 2:
                paired_macs.add(parts[1])

        unpaired = []
        for line in out.splitlines():
            parts = line.strip().split(maxsplit=2)
            if len(parts) >= 3 and parts[0] == "Device":
                mac = parts[1]
                name = parts[2]
                if mac not in paired_macs:
                    unpaired.append((mac, name))

        if not unpaired:
            notify("Scan Complete", "No new unpaired devices discovered.")
            return "back"

        items = [f"󰂱  Pair & Connect: {name} [{mac}]" for mac, name in unpaired]
        items.append("󰁞  Back to Bluetooth Menu")
        choice = run_rofi("󰑐 pair :~$", items)
        if choice is None:
            return "close"
        if "Back to Bluetooth" in choice:
            return "back"

        if "Pair & Connect:" in choice:
            m = re.search(r"\[([0-9A-Fa-f:]+)\]", choice)
            if m:
                target_mac = m.group(1)
                notify("Pairing...", f"Connecting to {target_mac}")
                subprocess.run(["bluetoothctl", "pair", target_mac], check=False)
                subprocess.run(["bluetoothctl", "trust", target_mac], check=False)
                res = subprocess.run(["bluetoothctl", "connect", target_mac], check=False, stdout=subprocess.PIPE, text=True)
                if "Connection successful" in res.stdout or res.returncode == 0:
                    notify("󰂱 Connected", f"Successfully paired with {target_mac}")
                else:
                    notify("Pairing Result", res.stdout.strip()[:100] or "Check device is in pairing mode")
        return "back"
    except Exception as e:
        notify("Scan Error", str(e), urgency="critical")
        return "back"


def device_menu(mac, name, is_conn):
    info = get_device_details(mac)
    bat_str = f" | Battery: {info['battery']}%" if info['battery'] else ""

    items = []
    if is_conn:
        items.append(f"󰂲  Disconnect from {name}")
    else:
        items.append(f"󰂱  Connect to {name}")
    items.append(f"󰅖  Unpair / Forget {name}")
    items.append(f"󰋼  Device Info (MAC: {mac}{bat_str})")
    items.append("󰁞  Back to Bluetooth Menu")

    choice = run_rofi(f"󰂯 {name[:18]} :~$", items)
    if choice is None:
        return "close"
    if "Back to Bluetooth" in choice:
        return "back"

    if "Connect to" in choice:
        notify("Connecting...", f"Connecting to {name}")
        res = subprocess.run(["bluetoothctl", "connect", mac], check=False, stdout=subprocess.PIPE, text=True)
        if "Connection successful" in res.stdout or res.returncode == 0:
            notify("󰂱 Connected", f"Connected to {name}")
        else:
            notify("Connection Failed", res.stdout.strip()[:80] or "Check device is turned on")
    elif "Disconnect" in choice:
        subprocess.run(["bluetoothctl", "disconnect", mac], check=False)
        notify("󰂲 Disconnected", f"Disconnected from {name}")
    elif "Unpair" in choice:
        subprocess.run(["bluetoothctl", "remove", mac], check=False)
        notify("󰅖 Unpaired", f"Forgot {name} [{mac}]")
    elif "Device Info" in choice:
        raw_info = subprocess.check_output(["bluetoothctl", "info", mac], text=True, stderr=subprocess.DEVNULL)
        notify(f"Info: {name}", raw_info[:200])

    return "back"


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--customize":
        action = customize_menu()
        if action != "back":
            return
        # If user explicitly clicked 'Back to Bluetooth Menu', transition smoothly into the main menu!

    while True:
        powered = is_powered_on()
        items = []

        if not powered:
            items.append("󰂯  Turn Bluetooth ON")
            items.append("󰒓  Configure Top Bar Widget")
            items.append("  Interactive CLI (bluetoothctl)")
            choice = run_rofi("󰂲 bluetooth [off] :~$", items)
            if choice is None:
                break
            if "Turn Bluetooth ON" in choice:
                set_power(True)
                continue
            elif "Configure" in choice or "Widget" in choice or "Customize" in choice:
                action = customize_menu()
                if action == "close":
                    break
                continue
            elif "Interactive CLI" in choice:
                subprocess.Popen(["alacritty", "--class", "FloatingBluetooth", "-e", "bluetoothctl"])
                break
            break

        # Powered ON: get paired & connected devices
        try:
            paired_raw = subprocess.check_output(["bluetoothctl", "devices", "Paired"], text=True, stderr=subprocess.DEVNULL)
        except Exception:
            paired_raw = ""
        try:
            connected_raw = subprocess.check_output(["bluetoothctl", "devices", "Connected"], text=True, stderr=subprocess.DEVNULL)
        except Exception:
            connected_raw = ""

        connected_macs = set()
        for line in connected_raw.splitlines():
            p = line.strip().split()
            if len(p) >= 2:
                connected_macs.add(p[1])

        device_entries = []
        for line in paired_raw.splitlines():
            p = line.strip().split(maxsplit=2)
            if len(p) >= 3 and p[0] == "Device":
                mac = p[1]
                name = p[2]
                is_conn = mac in connected_macs
                details = get_device_details(mac)
                icon = get_icon(details["icon_type"], is_conn)
                bat = f" ({details['battery']}%)" if details.get("battery") else ""
                tag = "[Connected]" if is_conn else "[Paired]"
                device_entries.append((mac, name, is_conn, f"{icon}  {name} {bat} {tag}"))

        # Sort: connected first, then alphabetical
        device_entries.sort(key=lambda x: (not x[2], x[1].lower()))

        for entry in device_entries:
            items.append(entry[3])

        items.append("󰂲  Turn Bluetooth OFF")
        items.append("󰑐  Scan for Nearby Devices")
        items.append("󰒓  Configure Top Bar Widget")
        items.append("  Interactive CLI (bluetoothctl)")

        status_tag = f"[{len(connected_macs)} connected]" if connected_macs else "[on]"
        choice = run_rofi(f"󰂯 bluetooth {status_tag} :~$", items)
        if choice is None:
            break

        if "Turn Bluetooth OFF" in choice:
            set_power(False)
            break
        elif "Scan for Nearby" in choice:
            action = scan_devices()
            if action == "close":
                break
            continue
        elif "Configure" in choice or "Widget" in choice or "Customize" in choice:
            action = customize_menu()
            if action == "close":
                break
            continue
        elif "Interactive CLI" in choice:
            subprocess.Popen(["alacritty", "--class", "FloatingBluetooth", "-e", "bluetoothctl"])
            break
        else:
            # A device was selected
            matched = False
            for mac, name, is_conn, menu_str in device_entries:
                if choice == menu_str:
                    matched = True
                    action = device_menu(mac, name, is_conn)
                    if action == "close":
                        return
                    break
            if not matched:
                break


if __name__ == "__main__":
    main()
