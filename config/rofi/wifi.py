#!/usr/bin/env python3
import subprocess
import sys
import os

ROFI_THEME = os.path.expanduser("~/.config/rofi/wifi.rasi")

def notify(summary, body="", icon=None, urgency="normal"):
    cmd = ["dunstify", "-r", "5555", "-u", urgency, summary, body]
    subprocess.run(cmd, check=False)

def run_rofi(prompt, items, is_password=False):
    cmd = ["rofi", "-dmenu", "-i", "-p", prompt, "-theme", ROFI_THEME]
    if is_password:
        cmd.append("-password")
    input_str = "\n".join(items) if isinstance(items, list) else items
    res = subprocess.run(cmd, input=input_str, stdout=subprocess.PIPE, text=True, check=False)
    if res.returncode == 0:
        return res.stdout.strip()
    return None

def get_signal_icon(sig):
    if sig >= 75:
        return "󰤨"
    elif sig >= 50:
        return "󰤥"
    elif sig >= 25:
        return "󰤢"
    return "󰤟"

def main():
    # 1. Check wifi radio status
    try:
        radio = subprocess.check_output(["nmcli", "radio", "wifi"], text=True).strip()
    except Exception as e:
        notify("Wi-Fi Error", f"nmcli failed: {e}", urgency="critical")
        return

    if radio == "disabled":
        choice = run_rofi("󰤮 wifi :~$", ["󰤨  Turn Wi-Fi ON", "󰒍  Advanced Settings (nmtui)"])
        if choice and "Turn Wi-Fi ON" in choice:
            subprocess.run(["nmcli", "radio", "wifi", "on"], check=False)
            notify("Wi-Fi Enabled", "Wi-Fi radio is now active")
        elif choice and "Advanced Settings" in choice:
            subprocess.run(["alacritty", "--class", "FloatingWifi", "-e", "nmtui"])
        return

    # 2. Get wifi scan results
    try:
        out = subprocess.check_output(
            ["nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY", "device", "wifi", "list"],
            text=True
        )
    except Exception as e:
        out = ""

    seen = set()
    active_ssid = None
    networks = []

    for line in out.splitlines():
        parts = line.split(":")
        if len(parts) >= 4:
            in_use = (parts[0].strip() == "*")
            sec = parts[-1].strip()
            sig_str = parts[-2].strip()
            sig = int(sig_str) if sig_str.isdigit() else 0
            ssid = ":".join(parts[1:-2]).strip()
            if not ssid or ssid in seen:
                continue
            seen.add(ssid)
            if in_use:
                active_ssid = ssid
            networks.append({
                "ssid": ssid,
                "in_use": in_use,
                "signal": sig,
                "security": sec
            })

    # 3. Build Rofi menu options
    menu_items = []
    mapping = {}

    # Controls
    opt_toggle = "󰤮  Turn Wi-Fi OFF"
    opt_rescan = "󰑓  Rescan Networks"
    opt_nmtui = "󰒍  Advanced Settings (nmtui)"

    menu_items.append(opt_toggle)
    mapping[opt_toggle] = ("action", "toggle_off")

    menu_items.append(opt_nmtui)
    mapping[opt_nmtui] = ("action", "nmtui")

    menu_items.append(opt_rescan)
    mapping[opt_rescan] = ("action", "rescan")

    # Separator / spacer
    menu_items.append("──────────────────────────────────────────")
    mapping["──────────────────────────────────────────"] = ("noop", None)

    # Sort networks: active first, then by signal strength desc
    networks.sort(key=lambda n: (1 if n["in_use"] else 0, n["signal"]), reverse=True)

    for n in networks:
        icon = get_signal_icon(n["signal"])
        lock = "" if n["security"] and n["security"] != "--" else "  "
        if n["in_use"]:
            label = f"󰄬  {n['ssid']:<22}  [Connected · {icon} {n['signal']}%]"
        else:
            label = f"   {n['ssid']:<22}   {icon} {n['signal']:>2}%  {lock} {n['security']}"
        menu_items.append(label)
        mapping[label] = ("network", n)

    selected = run_rofi("󰤨 wifi :~$", menu_items)
    if not selected:
        return

    action_type, data = mapping.get(selected, (None, None))
    if action_type == "action":
        if data == "toggle_off":
            subprocess.run(["nmcli", "radio", "wifi", "off"], check=False)
            notify("Wi-Fi Disabled", "Wi-Fi radio is now turned off")
        elif data == "nmtui":
            subprocess.run(["alacritty", "--class", "FloatingWifi", "-e", "nmtui"])
        elif data == "rescan":
            subprocess.run(["nmcli", "device", "wifi", "rescan"], check=False)
            notify("Wi-Fi Rescan", "Scanning for available networks...")
            # Re-launch
            os.execv(sys.executable, [sys.executable, __file__])
    elif action_type == "network":
        net = data
        ssid = net["ssid"]
        if net["in_use"]:
            # Action on currently connected network
            act = run_rofi(
                f"󰄬 {ssid} :~$",
                [f"󰌺  Disconnect from {ssid}", f"󰚃  Forget {ssid} (Delete Profile)"]
            )
            if act and "Disconnect" in act:
                subprocess.run(["nmcli", "device", "disconnect", "wlo1"], check=False)
                notify("Wi-Fi", f"Disconnected from {ssid}")
            elif act and "Forget" in act:
                subprocess.run(["nmcli", "connection", "delete", ssid], check=False)
                notify("Wi-Fi", f"Deleted saved connection for {ssid}")
        else:
            # Check if connection profile already exists
            saved_conns = subprocess.check_output(
                ["nmcli", "-t", "-f", "NAME", "connection", "show"],
                text=True
            ).splitlines()

            if ssid in saved_conns:
                notify("Wi-Fi", f"Connecting to saved network {ssid}...")
                res = subprocess.run(["nmcli", "connection", "up", ssid], capture_output=True, text=True)
                if res.returncode == 0:
                    notify("Wi-Fi Connected", f"Successfully connected to {ssid}")
                else:
                    notify("Wi-Fi Error", f"Failed to connect to {ssid}\n{res.stderr.strip()}", urgency="critical")
            else:
                # New connection
                if net["security"] and net["security"] != "--":
                    pwd = run_rofi(f"󰌾 {ssid} password :~$", [], is_password=True)
                    if not pwd:
                        return
                    notify("Wi-Fi", f"Connecting to {ssid}...")
                    res = subprocess.run(
                        ["nmcli", "device", "wifi", "connect", ssid, "password", pwd],
                        capture_output=True,
                        text=True
                    )
                    if res.returncode == 0:
                        notify("Wi-Fi Connected", f"Successfully connected to {ssid}")
                    else:
                        notify("Wi-Fi Error", f"Failed to connect to {ssid}\n{res.stderr.strip()}", urgency="critical")
                else:
                    notify("Wi-Fi", f"Connecting to open network {ssid}...")
                    res = subprocess.run(
                        ["nmcli", "device", "wifi", "connect", ssid],
                        capture_output=True,
                        text=True
                    )
                    if res.returncode == 0:
                        notify("Wi-Fi Connected", f"Successfully connected to {ssid}")
                    else:
                        notify("Wi-Fi Error", f"Failed to connect to {ssid}\n{res.stderr.strip()}", urgency="critical")

if __name__ == "__main__":
    main()
