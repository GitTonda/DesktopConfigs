#!/usr/bin/env python3
"""
Catppuccin Mocha Unified Control Center
Flyout quick settings panel anchored under Polybar in top-right corner.
"""

import os
import sys
import subprocess
import shutil
import time
import re
import json
import threading
import signal

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import Gtk, Gdk, GLib, Pango


PID_FILE = os.path.expanduser("~/.cache/control_center.pid")


# ------------------------------------------------------------------------------
# Helpers & System State Queries
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


def get_system_opacity():
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


def get_audio_state():
    vol = 50
    muted = False
    try:
        out = subprocess.check_output(["pactl", "get-sink-volume", "@DEFAULT_SINK@"], text=True, stderr=subprocess.DEVNULL)
        m = re.search(r"(\d+)%", out)
        if m:
            vol = int(m.group(1))
    except Exception:
        pass

    try:
        out = subprocess.check_output(["pactl", "get-sink-mute", "@DEFAULT_SINK@"], text=True, stderr=subprocess.DEVNULL)
        muted = "yes" in out.lower()
    except Exception:
        pass

    # Source / Mic mute
    mic_muted = False
    try:
        out = subprocess.check_output(["pactl", "get-source-mute", "@DEFAULT_SOURCE@"], text=True, stderr=subprocess.DEVNULL)
        mic_muted = "yes" in out.lower()
    except Exception:
        pass

    # Active sink description
    sink_desc = "Default Audio Output"
    try:
        out = subprocess.check_output(["pactl", "list", "sinks"], text=True, stderr=subprocess.DEVNULL)
        desc_matches = re.findall(r"Description:\s+(.*)", out)
        if desc_matches:
            sink_desc = desc_matches[0].strip()
    except Exception:
        pass

    return {
        "volume": min(100, max(0, vol)),
        "muted": muted,
        "mic_muted": mic_muted,
        "sink_desc": sink_desc
    }


def get_wifi_state():
    enabled = False
    ssid = "Disconnected"
    try:
        radio = subprocess.check_output(["nmcli", "-t", "-f", "WIFI", "g"], text=True, stderr=subprocess.DEVNULL).strip()
        enabled = (radio == "enabled")
        if enabled:
            out = subprocess.check_output(["nmcli", "-t", "-f", "NAME,TYPE", "c", "show", "--active"], text=True, stderr=subprocess.DEVNULL)
            for line in out.splitlines():
                parts = line.rsplit(":", 1)
                if len(parts) == 2 and "wireless" in parts[1]:
                    ssid = parts[0]
                    break
    except Exception:
        pass
    return {"enabled": enabled, "ssid": ssid}


def get_bluetooth_state():
    powered = False
    device_name = "Disconnected"
    try:
        rf = subprocess.check_output(["rfkill", "list", "bluetooth"], text=True, stderr=subprocess.DEVNULL)
        if "Soft blocked: yes" in rf or "Hard blocked: yes" in rf:
            return {"powered": False, "device": "Off"}
    except Exception:
        pass
    try:
        out = subprocess.check_output(["bluetoothctl", "show"], text=True, stderr=subprocess.DEVNULL)
        powered = "Powered: yes" in out
        if powered:
            con = subprocess.check_output(["bluetoothctl", "devices", "Connected"], text=True, stderr=subprocess.DEVNULL).strip()
            if con:
                lines = con.splitlines()
                # Line format: "Device XX:XX:XX:XX:XX:XX DeviceName"
                parts = lines[0].split(" ", 2)
                device_name = parts[2] if len(parts) >= 3 else "Connected"
            else:
                device_name = "Active"
        else:
            device_name = "Off"
    except Exception:
        pass
    return {"powered": powered, "device": device_name}


def get_dnd_state():
    is_paused = False
    try:
        out = subprocess.check_output(["dunstctl", "is-paused"], text=True, stderr=subprocess.DEVNULL).strip()
        is_paused = (out == "true")
    except Exception:
        pass
    return is_paused


def get_brightness():
    # 0. Check cache file
    cache_file = os.path.expanduser("~/.config/theme/brightness")
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r") as f:
                val = int(f.read().strip())
                return max(10, min(100, val))
        except Exception:
            pass

    # 1. Check brightnessctl backlight class
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

    # 2. Check xrandr
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

    # 1. Check brightnessctl
    try:
        out = subprocess.check_output(["brightnessctl", "-m"], text=True, stderr=subprocess.DEVNULL)
        for line in out.splitlines():
            parts = line.split(",")
            if len(parts) >= 5 and parts[1] == "backlight":
                subprocess.run(["brightnessctl", "set", f"{pct}%"], check=False)
                return
    except Exception:
        pass

    # 2. Check xrandr
    try:
        out = subprocess.check_output(["xrandr", "--query"], text=True, stderr=subprocess.DEVNULL)
        outputs = [line.split()[0] for line in out.splitlines() if " connected" in line]
        ratio = round(pct / 100.0, 2)
        for mon in outputs:
            subprocess.run(["xrandr", "--output", mon, "--brightness", str(ratio)], check=False)
    except Exception:
        pass


def get_media_info():
    try:
        status = subprocess.check_output(["playerctl", "status"], text=True, stderr=subprocess.DEVNULL).strip()
        if status in ("Playing", "Paused"):
            artist = subprocess.check_output(["playerctl", "metadata", "artist"], text=True, stderr=subprocess.DEVNULL).strip()
            title = subprocess.check_output(["playerctl", "metadata", "title"], text=True, stderr=subprocess.DEVNULL).strip()
            player = subprocess.check_output(["playerctl", "metadata", "--format", "{{playerName}}"], text=True, stderr=subprocess.DEVNULL).strip()
            return {
                "active": True,
                "status": status,
                "artist": artist or "Unknown Artist",
                "title": title or "Unknown Title",
                "player": player or "Media Player"
            }
    except Exception:
        pass
    return {"active": False}


def get_memory_info():
    total_gb = 0.0
    used_gb = 0.0
    pct = 0
    try:
        with open("/proc/meminfo", "r") as f:
            lines = f.readlines()
        data = {}
        for line in lines:
            parts = line.split(":")
            if len(parts) == 2:
                data[parts[0].strip()] = int(parts[1].split()[0])
        total = data.get("MemTotal", 1)
        avail = data.get("MemAvailable", total)
        used = total - avail
        pct = int(round((used / total) * 100))
        total_gb = total / (1024.0 * 1024.0)
        used_gb = used / (1024.0 * 1024.0)
    except Exception:
        pass
    return {"pct": pct, "used_gb": used_gb, "total_gb": total_gb}


_last_cpu_time = 0.0
_last_cpu_stat = (0.0, 0.0)


def _read_proc_stat():
    try:
        with open("/proc/stat", "r") as f:
            parts = f.readline().split()[1:]
            vals = [float(x) for x in parts]
            total = sum(vals)
            idle = vals[3] + (vals[4] if len(parts) > 4 else 0.0)
            return total, idle
    except Exception:
        return 0.0, 0.0


def get_cpu_info():
    global _last_cpu_time, _last_cpu_stat
    now = time.time()
    t, i = _read_proc_stat()
    if _last_cpu_stat[0] > 0 and (now - _last_cpu_time) > 0.05:
        dt = t - _last_cpu_stat[0]
        di = i - _last_cpu_stat[1]
        _last_cpu_stat = (t, i)
        _last_cpu_time = now
        if dt > 0:
            pct = int(round(100.0 * (1.0 - (di / dt))))
            return min(100, max(0, pct))
    _last_cpu_stat = (t, i)
    _last_cpu_time = now
    try:
        with open("/proc/loadavg", "r") as f:
            load = float(f.read().split()[0])
            cpus = os.cpu_count() or 1
            return int(min(100, max(0, round((load / cpus) * 100))))
    except Exception:
        return 0


# ------------------------------------------------------------------------------
# Main Window Class
# ------------------------------------------------------------------------------

class ControlCenterWindow(Gtk.Window):
    def __init__(self):
        super().__init__(type=Gtk.WindowType.TOPLEVEL)

        GLib.set_prgname("ControlCenter")
        self.set_wmclass("ControlCenter", "ControlCenter")
        self.set_name("ControlCenter")
        self.set_title("ControlCenter")
        self.set_role("pop-up")
        self.set_decorated(False)
        self.set_resizable(False)
        self.set_default_size(390, -1)
        self.set_app_paintable(True)
        self.set_skip_taskbar_hint(True)
        self.set_skip_pager_hint(True)
        self.set_keep_above(True)

        # Translucency visual
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual and screen.is_composited():
            self.set_visual(visual)

        self.get_style_context().add_class("control-center")

        # Load states
        self.audio_state = get_audio_state()
        self.wifi_state = get_wifi_state()
        self.bt_state = get_bluetooth_state()
        self.dnd_state = get_dnd_state()
        self.brightness = get_brightness()
        self.media_info = get_media_info()

        # Focus settling flag
        self._settled = False

        self._build_ui()
        self._apply_css()

        # Telemetry live refresh
        GLib.timeout_add(1500, self._update_hw_stats)

        # Listen for workspace switches to dismiss automatically
        self._start_workspace_listener()

        # Enable pointer and focus events
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK | Gdk.EventMask.FOCUS_CHANGE_MASK)

        # Connect events
        self.connect("map-event", self._on_map)
        self.connect("button-press-event", self._on_button_press)
        self.connect("focus-out-event", self._on_focus_out)
        self.connect("key-press-event", self._on_key_press)
        self.connect("destroy", self._on_destroy)

    def _start_workspace_listener(self):
        def _watch():
            try:
                self._i3_sub_proc = subprocess.Popen(
                    ["i3-msg", "-t", "subscribe", "-m", '["workspace"]'],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL,
                    text=True
                )
                for line in self._i3_sub_proc.stdout:
                    try:
                        data = json.loads(line)
                        if data.get("change") in ("focus", "init"):
                            current_ws = data.get("current", {}).get("name")
                            old_ws = data.get("old", {}).get("name")
                            if old_ws is not None and current_ws != old_ws:
                                GLib.idle_add(self.destroy)
                                break
                    except Exception:
                        pass
            except Exception:
                pass

        t = threading.Thread(target=_watch, daemon=True)
        t.start()

    def _on_map(self, widget, event):
        seat = Gdk.Display.get_default().get_default_seat()
        if seat:
            seat.grab(self.get_window(), Gdk.SeatCapabilities.ALL, True, None, None, None)
        GLib.timeout_add(150, self._mark_settled)

    def _mark_settled(self):
        self._settled = True
        return False

    def _on_button_press(self, widget, event):
        alloc = self.get_allocation()
        # Any click outside the control center bounds dismisses it
        if event.x < 0 or event.y < 0 or event.x > alloc.width or event.y > alloc.height:
            if self._settled:
                self.destroy()
                return True
        return False

    def _on_destroy(self, widget):
        if hasattr(self, '_i3_sub_proc') and self._i3_sub_proc:
            try:
                self._i3_sub_proc.terminate()
            except Exception:
                pass
        try:
            seat = Gdk.Display.get_default().get_default_seat()
            if seat:
                seat.ungrab()
        except Exception:
            pass
        if os.path.exists(PID_FILE):
            try:
                os.remove(PID_FILE)
            except Exception:
                pass
        Gtk.main_quit()

    def _apply_css(self):
        accent = get_accent_color()
        opacity = get_system_opacity()
        try:
            h = accent.lstrip('#')
            r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
            accent_dim = f"rgba({r}, {g}, {b}, 0.20)"
            accent_border = f"rgba({r}, {g}, {b}, 0.45)"
        except Exception:
            accent_dim = "rgba(137, 180, 250, 0.20)"
            accent_border = "rgba(137, 180, 250, 0.45)"

        css_path = os.path.expanduser("~/.config/control-center/style.css")
        if not os.path.exists(css_path):
            css_path = os.path.expanduser("~/.local/share/dotfiles/config/control-center/style.css")
        if os.path.exists(css_path):
            with open(css_path, "r") as f:
                raw_css = f.read()
            css_data = (raw_css
                .replace("@accent@", accent)
                .replace("@accent_dim@", accent_dim)
                .replace("@accent_border@", accent_border)
                .replace("@opacity@", f"{opacity:.2f}")
            )
            provider = Gtk.CssProvider()
            provider.load_from_data(css_data.encode("utf-8"))
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(),
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_USER
            )

    def _build_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        main_box.get_style_context().add_class("main-box")
        self.add(main_box)

        # 1. Header (User & Hostname & Close)
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        header_box.get_style_context().add_class("header-box")

        os_icon = Gtk.Label(label="")
        os_icon.get_style_context().add_class("pill-icon")
        header_box.pack_start(os_icon, False, False, 0)

        user_host_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        user = os.environ.get("USER", "user")
        hostname = "borch"
        try:
            with open("/etc/hostname", "r") as f:
                hostname = f.read().strip()
        except Exception:
            pass

        user_lbl = Gtk.Label(label=f"{user}@{hostname}", xalign=0)
        user_lbl.get_style_context().add_class("header-user")
        
        # Simple uptime
        up_str = "Session Active"
        try:
            with open("/proc/uptime", "r") as f:
                up_sec = float(f.readline().split()[0])
                h = int(up_sec // 3600)
                m = int((up_sec % 3600) // 60)
                up_str = f"Uptime: {h}h {m}m"
        except Exception:
            pass

        host_lbl = Gtk.Label(label=up_str, xalign=0)
        host_lbl.get_style_context().add_class("header-host")

        user_host_box.pack_start(user_lbl, False, False, 0)
        user_host_box.pack_start(host_lbl, False, False, 0)
        header_box.pack_start(user_host_box, True, True, 0)

        close_btn = Gtk.Button(label="󰅖")
        close_btn.get_style_context().add_class("close-btn")
        close_btn.connect("clicked", lambda b: self.destroy())
        header_box.pack_end(close_btn, False, False, 0)

        # Settings App button (opens desktop-settings)
        settings_btn = Gtk.Button(label="󰒓")
        settings_btn.get_style_context().add_class("settings-btn")
        settings_btn.set_tooltip_text("Open Settings")
        settings_btn.connect("clicked", self._on_open_settings)
        header_box.pack_end(settings_btn, False, False, 4)

        main_box.pack_start(header_box, False, False, 0)
        main_box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)

        # 2. Quick Toggles Grid (Wi-Fi, Bluetooth, Mute, Mic, DND, Wallpaper)
        toggles_title = Gtk.Label(label="QUICK TOGGLES", xalign=0)
        toggles_title.get_style_context().add_class("section-title")
        main_box.pack_start(toggles_title, False, False, 0)

        grid = Gtk.Grid()
        grid.set_column_spacing(6)
        grid.set_row_spacing(6)
        grid.set_column_homogeneous(True)

        # Wi-Fi Pill
        self.wifi_btn, self.wifi_icon, self.wifi_sub = self._create_toggle_pill(
            icon="󰤨" if self.wifi_state["enabled"] else "󰤮",
            title="Wi-Fi",
            status=self.wifi_state["ssid"],
            is_active=self.wifi_state["enabled"],
            has_chevron=True
        )
        self.wifi_btn.connect("clicked", self._on_toggle_wifi)
        self.wifi_btn.connect("button-press-event", self._on_wifi_right_click)
        grid.attach(self.wifi_btn, 0, 0, 1, 1)

        # Bluetooth Pill
        self.bt_btn, self.bt_icon, self.bt_sub = self._create_toggle_pill(
            icon="󰂯" if self.bt_state["powered"] else "󰂲",
            title="Bluetooth",
            status=self.bt_state["device"],
            is_active=self.bt_state["powered"],
            has_chevron=True
        )
        self.bt_btn.connect("clicked", self._on_toggle_bt)
        self.bt_btn.connect("button-press-event", self._on_bt_right_click)
        grid.attach(self.bt_btn, 1, 0, 1, 1)

        # Audio Mute Pill
        self.mute_btn, self.mute_icon, self.mute_sub = self._create_toggle_pill(
            icon="󰝟" if self.audio_state["muted"] else "󰕾",
            title="Audio Out",
            status="Muted" if self.audio_state["muted"] else f"{self.audio_state['volume']}%",
            is_active=not self.audio_state["muted"]
        )
        self.mute_btn.connect("clicked", self._on_toggle_mute)
        grid.attach(self.mute_btn, 0, 1, 1, 1)

        # Mic Mute Pill
        self.mic_btn, self.mic_icon, self.mic_sub = self._create_toggle_pill(
            icon="󰍭" if self.audio_state["mic_muted"] else "󰍬",
            title="Microphone",
            status="Muted" if self.audio_state["mic_muted"] else "Active",
            is_active=not self.audio_state["mic_muted"]
        )
        self.mic_btn.connect("clicked", self._on_toggle_mic)
        grid.attach(self.mic_btn, 1, 1, 1, 1)

        # DND Pill
        self.dnd_btn, self.dnd_icon, self.dnd_sub = self._create_toggle_pill(
            icon="󱤓",
            title="Do Not Disturb",
            status="Active" if self.dnd_state else "Off",
            is_active=self.dnd_state
        )
        self.dnd_btn.connect("clicked", self._on_toggle_dnd)
        grid.attach(self.dnd_btn, 0, 2, 1, 1)

        # Wallpaper / Theme Pill
        self.wall_btn, _, _ = self._create_toggle_pill(
            icon="󰸉",
            title="Appearance",
            status="Customize",
            is_active=False,
            has_chevron=True
        )
        self.wall_btn.connect("clicked", self._on_open_wallpaper_settings)
        grid.attach(self.wall_btn, 1, 2, 1, 1)

        main_box.pack_start(grid, False, False, 0)
        main_box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)

        # 3. Interactive Volume & Brightness Slider Card
        slider_card = Gtk.EventBox()
        slider_card_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        slider_card_box.get_style_context().add_class("slider-card")
        slider_card.add(slider_card_box)

        # Volume Row
        vol_hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        vol_title = Gtk.Label(label="󰕾 Master Volume", xalign=0)
        vol_title.get_style_context().add_class("slider-label")
        vol_hdr.pack_start(vol_title, True, True, 0)

        self.vol_val_lbl = Gtk.Label(label=f"{self.audio_state['volume']}%", xalign=1)
        self.vol_val_lbl.get_style_context().add_class("slider-value")
        vol_hdr.pack_end(self.vol_val_lbl, False, False, 0)
        slider_card_box.pack_start(vol_hdr, False, False, 0)

        self.vol_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0, 100, 1)
        self.vol_scale.set_value(self.audio_state["volume"])
        self.vol_scale.set_draw_value(False)
        self.vol_scale.connect("value-changed", self._on_scale_volume_changed)
        slider_card_box.pack_start(self.vol_scale, False, False, 0)

        # Brightness Row
        bri_hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        bri_title = Gtk.Label(label="󰃠 Brightness", xalign=0)
        bri_title.get_style_context().add_class("slider-label")
        bri_hdr.pack_start(bri_title, True, True, 0)

        self.bri_val_lbl = Gtk.Label(label=f"{self.brightness}%", xalign=1)
        self.bri_val_lbl.get_style_context().add_class("slider-value")
        bri_hdr.pack_end(self.bri_val_lbl, False, False, 0)
        slider_card_box.pack_start(bri_hdr, False, False, 0)

        self.bri_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 10, 100, 1)
        self.bri_scale.set_value(self.brightness)
        self.bri_scale.set_draw_value(False)
        self.bri_scale.connect("value-changed", self._on_scale_brightness_changed)
        slider_card_box.pack_start(self.bri_scale, False, False, 0)

        # Sink device switcher button
        sink_short = self.audio_state["sink_desc"]
        if len(sink_short) > 28:
            sink_short = sink_short[:25] + "..."
        self.sink_btn = Gtk.Button(label=f"󰓃 Device: {sink_short}")
        self.sink_btn.get_style_context().add_class("device-btn")
        lbl = self.sink_btn.get_child()
        if isinstance(lbl, Gtk.Label):
            lbl.set_ellipsize(Pango.EllipsizeMode.END)
            lbl.set_max_width_chars(26)
        self.sink_btn.connect("clicked", self._on_switch_output_device)
        slider_card_box.pack_start(self.sink_btn, False, False, 0)

        slider_card.connect("scroll-event", self._on_scroll_volume)
        main_box.pack_start(slider_card, False, False, 0)

        # Media Player Card (Visible only when playing/paused)
        if self.media_info.get("active"):
            media_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            media_card.get_style_context().add_class("media-card")

            media_top = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
            media_icon = Gtk.Label(label="󰝚")
            media_icon.get_style_context().add_class("media-icon")
            player_name = self.media_info.get("player", "Media")
            media_player_lbl = Gtk.Label(label=player_name, xalign=0)
            media_player_lbl.get_style_context().add_class("media-player-name")
            media_top.pack_start(media_icon, False, False, 0)
            media_top.pack_start(media_player_lbl, True, True, 0)
            media_card.pack_start(media_top, False, False, 0)

            title_str = f"{self.media_info.get('title', 'Unknown')} - {self.media_info.get('artist', 'Unknown')}"
            media_title = Gtk.Label(label=title_str, xalign=0)
            media_title.get_style_context().add_class("media-track-title")
            media_title.set_ellipsize(Pango.EllipsizeMode.END)
            media_title.set_max_width_chars(32)
            media_card.pack_start(media_title, False, False, 0)

            ctrl_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            ctrl_box.set_halign(Gtk.Align.CENTER)
            prev_btn = Gtk.Button(label="󰒮")
            prev_btn.get_style_context().add_class("media-btn")
            prev_btn.connect("clicked", lambda b: self._run_media("previous"))

            play_icon = "󰏤" if self.media_info.get("status") == "Playing" else "󰐊"
            self.play_btn = Gtk.Button(label=play_icon)
            self.play_btn.get_style_context().add_class("media-btn")
            self.play_btn.connect("clicked", self._on_toggle_play)

            next_btn = Gtk.Button(label="󰒭")
            next_btn.get_style_context().add_class("media-btn")
            next_btn.connect("clicked", lambda b: self._run_media("next"))

            ctrl_box.pack_start(prev_btn, False, False, 0)
            ctrl_box.pack_start(self.play_btn, False, False, 0)
            ctrl_box.pack_start(next_btn, False, False, 0)
            media_card.pack_start(ctrl_box, False, False, 0)

            main_box.pack_start(media_card, False, False, 0)

        # 4. Hardware Telemetry Card (Clickable to launch btop)
        hw_card = Gtk.EventBox()
        hw_card_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        hw_card_box.get_style_context().add_class("hardware-card")
        hw_card.add(hw_card_box)

        hw_hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        hw_title = Gtk.Label(label="󰍛 HARDWARE TELEMETRY", xalign=0)
        hw_title.get_style_context().add_class("section-title")
        hw_hdr.pack_start(hw_title, True, True, 0)

        hw_hint = Gtk.Label(label="Click: btop 󰓅", xalign=1)
        hw_hint.get_style_context().add_class("hw-value")
        hw_hdr.pack_end(hw_hint, False, False, 0)
        hw_card_box.pack_start(hw_hdr, False, False, 0)

        # CPU bar
        cpu_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        cpu_pct = get_cpu_info()
        cpu_lbl = Gtk.Label(label="CPU Load", xalign=0)
        cpu_lbl.get_style_context().add_class("hw-label")
        self.cpu_val = Gtk.Label(label=f"{cpu_pct}%", xalign=1)
        self.cpu_val.get_style_context().add_class("hw-value")
        cpu_box.pack_start(cpu_lbl, True, True, 0)
        cpu_box.pack_end(self.cpu_val, False, False, 0)
        hw_card_box.pack_start(cpu_box, False, False, 0)

        self.cpu_bar = Gtk.ProgressBar()
        self.cpu_bar.set_fraction(cpu_pct / 100.0)
        hw_card_box.pack_start(self.cpu_bar, False, False, 0)

        # RAM bar
        mem = get_memory_info()
        ram_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        ram_lbl = Gtk.Label(label="Memory (RAM)", xalign=0)
        ram_lbl.get_style_context().add_class("hw-label")
        self.ram_val = Gtk.Label(label=f"{mem['used_gb']:.1f} / {mem['total_gb']:.1f} GB ({mem['pct']}%)", xalign=1)
        self.ram_val.get_style_context().add_class("hw-value")
        ram_box.pack_start(ram_lbl, True, True, 0)
        ram_box.pack_end(self.ram_val, False, False, 0)
        hw_card_box.pack_start(ram_box, False, False, 0)

        self.ram_bar = Gtk.ProgressBar()
        self.ram_bar.set_fraction(mem['pct'] / 100.0)
        hw_card_box.pack_start(self.ram_bar, False, False, 0)

        hw_card.connect("button-press-event", self._on_launch_btop)
        main_box.pack_start(hw_card, False, False, 0)

        # 5. Session Actions (Bottom Row: Lock, Suspend, Reboot, Shutdown)
        power_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        power_box.get_style_context().add_class("power-bar")
        power_box.set_homogeneous(True)

        lock_btn = Gtk.Button(label="󰌾")
        lock_btn.set_tooltip_text("Lock session (Super+Ctrl+L)")
        lock_btn.get_style_context().add_class("power-btn")
        lock_btn.connect("clicked", lambda b: self._run_action(["~/.config/i3/lock.sh"]))
        power_box.pack_start(lock_btn, True, True, 0)

        sleep_btn = Gtk.Button(label="󰤄")
        sleep_btn.set_tooltip_text("Suspend system")
        sleep_btn.get_style_context().add_class("power-btn")
        sleep_btn.connect("clicked", lambda b: self._run_action(["systemctl", "suspend"]))
        power_box.pack_start(sleep_btn, True, True, 0)

        reboot_btn = Gtk.Button(label="󰑓")
        reboot_btn.set_tooltip_text("Reboot computer")
        reboot_btn.get_style_context().add_class("power-btn")
        reboot_btn.connect("clicked", lambda b: self._run_action(["systemctl", "reboot"]))
        power_box.pack_start(reboot_btn, True, True, 0)

        poweroff_btn = Gtk.Button(label="󰐥")
        poweroff_btn.set_tooltip_text("Shutdown computer")
        poweroff_btn.get_style_context().add_class("power-btn")
        poweroff_btn.get_style_context().add_class("danger")
        poweroff_btn.connect("clicked", lambda b: self._run_action(["systemctl", "poweroff"]))
        power_box.pack_start(poweroff_btn, True, True, 0)

        main_box.pack_start(power_box, False, False, 0)

    def _create_toggle_pill(self, icon, title, status, is_active, has_chevron=False):
        btn = Gtk.Button()
        btn.get_style_context().add_class("toggle-pill")
        if is_active:
            btn.get_style_context().add_class("active")

        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        btn.add(box)

        icon_lbl = Gtk.Label(label=icon)
        icon_lbl.get_style_context().add_class("pill-icon")
        box.pack_start(icon_lbl, False, False, 0)

        txt_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        title_lbl = Gtk.Label(label=title, xalign=0)
        title_lbl.get_style_context().add_class("pill-title")

        # Trim long status
        display_status = status
        if len(display_status) > 14:
            display_status = display_status[:12] + "..."
        status_lbl = Gtk.Label(label=display_status, xalign=0)
        status_lbl.get_style_context().add_class("pill-status")

        txt_box.pack_start(title_lbl, False, False, 0)
        txt_box.pack_start(status_lbl, False, False, 0)
        box.pack_start(txt_box, True, True, 0)

        if has_chevron:
            chev = Gtk.Label(label="󰅂")
            chev.get_style_context().add_class("pill-chevron")
            box.pack_end(chev, False, False, 0)

        return btn, icon_lbl, status_lbl

    # --------------------------------------------------------------------------
    # Callbacks & Actions
    # --------------------------------------------------------------------------

    def _on_open_settings(self, btn):
        self.destroy()
        cmd = ["python3", os.path.expanduser("~/.config/desktop-settings/desktop_settings.py")]
        subprocess.Popen(cmd, start_new_session=True)

    def _open_settings_page(self, page_name, fallback_cmd=None):
        self.destroy()
        settings_script = os.path.expanduser("~/.config/desktop-settings/desktop_settings.py")
        if os.path.exists(settings_script):
            subprocess.Popen(["python3", settings_script, "--page", page_name], start_new_session=True)
        elif fallback_cmd:
            subprocess.Popen(fallback_cmd, start_new_session=True)

    def _on_wifi_right_click(self, btn, event):
        if event.button == 3: # Right click
            self._open_settings_page("wifi", ["alacritty", "--class", "FloatingWifi", "-e", "nmtui"])
            return True
        return False

    def _on_bt_right_click(self, btn, event):
        if event.button == 3: # Right click
            self._open_settings_page("bluetooth", ["alacritty", "--class", "FloatingBluetooth", "-e", "bluetoothctl"])
            return True
        return False

    def _on_open_wallpaper_settings(self, btn):
        self._open_settings_page("appearance", [
            "feh", "-t", "-E", "180", "-y", "140", "-W", "1080", "-H", "720",
            "--title", "Wallpaper Gallery - Click to Apply",
            "--action", os.path.expanduser("~/.config/theme/apply-theme.sh '%f'"),
            os.path.expanduser("~/Pictures/Wallpapers")
        ])

    def _on_toggle_wifi(self, btn):
        curr = self.wifi_state["enabled"]
        new_state = not curr
        self.wifi_state["enabled"] = new_state
        # Instant optimistic UI feedback
        if new_state:
            self.wifi_btn.get_style_context().add_class("active")
            self.wifi_icon.set_text("󰤨")
            self.wifi_sub.set_text("Connecting...")
        else:
            self.wifi_btn.get_style_context().remove_class("active")
            self.wifi_icon.set_text("󰤮")
            self.wifi_sub.set_text("Disconnected")

        def _worker():
            subprocess.run(["nmcli", "radio", "wifi", "on" if new_state else "off"], check=False)
            st = get_wifi_state()
            def _apply():
                self.wifi_state = st
                if st["enabled"]:
                    self.wifi_btn.get_style_context().add_class("active")
                    self.wifi_icon.set_text("󰤨")
                else:
                    self.wifi_btn.get_style_context().remove_class("active")
                    self.wifi_icon.set_text("󰤮")
                self.wifi_sub.set_text(st["ssid"])
                return False
            GLib.idle_add(_apply)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_toggle_bt(self, btn):
        curr = self.bt_state["powered"]
        new_state = not curr
        self.bt_state["powered"] = new_state
        # Instant optimistic UI feedback
        if new_state:
            self.bt_btn.get_style_context().add_class("active")
            self.bt_icon.set_text("󰂯")
            self.bt_sub.set_text("Active")
        else:
            self.bt_btn.get_style_context().remove_class("active")
            self.bt_icon.set_text("󰂲")
            self.bt_sub.set_text("Off")

        def _worker():
            if new_state:
                subprocess.run(["rfkill", "unblock", "bluetooth"], check=False)
                for _ in range(6):
                    time.sleep(0.15)
                    try:
                        out = subprocess.check_output(["bluetoothctl", "show"], text=True, stderr=subprocess.DEVNULL)
                        if "Powered: yes" in out:
                            break
                    except Exception:
                        pass
                    subprocess.run(["bluetoothctl", "power", "on"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                subprocess.run(["bluetoothctl", "power", "off"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(["rfkill", "block", "bluetooth"], check=False)
                for _ in range(4):
                    time.sleep(0.1)
                    try:
                        out = subprocess.check_output(["bluetoothctl", "show"], text=True, stderr=subprocess.DEVNULL)
                        if "Powered: yes" not in out:
                            break
                    except Exception:
                        pass

            st = get_bluetooth_state()
            def _apply():
                self.bt_state = st
                if st["powered"]:
                    self.bt_btn.get_style_context().add_class("active")
                    self.bt_icon.set_text("󰂯")
                else:
                    self.bt_btn.get_style_context().remove_class("active")
                    self.bt_icon.set_text("󰂲")
                self.bt_sub.set_text(st["device"])
                return False
            GLib.idle_add(_apply)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_toggle_mute(self, btn):
        curr_muted = self.audio_state["muted"]
        new_muted = not curr_muted
        self.audio_state["muted"] = new_muted
        # Instant optimistic feedback
        if new_muted:
            self.mute_btn.get_style_context().remove_class("active")
            self.mute_icon.set_text("󰝟")
            self.mute_sub.set_text("Muted")
        else:
            self.mute_btn.get_style_context().add_class("active")
            self.mute_icon.set_text("󰕾")
            self.mute_sub.set_text(f"{self.audio_state['volume']}%")

        def _worker():
            subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"], check=False)
            st = get_audio_state()
            def _apply():
                self.audio_state = st
                if st["muted"]:
                    self.mute_btn.get_style_context().remove_class("active")
                    self.mute_icon.set_text("󰝟")
                    self.mute_sub.set_text("Muted")
                else:
                    self.mute_btn.get_style_context().add_class("active")
                    self.mute_icon.set_text("󰕾")
                    self.mute_sub.set_text(f"{st['volume']}%")
                return False
            GLib.idle_add(_apply)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_toggle_mic(self, btn):
        curr_muted = self.audio_state["mic_muted"]
        new_muted = not curr_muted
        self.audio_state["mic_muted"] = new_muted
        # Instant optimistic feedback
        if new_muted:
            self.mic_btn.get_style_context().remove_class("active")
            self.mic_icon.set_text("󰍭")
            self.mic_sub.set_text("Muted")
        else:
            self.mic_btn.get_style_context().add_class("active")
            self.mic_icon.set_text("󰍬")
            self.mic_sub.set_text("Active")

        def _worker():
            subprocess.run(["pactl", "set-source-mute", "@DEFAULT_SOURCE@", "toggle"], check=False)
            st = get_audio_state()
            def _apply():
                self.audio_state = st
                if st["mic_muted"]:
                    self.mic_btn.get_style_context().remove_class("active")
                    self.mic_icon.set_text("󰍭")
                    self.mic_sub.set_text("Muted")
                else:
                    self.mic_btn.get_style_context().add_class("active")
                    self.mic_icon.set_text("󰍬")
                    self.mic_sub.set_text("Active")
                return False
            GLib.idle_add(_apply)

        threading.Thread(target=_worker, daemon=True).start()

    def _on_toggle_dnd(self, btn):
        curr = self.dnd_state
        new_state = not curr
        self.dnd_state = new_state
        # Instant optimistic feedback
        if new_state:
            self.dnd_btn.get_style_context().add_class("active")
            self.dnd_sub.set_text("Active")
        else:
            self.dnd_btn.get_style_context().remove_class("active")
            self.dnd_sub.set_text("Off")

        def _worker():
            subprocess.run(["dunstctl", "set-paused", "toggle"], check=False)
            st = get_dnd_state()
            def _apply():
                self.dnd_state = st
                if st:
                    self.dnd_btn.get_style_context().add_class("active")
                    self.dnd_sub.set_text("Active")
                else:
                    self.dnd_btn.get_style_context().remove_class("active")
                    self.dnd_sub.set_text("Off")
                return False
            GLib.idle_add(_apply)

        threading.Thread(target=_worker, daemon=True).start()



    def _on_scroll_volume(self, widget, event):
        curr = int(round(self.vol_scale.get_value()))
        if event.direction == Gdk.ScrollDirection.UP:
            new_val = min(100, curr + 5)
        elif event.direction == Gdk.ScrollDirection.DOWN:
            new_val = max(0, curr - 5)
        elif event.direction == Gdk.ScrollDirection.SMOOTH:
            _, _, dy = event.get_scroll_deltas()
            new_val = min(100, curr + 5) if dy < 0 else max(0, curr - 5)
        else:
            return False
        self.vol_scale.set_value(new_val)
        return True

    def _on_scale_volume_changed(self, scale):
        val = int(round(scale.get_value()))
        self.vol_val_lbl.set_text(f"{val}%")
        subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{val}%"], check=False)
        # If unmuted now, update pill
        if self.audio_state["muted"]:
            subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"], check=False)
            self.mute_btn.get_style_context().add_class("active")
            self.mute_icon.set_text("󰕾")
        self.mute_sub.set_text(f"{val}%")

    def _on_scale_brightness_changed(self, scale):
        val = int(round(scale.get_value()))
        self.bri_val_lbl.set_text(f"{val}%")
        set_brightness(val)

    def _run_media(self, action):
        subprocess.run(["playerctl", action], check=False)
        time.sleep(0.1)
        self._refresh_media()

    def _on_toggle_play(self, btn):
        subprocess.run(["playerctl", "play-pause"], check=False)
        time.sleep(0.1)
        self._refresh_media()

    def _refresh_media(self):
        self.media_info = get_media_info()
        if hasattr(self, 'play_btn'):
            play_icon = "󰏤" if self.media_info.get("status") == "Playing" else "󰐊"
            self.play_btn.set_label(play_icon)

    def _on_switch_output_device(self, btn):
        # Cycle through sinks
        try:
            out = subprocess.check_output(["pactl", "list", "short", "sinks"], text=True, stderr=subprocess.DEVNULL)
            sinks = [line.split()[1] for line in out.strip().splitlines() if line]
            if len(sinks) > 1:
                cur_out = subprocess.check_output(["pactl", "get-default-sink"], text=True, stderr=subprocess.DEVNULL).strip()
                try:
                    idx = sinks.index(cur_out)
                    nxt = sinks[(idx + 1) % len(sinks)]
                except ValueError:
                    nxt = sinks[0]
                subprocess.run(["pactl", "set-default-sink", nxt], check=False)
                # Move active inputs
                inputs_out = subprocess.check_output(["pactl", "list", "short", "sink-inputs"], text=True, stderr=subprocess.DEVNULL)
                for line in inputs_out.strip().splitlines():
                    if line:
                        inp_id = line.split()[0]
                        subprocess.run(["pactl", "move-sink-input", inp_id, nxt], check=False)
                time.sleep(0.1)
                self.audio_state = get_audio_state()
                desc = self.audio_state["sink_desc"]
                if len(desc) > 28:
                    desc = desc[:25] + "..."
                self.sink_btn.set_label(f"󰓃 Device: {desc}")
                lbl = self.sink_btn.get_child()
                if isinstance(lbl, Gtk.Label):
                    lbl.set_ellipsize(Pango.EllipsizeMode.END)
                    lbl.set_max_width_chars(26)
        except Exception:
            pass

    def _on_launch_btop(self, box, event):
        self.destroy()
        subprocess.Popen(["alacritty", "--class", "FloatingBtop", "-e", "btop"])

    def _run_action(self, cmd):
        self.destroy()
        # Expand user in cmd
        expanded = [os.path.expanduser(c) for c in cmd]
        subprocess.Popen(expanded)

    def _on_key_press(self, widget, event):
        if event.keyval == Gdk.KEY_Escape:
            self.destroy()
            return True
        return False

    def _on_focus_out(self, widget, event):
        return False

    def _update_hw_stats(self):
        cpu_pct = get_cpu_info()
        mem = get_memory_info()
        if hasattr(self, 'cpu_val') and hasattr(self, 'cpu_bar'):
            self.cpu_val.set_text(f"{cpu_pct}%")
            self.cpu_bar.set_fraction(cpu_pct / 100.0)
        if hasattr(self, 'ram_val') and hasattr(self, 'ram_bar'):
            self.ram_val.set_text(f"{mem['used_gb']:.1f} / {mem['total_gb']:.1f} GB ({mem['pct']}%)")
            self.ram_bar.set_fraction(mem['pct'] / 100.0)
        return True

# ------------------------------------------------------------------------------
# Entry Point & Dynamic Placement
# ------------------------------------------------------------------------------

def calculate_target_position(win, inset=10):
    """
    Dynamically calculate (x, y) coordinates for the control center so that:
    1. It anchors under Polybar on the active workspace.
    2. It aligns inside the active/top-right open window.
    3. The inset from the window's top border EQUALS the inset from the window's right border.
    4. NO hardcoded screen resolutions, widths, or fixed gaps are used.
    """
    target_top = None
    target_right = None

    try:
        tree = json.loads(subprocess.check_output(['i3-msg', '-t', 'get_tree'], stderr=subprocess.DEVNULL))
        workspaces = json.loads(subprocess.check_output(['i3-msg', '-t', 'get_workspaces'], stderr=subprocess.DEVNULL))

        focused_ws = next((w for w in workspaces if w.get('focused')), None)
        if not focused_ws:
            focused_ws = next((w for w in workspaces if w.get('visible')), None)

        ws_name = focused_ws.get('name') if focused_ws else None
        ws_rect = focused_ws.get('rect') if focused_ws else None

        def find_ws_node(node, name):
            if node.get('type') == 'workspace' and node.get('name') == name:
                return node
            for child in node.get('nodes', []) + node.get('floating_nodes', []):
                res = find_ws_node(child, name)
                if res:
                    return res
            return None

        ws_node = find_ws_node(tree, ws_name) if ws_name else None

        def collect_windows(node):
            wins = []
            if node.get('window') and node.get('window_properties'):
                cls = node.get('window_properties', {}).get('class', '')
                if cls.lower() not in ('polybar', 'controlcenter', 'control_center'):
                    wins.append(node)
            for child in node.get('nodes', []) + node.get('floating_nodes', []):
                wins.extend(collect_windows(child))
            return wins

        open_wins = collect_windows(ws_node) if ws_node else []

        if open_wins:
            # Find the top-rightmost window:
            # Sort by: (x + width) descending, then y ascending
            top_right_win = sorted(
                open_wins,
                key=lambda w: (w['rect']['x'] + w['rect']['width'], -w['rect']['y']),
                reverse=True
            )[0]
            rect = top_right_win['rect']
            target_top = rect['y']
            target_right = rect['x'] + rect['width']
        elif ws_rect:
            target_top = ws_rect['y']
            target_right = ws_rect['x'] + ws_rect['width']
    except Exception:
        pass

    # GDK Fallback if i3 query didn't return values
    if target_top is None or target_right is None:
        display = Gdk.Display.get_default()
        monitor = display.get_primary_monitor() or display.get_monitor(0)
        geom = monitor.get_geometry()
        target_top = geom.y + 40
        target_right = geom.x + geom.width - 7

    min_w, nat_w = win.get_preferred_width()
    alloc = win.get_allocation()
    win_w, _ = win.get_size()
    panel_width = max(win_w, min_w, nat_w, alloc.width)
    if panel_width <= 1:
        panel_width = 390

    x = int(target_right - panel_width - inset)
    y = int(target_top + inset)

    return x, y


def main():
    try:
        os.makedirs(os.path.dirname(PID_FILE), exist_ok=True)
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))
    except Exception:
        pass

    win = ControlCenterWindow()
    x, y = calculate_target_position(win, inset=10)

    win.move(x, y)
    win.show_all()
    win.set_keep_above(True)

    subprocess.run([
        "i3-msg",
        f'[class="(?i)control_center.*|ControlCenter"] border none, move position {x} {y}'
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, lambda: (win.destroy(), GLib.SOURCE_REMOVE)[1])

    Gtk.main()


if __name__ == "__main__":
    main()
