#!/usr/bin/env python3
"""
Catppuccin Mocha Desktop Settings
A modern, native Android-like settings application for i3 and Pop!_OS.
Supports deep-linking via CLI: desktop-settings --page <page_name>
"""

import os
import sys
import subprocess
import shutil
import time
import re
import argparse
import colorsys

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango


# ------------------------------------------------------------------------------
# Helpers & System Integrations
# ------------------------------------------------------------------------------

def get_accent_color():
    colors_file = os.path.expanduser("~/.config/polybar/colors.ini")
    if os.path.exists(colors_file):
        try:
            with open(colors_file, "r") as f:
                for line in f:
                    if line.strip().startswith("accent"):
                        parts = line.split("=")
                        if len(parts) == 2:
                            col = parts[1].strip()
                            if col:
                                return col
        except Exception:
            pass
    return "#89b4fa"


def apply_accent_color(accent_hex):
    """Applies a Catppuccin accent color system-wide."""
    try:
        # 1. Polybar
        pb_file = os.path.expanduser("~/.config/polybar/colors.ini")
        os.makedirs(os.path.dirname(pb_file), exist_ok=True)
        with open(pb_file, "w") as f:
            f.write(f"[colors]\naccent = {accent_hex}\n")

        # 2. Theme accent file
        theme_dir = os.path.expanduser("~/.config/theme")
        os.makedirs(theme_dir, exist_ok=True)
        with open(os.path.join(theme_dir, "accent.color"), "w") as f:
            f.write(f"{accent_hex}\n")

        # 3. i3 Window borders
        i3_colors = os.path.expanduser("~/.config/i3/colors.conf")
        if os.path.exists(i3_colors):
            with open(i3_colors, "r") as f:
                content = f.read()
            content = re.sub(r'set \$accent #[0-9a-fA-F]{6}', f'set $accent {accent_hex}', content)
            with open(i3_colors, "w") as f:
                f.write(content)
            subprocess.run(["i3-msg", "reload"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 4. Rofi colors
        rofi_colors = os.path.expanduser("~/.config/rofi/colors.rasi")
        if os.path.exists(rofi_colors):
            with open(rofi_colors, "r") as f:
                content = f.read()
            content = re.sub(r'accent:\s*#[0-9a-fA-F]{6};', f'accent:     {accent_hex};', content)
            with open(rofi_colors, "w") as f:
                f.write(content)

        # 5. Reload polybar
        poly_launch = os.path.expanduser("~/.config/polybar/launch.sh")
        if os.path.exists(poly_launch):
            subprocess.Popen([poly_launch], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # 6. Notify
        subprocess.run([
            "dunstify", "-r", "4445", "-u", "normal",
            "󰏘 Accent Updated",
            f"New accent color: <span foreground='{accent_hex}'><b>{accent_hex}</b></span>"
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:
        print(f"Error applying accent: {e}")


def get_system_opacity():
    """Gets synchronized system opacity (float between 0.3 and 1.0)."""
    opacity_file = os.path.expanduser("~/.config/theme/opacity")
    if os.path.exists(opacity_file):
        try:
            with open(opacity_file, "r") as f:
                val = float(f.read().strip())
                return max(0.3, min(1.0, val))
        except Exception:
            pass
    alacritty_file = os.path.expanduser("~/.config/alacritty/alacritty.toml")
    if os.path.exists(alacritty_file):
        try:
            with open(alacritty_file, "r") as f:
                for line in f:
                    if "opacity" in line and "=" in line:
                        return float(line.split("=")[1].strip())
        except Exception:
            pass
    return 0.70


def set_system_opacity(pct):
    """Sets synchronized opacity across Alacritty, Control Center, and Desktop Settings."""
    val = round(max(0.3, min(1.0, pct / 100.0)), 2)
    theme_dir = os.path.expanduser("~/.config/theme")
    os.makedirs(theme_dir, exist_ok=True)
    with open(os.path.join(theme_dir, "opacity"), "w") as f:
        f.write(f"{val}\n")

    alacritty_file = os.path.expanduser("~/.config/alacritty/alacritty.toml")
    if os.path.exists(alacritty_file):
        try:
            with open(alacritty_file, "r") as f:
                content = f.read()
            content = re.sub(r'opacity\s*=\s*[0-9.]+', f'opacity = {val}', content)
            with open(alacritty_file, "w") as f:
                f.write(content)
        except Exception:
            pass


def get_wifi_state():
    enabled = False
    ssid = "Disconnected"
    try:
        radio = subprocess.check_output(["nmcli", "-t", "-f", "WIFI", "g"], text=True, stderr=subprocess.DEVNULL).strip()
        enabled = (radio == "enabled")
        if enabled:
            out = subprocess.check_output(["nmcli", "-t", "-f", "ACTIVE,SSID", "dev", "wifi"], text=True, stderr=subprocess.DEVNULL)
            for line in out.splitlines():
                if line.startswith("yes:"):
                    cur = line.split(":", 1)[1].strip()
                    if cur:
                        ssid = cur
                        break
    except Exception:
        pass
    return {"enabled": enabled, "ssid": ssid}


def get_network_details():
    ip_addr = "N/A"
    gateway = "N/A"
    dns = "N/A"
    iface = "N/A"
    try:
        out = subprocess.check_output(["ip", "route", "get", "1.1.1.1"], text=True, stderr=subprocess.DEVNULL)
        m = re.search(r"via\s+(\S+)\s+dev\s+(\S+)\s+src\s+(\S+)", out)
        if m:
            gateway = m.group(1)
            iface = m.group(2)
            ip_addr = m.group(3)
        with open("/etc/resolv.conf", "r") as f:
            for line in f:
                if line.startswith("nameserver"):
                    dns = line.split()[1]
                    break
    except Exception:
        pass
    return {"ip": ip_addr, "gateway": gateway, "dns": dns, "iface": iface}


def get_wifi_networks():
    nets = []
    try:
        out = subprocess.check_output(["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY,IN-USE", "dev", "wifi", "list"], text=True, stderr=subprocess.DEVNULL)
        seen = set()
        for line in out.splitlines():
            parts = line.split(":")
            if len(parts) >= 4:
                ssid = parts[0].strip()
                if not ssid or ssid in seen:
                    continue
                seen.add(ssid)
                sig = int(parts[1]) if parts[1].isdigit() else 50
                sec = parts[2].strip() or "Open"
                in_use = (parts[3].strip() == "*")
                nets.append({"ssid": ssid, "signal": sig, "security": sec, "active": in_use})
    except Exception:
        pass
    nets.sort(key=lambda x: (not x["active"], -x["signal"]))
    return nets


def get_bluetooth_state():
    powered = False
    try:
        out = subprocess.check_output(["bluetoothctl", "show"], text=True, stderr=subprocess.DEVNULL)
        powered = "Powered: yes" in out
    except Exception:
        pass
    return powered


def get_bluetooth_devices():
    devs = []
    try:
        out = subprocess.check_output(["bluetoothctl", "devices"], text=True, stderr=subprocess.DEVNULL)
        for line in out.splitlines():
            parts = line.split(" ", 2)
            if len(parts) >= 3 and parts[0] == "Device":
                mac = parts[1]
                name = parts[2]
                info = subprocess.check_output(["bluetoothctl", "info", mac], text=True, stderr=subprocess.DEVNULL)
                connected = "Connected: yes" in info
                paired = "Paired: yes" in info
                icon = "󰂯"
                if "audio-card" in info or "audio-headset" in info or "audio-headphones" in info:
                    icon = "󰋋"
                elif "keyboard" in info:
                    icon = "󰌌"
                elif "mouse" in info:
                    icon = "󰍽"
                elif "phone" in info:
                    icon = "󰏲"
                devs.append({"mac": mac, "name": name, "connected": connected, "paired": paired, "icon": icon})
    except Exception:
        pass
    devs.sort(key=lambda x: not x["connected"])
    return devs


def get_audio_sinks():
    sinks = []
    try:
        out = subprocess.check_output(["pactl", "list", "sinks"], text=True, stderr=subprocess.DEVNULL)
        curr = {}
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("Sink #"):
                if curr:
                    sinks.append(curr)
                curr = {"id": line.split("#")[1]}
            elif line.startswith("Name:"):
                curr["name"] = line.split(":", 1)[1].strip()
            elif line.startswith("Description:"):
                curr["desc"] = line.split(":", 1)[1].strip()
            elif line.startswith("Mute:"):
                curr["muted"] = "yes" in line.lower()
        if curr:
            sinks.append(curr)
    except Exception:
        pass
    return sinks


def get_default_sink():
    try:
        return subprocess.check_output(["pactl", "get-default-sink"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def get_audio_sources():
    sources = []
    try:
        out = subprocess.check_output(["pactl", "list", "sources"], text=True, stderr=subprocess.DEVNULL)
        curr = {}
        for line in out.splitlines():
            line = line.strip()
            if line.startswith("Source #"):
                if curr and not curr.get("is_monitor", False):
                    sources.append(curr)
                curr = {"id": line.split("#")[1], "is_monitor": False}
            elif line.startswith("Name:"):
                curr["name"] = line.split(":", 1)[1].strip()
                if ".monitor" in curr["name"]:
                    curr["is_monitor"] = True
            elif line.startswith("Description:"):
                curr["desc"] = line.split(":", 1)[1].strip()
            elif line.startswith("Mute:"):
                curr["muted"] = "yes" in line.lower()
        if curr and not curr.get("is_monitor", False):
            sources.append(curr)
    except Exception:
        pass
    return sources


def get_default_source():
    try:
        return subprocess.check_output(["pactl", "get-default-source"], text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        return ""


def get_displays_info():
    displays = []
    try:
        out = subprocess.check_output(["xrandr", "--query"], text=True, stderr=subprocess.DEVNULL)
        cur_disp = None
        for line in out.splitlines():
            m = re.match(r"^(\S+)\s+(connected|disconnected)\s*(primary)?\s*([0-9]+x[0-9]+\+[0-9]+\+[0-9]+)?", line)
            if m:
                name, status, is_pri, geom = m.groups()
                if status == "connected":
                    cur_disp = {"name": name, "primary": bool(is_pri), "geom": geom or "N/A", "modes": []}
                    displays.append(cur_disp)
                else:
                    cur_disp = None
            elif cur_disp and re.match(r"^\s+([0-9]+x[0-9]+)", line):
                parts = line.strip().split()
                res = parts[0]
                rates = [r.replace("*", "").replace("+", "") for r in parts[1:]]
                cur_disp["modes"].append({"res": res, "rates": rates})
    except Exception:
        pass
    return displays


def get_brightness():
    cache_file = os.path.expanduser("~/.config/theme/brightness")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                val = int(f.read().strip())
                return max(10, min(100, val))
        except Exception:
            pass
    try:
        out = subprocess.check_output(["brightnessctl", "-m"], text=True, stderr=subprocess.DEVNULL)
        for line in out.splitlines():
            parts = line.split(",")
            if len(parts) >= 5 and parts[1] == "backlight":
                b = int(parts[3].replace("%", ""))
                try:
                    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                    with open(cache_file, "w") as f:
                        f.write(str(b))
                except Exception:
                    pass
                return b
    except Exception:
        pass
    try:
        out = subprocess.check_output(["xrandr", "--verbose"], text=True, stderr=subprocess.DEVNULL)
        m = re.search(r"Brightness:\s*([0-9.]+)", out)
        if m:
            val = float(m.group(1))
            b = int(round(val * 100))
            try:
                os.makedirs(os.path.dirname(cache_file), exist_ok=True)
                with open(cache_file, "w") as f:
                    f.write(str(b))
            except Exception:
                pass
            return b
    except Exception:
        pass
    return 100


def set_brightness(pct):
    pct = max(10, min(100, pct))
    cache_file = os.path.expanduser("~/.config/theme/brightness")
    try:
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        with open(cache_file, "w") as f:
            f.write(str(pct))
    except Exception:
        pass
    try:
        out = subprocess.check_output(["brightnessctl", "-m"], text=True, stderr=subprocess.DEVNULL)
        for line in out.splitlines():
            parts = line.split(",")
            if len(parts) >= 5 and parts[1] == "backlight":
                subprocess.run(["brightnessctl", "set", f"{pct}%"], check=False)
                return
    except Exception:
        pass
    try:
        out = subprocess.check_output(["xrandr", "--query"], text=True, stderr=subprocess.DEVNULL)
        outputs = [line.split()[0] for line in out.splitlines() if " connected" in line]
        ratio = round(pct / 100.0, 2)
        for mon in outputs:
            subprocess.run(["xrandr", "--output", mon, "--brightness", str(ratio)], check=False)
    except Exception:
        pass


def get_wallpapers():
    wp_dir = os.path.expanduser("~/Pictures/Wallpapers")
    wps = []
    if os.path.exists(wp_dir):
        for f in sorted(os.listdir(wp_dir)):
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                wps.append(os.path.join(wp_dir, f))
    return wps


def get_i3_shortcuts():
    conf = os.path.expanduser("~/.config/i3/config")
    shortcuts = []
    if os.path.exists(conf):
        try:
            with open(conf, "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("bindsym "):
                        parts = line.split(None, 2)
                        if len(parts) >= 3:
                            key = parts[1].replace("$mod", "Super").replace("mod4", "Super")
                            cmd = parts[2].replace("exec --no-startup-id ", "").replace("exec ", "")
                            desc = cmd
                            if "alacritty" in cmd:
                                desc = "Alacritty Terminal"
                            elif "zen-browser" in cmd:
                                desc = "Zen Web Browser"
                            elif "thunar" in cmd:
                                desc = "Thunar File Manager"
                            elif "rofi" in cmd:
                                desc = "Rofi App Launcher"
                            elif "toggle.sh" in cmd:
                                desc = "Control Center (Quick Settings)"
                            elif "desktop_settings.py" in cmd:
                                desc = "Desktop Settings"
                            elif "lock.sh" in cmd:
                                desc = "Lock Screen"
                            elif "kill" in cmd:
                                desc = "Close Active Window"
                            elif "split" in cmd:
                                desc = "Split Window Layout"
                            elif "fullscreen" in cmd:
                                desc = "Toggle Fullscreen"
                            elif "floating" in cmd:
                                desc = "Toggle Floating Window"
                            elif "focus" in cmd:
                                desc = f"Move Focus ({key})"
                            elif "move" in cmd:
                                desc = f"Move Window ({key})"
                            elif "workspace" in cmd:
                                desc = f"Switch to Workspace ({key})"
                            shortcuts.append((key, desc, cmd))
        except Exception:
            pass
    return shortcuts


def get_system_specs():
    specs = {}
    try:
        specs["user"] = os.environ.get("USER", "user")
        with open("/etc/hostname") as f:
            specs["hostname"] = f.read().strip()
    except Exception:
        specs["user"] = "tonda"
        specs["hostname"] = "pop-sos"

    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    specs["os"] = line.split("=")[1].strip().strip('"')
                    break
    except Exception:
        specs["os"] = "Linux"

    try:
        specs["kernel"] = subprocess.check_output(["uname", "-r"], text=True).strip()
    except Exception:
        specs["kernel"] = "Unknown"

    try:
        with open("/proc/cpuinfo") as f:
            for line in f:
                if "model name" in line:
                    specs["cpu"] = line.split(":", 1)[1].strip()
                    break
    except Exception:
        specs["cpu"] = "Processor"

    try:
        out = subprocess.check_output(["lspci"], text=True)
        for line in out.splitlines():
            if "VGA compatible" in line or "3D controller" in line:
                specs["gpu"] = line.split(":", 2)[2].strip()
                break
    except Exception:
        specs["gpu"] = "GPU"

    try:
        with open("/proc/meminfo") as f:
            total = 0
            for line in f:
                if "MemTotal" in line:
                    total = int(line.split()[1]) / (1024 * 1024)
                    break
        specs["ram_total"] = f"{total:.1f} GB"
    except Exception:
        specs["ram_total"] = "16.0 GB"

    try:
        out = subprocess.check_output(["df", "-h", "/"], text=True).splitlines()[1].split()
        specs["disk_used"] = f"{out[2]} / {out[1]} ({out[4]})"
    except Exception:
        specs["disk_used"] = "N/A"

    return specs


# ------------------------------------------------------------------------------
# UI Components: Settings Card Group
# ------------------------------------------------------------------------------

class SettingsCard(Gtk.Box):
    def __init__(self, title=None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.get_style_context().add_class("settings-card")

        if title:
            lbl = Gtk.Label(label=title, xalign=0)
            lbl.get_style_context().add_class("settings-card-title")
            self.pack_start(lbl, False, False, 8)

        self.rows_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.pack_start(self.rows_box, True, True, 0)
        self._count = 0

    def add_row(self, icon, title, subtitle=None, widget=None):
        if self._count > 0:
            sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
            sep.get_style_context().add_class("settings-separator")
            self.rows_box.pack_start(sep, False, False, 0)

        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        row.get_style_context().add_class("settings-row")

        if icon:
            icon_lbl = Gtk.Label(label=icon)
            icon_lbl.get_style_context().add_class("settings-row-icon")
            row.pack_start(icon_lbl, False, False, 0)

        txt_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title_lbl = Gtk.Label(label=title, xalign=0)
        title_lbl.get_style_context().add_class("settings-row-title")
        txt_box.pack_start(title_lbl, False, False, 0)

        if subtitle:
            sub_lbl = Gtk.Label(label=subtitle, xalign=0)
            sub_lbl.get_style_context().add_class("settings-row-sub")
            txt_box.pack_start(sub_lbl, False, False, 0)

        row.pack_start(txt_box, True, True, 0)

        if widget:
            row.pack_end(widget, False, False, 0)

        self.rows_box.pack_start(row, False, False, 0)
        self._count += 1
        return row


# ------------------------------------------------------------------------------
# Pages Implementations
# ------------------------------------------------------------------------------

class NetworkPage(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        content.set_margin_start(16)
        content.set_margin_end(16)
        content.set_margin_top(16)
        content.set_margin_bottom(16)
        self.add(content)

        # Header
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        lbl = Gtk.Label(label="󰤨 Network & Wi-Fi", xalign=0)
        lbl.get_style_context().add_class("page-title")
        hdr.pack_start(lbl, True, True, 0)
        content.pack_start(hdr, False, False, 0)

        # 1. Wi-Fi Switch Card
        wifi_st = get_wifi_state()
        card_wifi = SettingsCard()
        self.wifi_sw = Gtk.Switch()
        self.wifi_sw.set_active(wifi_st["enabled"])
        self.wifi_sw.connect("state-set", self._on_wifi_switch)
        card_wifi.add_row(
            icon="󰤨",
            title="Wi-Fi",
            subtitle="Connect to available wireless networks",
            widget=self.wifi_sw
        )
        content.pack_start(card_wifi, False, False, 0)

        # 2. Connection Details Card
        net_det = get_network_details()
        card_det = SettingsCard(title="ACTIVE CONNECTION")
        card_det.add_row("󰩠", "Local IP Address", net_det["ip"])
        card_det.add_row("󰒍", "Gateway / Router", net_det["gateway"])
        card_det.add_row("󰇚", "DNS Server", net_det["dns"])
        card_det.add_row("󰈀", "Network Interface", net_det["iface"])
        content.pack_start(card_det, False, False, 0)

        # 3. Available Networks Card
        card_nets = SettingsCard(title="AVAILABLE WI-FI NETWORKS")
        scan_btn = Gtk.Button(label="󰑓 Scan")
        scan_btn.get_style_context().add_class("action-btn")
        scan_btn.connect("clicked", self._on_rescan_wifi)

        scan_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        scan_lbl = Gtk.Label(label="Search for nearby wireless networks", xalign=0)
        scan_lbl.get_style_context().add_class("settings-row-sub")
        scan_row.pack_start(scan_lbl, True, True, 0)
        scan_row.pack_end(scan_btn, False, False, 0)
        card_nets.pack_start(scan_row, False, False, 8)

        self.nets_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        card_nets.pack_start(self.nets_box, True, True, 0)
        content.pack_start(card_nets, False, False, 0)

        self._populate_wifi_nets()

    def _on_wifi_switch(self, sw, state):
        cmd = ["nmcli", "radio", "wifi", "on" if state else "off"]
        subprocess.run(cmd, check=False)
        GLib.timeout_add(800, self._populate_wifi_nets)
        return False

    def _on_rescan_wifi(self, btn):
        subprocess.run(["nmcli", "dev", "wifi", "rescan"], check=False)
        GLib.timeout_add(1000, self._populate_wifi_nets)

    def _populate_wifi_nets(self):
        for c in self.nets_box.get_children():
            self.nets_box.remove(c)

        nets = get_wifi_networks()
        if not nets:
            no_lbl = Gtk.Label(label="No Wi-Fi networks found or Wi-Fi is disabled.", xalign=0)
            no_lbl.get_style_context().add_class("settings-row-sub")
            self.nets_box.pack_start(no_lbl, False, False, 8)
            self.nets_box.show_all()
            return

        for net in nets:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            row.get_style_context().add_class("settings-row")

            icon_name = "󰤨" if net["signal"] > 70 else ("󰤥" if net["signal"] > 40 else "󰤢")
            icon_lbl = Gtk.Label(label=icon_name)
            icon_lbl.get_style_context().add_class("settings-row-icon")
            row.pack_start(icon_lbl, False, False, 0)

            txt = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            name_lbl = Gtk.Label(label=net["ssid"], xalign=0)
            name_lbl.get_style_context().add_class("settings-row-title")
            sub_lbl = Gtk.Label(label=f"Signal: {net['signal']}% • {net['security']}", xalign=0)
            sub_lbl.get_style_context().add_class("settings-row-sub")
            txt.pack_start(name_lbl, False, False, 0)
            txt.pack_start(sub_lbl, False, False, 0)
            row.pack_start(txt, True, True, 0)

            if net["active"]:
                badge = Gtk.Label(label="󰄬 Connected")
                badge.get_style_context().add_class("connected-badge")
                row.pack_end(badge, False, False, 0)
            else:
                con_btn = Gtk.Button(label="Connect")
                con_btn.get_style_context().add_class("action-btn")
                con_btn.connect("clicked", lambda b, s=net["ssid"]: self._connect_dialog(s))
                row.pack_end(con_btn, False, False, 0)

            self.nets_box.pack_start(row, False, False, 0)

        self.nets_box.show_all()

    def _connect_dialog(self, ssid):
        dialog = Gtk.Dialog(
            title=f"Connect to {ssid}",
            parent=self.get_toplevel(),
            flags=Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT
        )
        dialog.add_buttons("Cancel", Gtk.ResponseType.CANCEL, "Connect", Gtk.ResponseType.OK)
        box = dialog.get_content_area()
        box.set_spacing(10)
        box.set_margin_start(16)
        box.set_margin_end(16)
        box.set_margin_top(16)
        box.set_margin_bottom(16)

        lbl = Gtk.Label(label=f"Enter password for network '{ssid}':", xalign=0)
        entry = Gtk.Entry()
        entry.set_visibility(False)
        box.pack_start(lbl, False, False, 0)
        box.pack_start(entry, False, False, 0)
        dialog.show_all()

        resp = dialog.run()
        pwd = entry.get_text()
        dialog.destroy()

        if resp == Gtk.ResponseType.OK:
            cmd = ["nmcli", "dev", "wifi", "connect", ssid]
            if pwd:
                cmd.extend(["password", pwd])
            subprocess.run(cmd, check=False)
            GLib.timeout_add(1500, self._populate_wifi_nets)


class BluetoothPage(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        content.set_margin_start(16)
        content.set_margin_end(16)
        content.set_margin_top(16)
        content.set_margin_bottom(16)
        self.add(content)

        # Header
        lbl = Gtk.Label(label="󰂯 Bluetooth", xalign=0)
        lbl.get_style_context().add_class("page-title")
        content.pack_start(lbl, False, False, 0)

        # 1. Power Switch Card
        powered = get_bluetooth_state()
        card_pwr = SettingsCard()
        self.pwr_sw = Gtk.Switch()
        self.pwr_sw.set_active(powered)
        self.pwr_sw.connect("state-set", self._on_power_switch)
        card_pwr.add_row(
            icon="󰂯",
            title="Bluetooth",
            subtitle="Connect to wireless headphones, keyboards, and accessories",
            widget=self.pwr_sw
        )
        content.pack_start(card_pwr, False, False, 0)

        # 2. Devices Card
        card_devs = SettingsCard(title="PAIRED & DETECTED DEVICES")
        scan_btn = Gtk.Button(label="󰑓 Scan")
        scan_btn.get_style_context().add_class("action-btn")
        scan_btn.connect("clicked", self._on_scan_bt)

        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        sub = Gtk.Label(label="Manage wireless Bluetooth accessories", xalign=0)
        sub.get_style_context().add_class("settings-row-sub")
        top_row.pack_start(sub, True, True, 0)
        top_row.pack_end(scan_btn, False, False, 0)
        card_devs.pack_start(top_row, False, False, 8)

        self.devs_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        card_devs.pack_start(self.devs_box, True, True, 0)
        content.pack_start(card_devs, False, False, 0)

        self._populate_devices()

    def _on_power_switch(self, sw, state):
        cmd = ["bluetoothctl", "power", "on" if state else "off"]
        subprocess.run(cmd, check=False)
        GLib.timeout_add(600, self._populate_devices)
        return False

    def _on_scan_bt(self, btn):
        subprocess.Popen(["bluetoothctl", "--timeout", "5", "scan", "on"])
        GLib.timeout_add(2500, self._populate_devices)

    def _populate_devices(self):
        for c in self.devs_box.get_children():
            self.devs_box.remove(c)

        devs = get_bluetooth_devices()
        if not devs:
            no_lbl = Gtk.Label(label="No devices found or Bluetooth is turned off.", xalign=0)
            no_lbl.get_style_context().add_class("settings-row-sub")
            self.devs_box.pack_start(no_lbl, False, False, 8)
            self.devs_box.show_all()
            return

        for d in devs:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            row.get_style_context().add_class("settings-row")

            icon_lbl = Gtk.Label(label=d["icon"])
            icon_lbl.get_style_context().add_class("settings-row-icon")
            row.pack_start(icon_lbl, False, False, 0)

            txt = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
            name_lbl = Gtk.Label(label=d["name"], xalign=0)
            name_lbl.get_style_context().add_class("settings-row-title")
            st_text = "Connected" if d["connected"] else ("Paired" if d["paired"] else "Available")
            sub_lbl = Gtk.Label(label=f"{d['mac']} • {st_text}", xalign=0)
            sub_lbl.get_style_context().add_class("settings-row-sub")
            txt.pack_start(name_lbl, False, False, 0)
            txt.pack_start(sub_lbl, False, False, 0)
            row.pack_start(txt, True, True, 0)

            act_btn = Gtk.Button(label="Disconnect" if d["connected"] else "Connect")
            act_btn.get_style_context().add_class("action-btn")
            act_btn.connect("clicked", lambda b, mac=d["mac"], con=d["connected"]: self._toggle_con(mac, con))
            row.pack_end(act_btn, False, False, 0)

            self.devs_box.pack_start(row, False, False, 0)

        self.devs_box.show_all()

    def _toggle_con(self, mac, is_connected):
        action = "disconnect" if is_connected else "connect"
        subprocess.run(["bluetoothctl", action, mac], check=False)
        GLib.timeout_add(1000, self._populate_devices)


class SoundPage(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        content.set_margin_start(16)
        content.set_margin_end(16)
        content.set_margin_top(16)
        content.set_margin_bottom(16)
        self.add(content)

        # Header
        lbl = Gtk.Label(label="󰕾 Sound & Audio", xalign=0)
        lbl.get_style_context().add_class("page-title")
        content.pack_start(lbl, False, False, 0)

        # 1. Output Sound Card
        card_out = SettingsCard(title="SOUND OUTPUT (SPEAKERS / HEADPHONES)")

        # Volume slider
        vol_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.vol_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.vol_scale.set_hexpand(True)
        cur_vol = 50
        try:
            out = subprocess.check_output(["pactl", "get-sink-volume", "@DEFAULT_SINK@"], text=True)
            m = re.search(r"(\d+)%", out)
            if m: cur_vol = int(m.group(1))
        except Exception:
            pass
        self.vol_scale.set_value(cur_vol)
        self.vol_scale.connect("value-changed", self._on_volume_change)
        vol_box.pack_start(self.vol_scale, True, True, 0)
        card_out.add_row("󰕾", "Master Volume", "Adjust primary system volume", vol_box)

        # Output Device dropdown
        sinks = get_audio_sinks()
        def_sink = get_default_sink()
        self.sink_combo = Gtk.ComboBoxText()
        cur_idx = 0
        for i, s in enumerate(sinks):
            self.sink_combo.append(s["name"], s.get("desc", s["name"]))
            if s["name"] == def_sink:
                cur_idx = i
        if sinks:
            self.sink_combo.set_active(cur_idx)
        self.sink_combo.connect("changed", self._on_sink_changed)
        card_out.add_row("󰓃", "Output Device", "Choose audio playback destination", self.sink_combo)

        # Test sound button
        test_btn = Gtk.Button(label="󰐊 Play Test Sound")
        test_btn.get_style_context().add_class("action-btn")
        test_btn.connect("clicked", lambda b: subprocess.Popen(["paplay", "/usr/share/sounds/freedesktop/stereo/bell.oga"]))
        card_out.add_row("󰎈", "Speaker Test", "Check that audio output is working properly", test_btn)
        content.pack_start(card_out, False, False, 0)

        # 2. Input Microphone Card
        card_in = SettingsCard(title="SOUND INPUT (MICROPHONE)")
        sources = get_audio_sources()
        def_src = get_default_source()
        self.src_combo = Gtk.ComboBoxText()
        cur_s_idx = 0
        for i, s in enumerate(sources):
            self.src_combo.append(s["name"], s.get("desc", s["name"]))
            if s["name"] == def_src:
                cur_s_idx = i
        if sources:
            self.src_combo.set_active(cur_s_idx)
        self.src_combo.connect("changed", self._on_source_changed)
        card_in.add_row("󰍬", "Microphone Device", "Select audio recording source", self.src_combo)

        # Mic Mute Toggle
        mic_muted = False
        try:
            m_out = subprocess.check_output(["pactl", "get-source-mute", "@DEFAULT_SOURCE@"], text=True)
            mic_muted = "yes" in m_out.lower()
        except Exception:
            pass
        self.mic_sw = Gtk.Switch()
        self.mic_sw.set_active(not mic_muted)
        self.mic_sw.connect("state-set", lambda sw, st: subprocess.run(["pactl", "set-source-mute", "@DEFAULT_SOURCE@", "0" if st else "1"], check=False) or False)
        card_in.add_row("󰍭", "Microphone Active", "Enable voice recording input", self.mic_sw)
        content.pack_start(card_in, False, False, 0)

    def _on_volume_change(self, scale):
        val = int(round(scale.get_value()))
        subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{val}%"], check=False)

    def _on_sink_changed(self, combo):
        name = combo.get_active_id()
        if name:
            subprocess.run(["pactl", "set-default-sink", name], check=False)
            try:
                inp_out = subprocess.check_output(["pactl", "list", "short", "sink-inputs"], text=True)
                for line in inp_out.splitlines():
                    if line:
                        subprocess.run(["pactl", "move-sink-input", line.split()[0], name], check=False)
            except Exception:
                pass

    def _on_source_changed(self, combo):
        name = combo.get_active_id()
        if name:
            subprocess.run(["pactl", "set-default-source", name], check=False)


class DisplayPage(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        content.set_margin_start(16)
        content.set_margin_end(16)
        content.set_margin_top(16)
        content.set_margin_bottom(16)
        self.add(content)

        # Header
        lbl = Gtk.Label(label="󰍹 Display & Brightness", xalign=0)
        lbl.get_style_context().add_class("page-title")
        content.pack_start(lbl, False, False, 0)

        # 1. Brightness Card
        card_bri = SettingsCard(title="DISPLAY BRIGHTNESS")
        cur_bri = get_brightness()
        self.bri_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 10, 100, 1)
        self.bri_scale.set_value(cur_bri)
        self.bri_scale.set_hexpand(True)
        self.bri_scale.connect("value-changed", lambda s: set_brightness(int(round(s.get_value()))))
        card_bri.add_row("󰃠", "Brightness Level", "Adjust screen backlight", self.bri_scale)

        # Night Light Gamma
        self.night_sw = Gtk.Switch()
        self.night_sw.set_active(False)
        self.night_sw.connect("state-set", self._on_night_light)
        card_bri.add_row("󱤓", "Night Light (Blue Light Filter)", "Warm colors to reduce eye strain during evening hours", self.night_sw)
        content.pack_start(card_bri, False, False, 0)

        # 2. Monitors Card
        displays = get_displays_info()
        card_disp = SettingsCard(title="CONNECTED MONITORS")
        for d in displays:
            pri_str = " (Primary)" if d["primary"] else ""
            res_cur = d["geom"]

            res_combo = Gtk.ComboBoxText()
            for m in d["modes"]:
                res_combo.append(m["res"], f"{m['res']} ({', '.join(m['rates'][:2])} Hz)")
            if d["modes"]:
                res_combo.set_active(0)

            card_disp.add_row(
                "󰍹",
                f"{d['name']}{pri_str}",
                f"Current resolution: {res_cur}",
                res_combo
            )
        content.pack_start(card_disp, False, False, 0)

    def _on_night_light(self, sw, state):
        gamma = "1.0:0.85:0.7" if state else "1.0:1.0:1.0"
        try:
            out = subprocess.check_output(["xrandr", "--query"], text=True)
            for line in out.splitlines():
                if " connected" in line:
                    mon = line.split()[0]
                    subprocess.run(["xrandr", "--output", mon, "--gamma", gamma], check=False)
        except Exception:
            pass
        return False


class AppearancePage(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        content.set_margin_start(16)
        content.set_margin_end(16)
        content.set_margin_top(16)
        content.set_margin_bottom(16)
        self.add(content)

        # Header
        lbl = Gtk.Label(label="󰏘 Appearance & Themes", xalign=0)
        lbl.get_style_context().add_class("page-title")
        content.pack_start(lbl, False, False, 0)

        # 1. Catppuccin Accents
        card_acc = SettingsCard(title="CATPPUCCIN MOCHA ACCENT COLOR")
        acc_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        acc_box.set_margin_start(12)
        acc_box.set_margin_end(12)
        acc_box.set_margin_bottom(10)

        accents = [
            ("#89b4fa", "Blue"),
            ("#74c7ec", "Sapphire"),
            ("#b4befe", "Lavender"),
            ("#cba6f7", "Mauve"),
            ("#f5c2e7", "Pink"),
            ("#f2cdcd", "Flamingo"),
            ("#f38ba8", "Red"),
            ("#fab387", "Peach"),
            ("#f9e2af", "Yellow"),
            ("#a6e3a1", "Green"),
            ("#94e2d5", "Teal"),
        ]

        cur_acc = get_accent_color().lower()
        for hex_col, name in accents:
            btn = Gtk.Button()
            btn.set_tooltip_text(f"{name} ({hex_col})")
            btn.get_style_context().add_class("color-swatch-btn")
            prov = Gtk.CssProvider()
            border_col = "#ffffff" if hex_col.lower() == cur_acc else "#313244"
            css = f"button, button.color-swatch-btn {{ background-image: none; background-color: {hex_col}; background: {hex_col}; min-width: 32px; min-height: 32px; border: 2px solid {border_col}; border-radius: 0px; box-shadow: none; }}"
            prov.load_from_data(css.encode())
            btn.get_style_context().add_provider(prov, Gtk.STYLE_PROVIDER_PRIORITY_USER)
            btn.connect("clicked", lambda b, h=hex_col: self._on_pick_accent(h))
            acc_box.pack_start(btn, False, False, 0)

        card_acc.pack_start(acc_box, False, False, 0)
        content.pack_start(card_acc, False, False, 0)

        # 2. Synchronized System Transparency
        card_term = SettingsCard(title="SYSTEM TRANSPARENCY & BLUR")
        cur_op_pct = int(round(get_system_opacity() * 100))
        self.op_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 30, 100, 1)
        self.op_scale.set_value(cur_op_pct)
        self.op_scale.set_hexpand(True)
        self.op_scale.connect("value-changed", self._on_opacity_change)
        self.op_row = card_term.add_row(
            icon="󰞕",
            title="Window & Terminal Opacity",
            subtitle=f"Current: {cur_op_pct}% (Synced with Alacritty & Control Center)",
            widget=self.op_scale
        )
        content.pack_start(card_term, False, False, 0)

        # 3. Wallpapers Gallery
        card_wp = SettingsCard(title="WALLPAPERS GALLERY (~/Pictures/Wallpapers)")
        wps = get_wallpapers()
        if wps:
            wp_flow = Gtk.FlowBox()
            wp_flow.set_valign(Gtk.Align.START)
            wp_flow.set_max_children_per_line(3)
            wp_flow.set_selection_mode(Gtk.SelectionMode.NONE)
            wp_flow.set_column_spacing(10)
            wp_flow.set_row_spacing(10)
            wp_flow.set_margin_start(10)
            wp_flow.set_margin_end(10)
            wp_flow.set_margin_bottom(10)

            for wp_path in wps:
                wp_btn = Gtk.Button()
                wp_btn.get_style_context().add_class("wp-item-btn")
                wp_btn_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
                name_lbl = Gtk.Label(label=os.path.basename(wp_path))
                name_lbl.set_ellipsize(Pango.EllipsizeMode.END)
                name_lbl.set_max_width_chars(20)
                wp_btn_box.pack_start(Gtk.Label(label="󰸉"), False, False, 0)
                wp_btn_box.pack_start(name_lbl, False, False, 0)
                wp_btn.add(wp_btn_box)
                wp_btn.connect("clicked", lambda b, p=wp_path: subprocess.Popen([os.path.expanduser("~/.config/theme/apply-theme.sh"), p]))
                wp_flow.add(wp_btn)

            card_wp.pack_start(wp_flow, False, False, 0)
        else:
            no_wp = Gtk.Label(label="No wallpapers found in ~/Pictures/Wallpapers", xalign=0)
            card_wp.pack_start(no_wp, False, False, 8)

        content.pack_start(card_wp, False, False, 0)

    def _on_pick_accent(self, hex_col):
        apply_accent_color(hex_col)
        toplevel = self.get_toplevel()
        if hasattr(toplevel, "_apply_css"):
            toplevel._apply_css()

    def _on_opacity_change(self, scale):
        pct = int(round(scale.get_value()))
        set_system_opacity(pct)
        # Update subtitle
        txt_box = self.op_row.get_children()[1]
        if hasattr(txt_box, "get_children") and len(txt_box.get_children()) >= 2:
            sub = txt_box.get_children()[1]
            sub.set_text(f"Current: {pct}% (Synced with Alacritty & Control Center)")
        # Live reload CSS on Settings window
        toplevel = self.get_toplevel()
        if hasattr(toplevel, "_apply_css"):
            toplevel._apply_css()


class NotificationsPage(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        content.set_margin_start(16)
        content.set_margin_end(16)
        content.set_margin_top(16)
        content.set_margin_bottom(16)
        self.add(content)

        # Header
        lbl = Gtk.Label(label="󰂚 Notifications & Dunst", xalign=0)
        lbl.get_style_context().add_class("page-title")
        content.pack_start(lbl, False, False, 0)

        # 1. Do Not Disturb
        is_paused = False
        try:
            out = subprocess.check_output(["dunstctl", "is-paused"], text=True).strip()
            is_paused = (out == "true")
        except Exception:
            pass

        card_dnd = SettingsCard(title="DO NOT DISTURB MODE")
        self.dnd_sw = Gtk.Switch()
        self.dnd_sw.set_active(is_paused)
        self.dnd_sw.connect("state-set", lambda sw, st: subprocess.run(["dunstctl", "set-paused", "true" if st else "false"], check=False) or False)
        card_dnd.add_row("󱤓", "Mute Notifications", "Pause on-screen notification popups", self.dnd_sw)
        content.pack_start(card_dnd, False, False, 0)

        # 2. Test Notification Card
        card_test = SettingsCard(title="NOTIFICATION TEST & CONTROLS")
        norm_btn = Gtk.Button(label="Send Normal Alert")
        norm_btn.get_style_context().add_class("action-btn")
        norm_btn.connect("clicked", lambda b: subprocess.run(["dunstify", "-u", "normal", "󰂚 Normal Alert", "This is a test notification from Desktop Settings!"], check=False))
        card_test.add_row("󰵅", "Informational Notification", "Send a standard alert", norm_btn)

        crit_btn = Gtk.Button(label="Send Urgent Alert")
        crit_btn.get_style_context().add_class("action-btn")
        crit_btn.connect("clicked", lambda b: subprocess.run(["dunstify", "-u", "critical", "󰀪 Urgent Alert", "Critical priority test notification!"], check=False))
        card_test.add_row("󰀪", "Urgent Alert", "Send an urgent persistent popup", crit_btn)

        clear_btn = Gtk.Button(label="Clear All")
        clear_btn.get_style_context().add_class("action-btn")
        clear_btn.connect("clicked", lambda b: subprocess.run(["dunstctl", "close-all"], check=False))
        card_test.add_row("󰅖", "Clear Screen", "Dismiss all active on-screen popups", clear_btn)
        content.pack_start(card_test, False, False, 0)


class ShortcutsPage(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        content.set_margin_start(16)
        content.set_margin_end(16)
        content.set_margin_top(16)
        content.set_margin_bottom(16)
        self.add(content)

        # Header
        lbl = Gtk.Label(label="󰌌 i3 Keyboard Shortcuts", xalign=0)
        lbl.get_style_context().add_class("page-title")
        content.pack_start(lbl, False, False, 0)

        # Search Bar
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Filter by key or command (e.g. Super, terminal, focus)...")
        self.search_entry.connect("search-changed", self._on_search_changed)
        content.pack_start(self.search_entry, False, False, 0)

        # Shortcuts Table Card
        self.card_keys = SettingsCard(title="CONFIGURED BINDINGS (~/.config/i3/config)")
        content.pack_start(self.card_keys, True, True, 0)

        self.all_shortcuts = get_i3_shortcuts()
        self._populate_shortcuts(self.all_shortcuts)

    def _on_search_changed(self, entry):
        query = entry.get_text().lower().strip()
        if not query:
            self._populate_shortcuts(self.all_shortcuts)
            return
        filtered = [s for s in self.all_shortcuts if query in s[0].lower() or query in s[1].lower() or query in s[2].lower()]
        self._populate_shortcuts(filtered)

    def _populate_shortcuts(self, shortcuts):
        for c in self.card_keys.rows_box.get_children():
            self.card_keys.rows_box.remove(c)
        self.card_keys._count = 0

        for key, desc, cmd in shortcuts[:40]:
            badge = Gtk.Label(label=key)
            badge.get_style_context().add_class("key-badge")
            self.card_keys.add_row("󰌌", desc, subtitle=cmd, widget=badge)

        self.card_keys.show_all()


class SystemPage(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        content.set_margin_start(16)
        content.set_margin_end(16)
        content.set_margin_top(16)
        content.set_margin_bottom(16)
        self.add(content)

        # Header
        lbl = Gtk.Label(label="󰘚 System Information & Dotfiles", xalign=0)
        lbl.get_style_context().add_class("page-title")
        content.pack_start(lbl, False, False, 0)

        specs = get_system_specs()

        # 1. Hardware Specs Card
        card_hw = SettingsCard(title="HARDWARE & SYSTEM SPECIFICATIONS")
        card_hw.add_row("", "Device / User", f"{specs['user']}@{specs['hostname']}")
        card_hw.add_row("󰣇", "OS Distribution", specs["os"])
        card_hw.add_row("", "Linux Kernel", specs["kernel"])
        card_hw.add_row("", "Processor (CPU)", specs["cpu"])
        card_hw.add_row("󰾲", "Graphics Card (GPU)", specs["gpu"])
        card_hw.add_row("", "Total RAM Memory", specs["ram_total"])
        card_hw.add_row("󰉉", "Root Disk Space (/)", specs["disk_used"])
        content.pack_start(card_hw, False, False, 0)

        # 2. Dotfiles Management Card
        card_git = SettingsCard(title="CONFIGURATIONS SYNC (DOTFILES)")
        dotfiles_dir = os.path.expanduser("~/.local/share/dotfiles")
        branch = "experimental/control-center"
        commit_msg = "Up to date"
        if os.path.exists(dotfiles_dir):
            try:
                b_out = subprocess.check_output(["git", "-C", dotfiles_dir, "branch", "--show-current"], text=True).strip()
                if b_out: branch = b_out
                c_out = subprocess.check_output(["git", "-C", dotfiles_dir, "log", "-1", "--oneline"], text=True).strip()
                if c_out: commit_msg = c_out
            except Exception:
                pass

        card_git.add_row("", "Active Dotfiles Branch", branch)
        card_git.add_row("󰊢", "Latest Local Commit", commit_msg)

        sync_btn = Gtk.Button(label="󰑓 Sync Configs")
        sync_btn.get_style_context().add_class("action-btn")
        sync_btn.connect("clicked", self._on_sync_dotfiles)
        card_git.add_row("󰄬", "Update Desktop", "Pull and apply latest dotfiles configuration", sync_btn)

        content.pack_start(card_git, False, False, 0)

    def _on_sync_dotfiles(self, btn):
        subprocess.Popen(["alacritty", "--hold", "-e", "dotfiles", "status"])


# ------------------------------------------------------------------------------
# Main Window & Application Shell
# ------------------------------------------------------------------------------

class DesktopSettingsWindow(Gtk.Window):
    def __init__(self, initial_page=None):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)

        GLib.set_prgname("DesktopSettings")
        self.set_wmclass("DesktopSettings", "DesktopSettings")
        self.set_name("DesktopSettings")
        self.set_title("Desktop Settings")
        self.set_default_size(940, 640)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_decorated(False)
        self.set_app_paintable(True)

        # Enable translucency matching Alacritty
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)

        self.get_style_context().add_class("desktop-settings")

        self._apply_css()

        # Main Layout
        root_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        root_box.get_style_context().add_class("main-window")
        self.add(root_box)

        # Header bar (Draggable)
        header = Gtk.EventBox()
        header.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        header.connect("button-press-event", self._on_header_drag)

        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header_box.get_style_context().add_class("header-bar")
        header.add(header_box)

        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        gear_icon = Gtk.Label(label="󰒓")
        gear_icon.get_style_context().add_class("header-gear")
        win_title = Gtk.Label(label="Settings", xalign=0)
        win_title.get_style_context().add_class("header-title")
        title_box.pack_start(gear_icon, False, False, 0)
        title_box.pack_start(win_title, False, False, 0)
        header_box.pack_start(title_box, False, False, 0)

        close_btn = Gtk.Button(label="󰅖")
        close_btn.get_style_context().add_class("header-close-btn")
        close_btn.connect("clicked", lambda b: self.destroy())
        header_box.pack_end(close_btn, False, False, 0)

        root_box.pack_start(header, False, False, 0)
        root_box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)

        # Dual-pane body
        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        root_box.pack_start(body, True, True, 0)

        # Sidebar (Left)
        sidebar_scroll = Gtk.ScrolledWindow()
        sidebar_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        sidebar_scroll.set_size_request(260, -1)
        sidebar_scroll.get_style_context().add_class("sidebar-container")

        self.sidebar_list = Gtk.ListBox()
        self.sidebar_list.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.sidebar_list.get_style_context().add_class("sidebar-list")
        self.sidebar_list.connect("row-selected", self._on_sidebar_selected)
        sidebar_scroll.add(self.sidebar_list)
        body.pack_start(sidebar_scroll, False, False, 0)

        body.pack_start(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL), False, False, 0)

        # Stack (Right)
        self.stack = Gtk.Stack()
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        self.stack.set_transition_duration(180)
        self.stack.get_style_context().add_class("content-stack")
        body.pack_start(self.stack, True, True, 0)

        # Pages definition (Strictly English)
        self.pages = [
            ("wifi", "󰤨", "Network & Wi-Fi", NetworkPage()),
            ("bluetooth", "󰂯", "Bluetooth", BluetoothPage()),
            ("sound", "󰕾", "Sound & Audio", SoundPage()),
            ("display", "󰍹", "Display & Brightness", DisplayPage()),
            ("appearance", "󰏘", "Appearance & Themes", AppearancePage()),
            ("notifications", "󰂚", "Notifications", NotificationsPage()),
            ("shortcuts", "󰌌", "Keyboard Shortcuts", ShortcutsPage()),
            ("system", "󰘚", "System & Dotfiles", SystemPage()),
        ]

        self.page_rows = {}
        for pid, icon, title, page_widget in self.pages:
            self.stack.add_named(page_widget, pid)

            row = Gtk.ListBoxRow()
            row.get_style_context().add_class("sidebar-row")
            r_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            r_box.set_margin_start(12)
            r_box.set_margin_end(12)
            r_box.set_margin_top(10)
            r_box.set_margin_bottom(10)

            ic = Gtk.Label(label=icon)
            ic.get_style_context().add_class("sidebar-icon")
            lbl = Gtk.Label(label=title, xalign=0)
            lbl.get_style_context().add_class("sidebar-title")

            r_box.pack_start(ic, False, False, 0)
            r_box.pack_start(lbl, True, True, 0)
            row.add(r_box)
            row.page_id = pid

            self.sidebar_list.add(row)
            self.page_rows[pid] = row

        self.connect("key-press-event", self._on_key_press)

        # Select initial page
        self.initial_target = initial_page if (initial_page and initial_page in self.page_rows) else "wifi"
        self.set_active_page(self.initial_target)

    def _on_header_drag(self, widget, event):
        if event.button == 1:
            self.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)

    def set_active_page(self, page_id):
        if page_id in self.page_rows:
            self.sidebar_list.select_row(self.page_rows[page_id])
            self.stack.set_visible_child_name(page_id)

    def show_all(self):
        super().show_all()
        if hasattr(self, "initial_target") and self.initial_target:
            self.set_active_page(self.initial_target)

    def _apply_css(self):
        accent = get_accent_color()
        opacity = get_system_opacity()
        css_path = os.path.expanduser("~/.config/desktop-settings/style.css")
        if not os.path.exists(css_path):
            css_path = os.path.expanduser("~/.local/share/dotfiles/config/desktop-settings/style.css")

        if os.path.exists(css_path):
            with open(css_path, "r") as f:
                raw = f.read()
            css_data = (
                raw.replace("@accent@", accent)
                   .replace("@opacity@", f"{opacity:.2f}")
                   .replace("@header_opacity@", f"{min(1.0, opacity + 0.10):.2f}")
                   .replace("@sidebar_opacity@", f"{min(1.0, opacity + 0.05):.2f}")
                   .replace("@card_opacity@", f"{max(0.3, opacity * 0.85):.2f}")
            )
            provider = Gtk.CssProvider()
            provider.load_from_data(css_data.encode("utf-8"))
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(),
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_USER
            )

    def _on_sidebar_selected(self, listbox, row):
        if row and hasattr(row, "page_id"):
            self.stack.set_visible_child_name(row.page_id)

    def _on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()
            return True
        return False


# ------------------------------------------------------------------------------
# Entry Point
# ------------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Catppuccin Mocha Desktop Settings")
    parser.add_argument("--page", "-p", choices=["wifi", "network", "bluetooth", "sound", "audio", "display", "appearance", "notifications", "shortcuts", "system"], default=None, help="Directly open a specific settings page")
    args = parser.parse_args()

    page_map = {
        "network": "wifi",
        "audio": "sound",
    }
    target_page = page_map.get(args.page, args.page)

    win = DesktopSettingsWindow(initial_page=target_page)
    win.connect("destroy", Gtk.main_quit)
    win.show_all()
    Gtk.main()


if __name__ == "__main__":
    main()
