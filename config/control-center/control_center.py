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


def get_quickshare_state():
    is_running = False
    try:
        res = subprocess.run(["pgrep", "-f", "rquickshare"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        is_running = (res.returncode == 0)
    except Exception:
        pass
    return {
        "running": is_running,
        "status": "Active" if is_running else "Off"
    }


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


def get_notifications():
    notifications = []
    try:
        out = subprocess.check_output(["dunstctl", "history"], text=True, stderr=subprocess.DEVNULL)
        data = json.loads(out).get("data", [[]])[0]

        try:
            with open("/proc/uptime", "r") as f:
                uptime = float(f.read().split()[0])
        except Exception:
            uptime = time.time()

        for item in data:
            nid = item.get("id", {}).get("data", 0)
            app = item.get("appname", {}).get("data", "").strip()
            summary = item.get("summary", {}).get("data", "").strip()
            body = item.get("body", {}).get("data", "").strip()
            icon_path = item.get("icon_path", {}).get("data", "").strip()
            ts = item.get("timestamp", {}).get("data", 0)

            secs_ago = max(0, uptime - (ts / 1e6))
            if secs_ago < 60:
                time_str = "Just now"
            elif secs_ago < 3600:
                time_str = f"{int(secs_ago // 60)}m ago"
            elif secs_ago < 86400:
                time_str = f"{int(secs_ago // 3600)}h ago"
            else:
                time_str = f"{int(secs_ago // 86400)}d ago"

            clean_body = " ".join(body.split())
            if not app:
                if "zen" in icon_path.lower() or "navigator" in icon_path.lower() or "ticket" in summary.lower() or "http" in body.lower():
                    app = "Zen Browser"
                elif "discord" in icon_path.lower():
                    app = "Discord"
                elif "spotify" in icon_path.lower():
                    app = "Spotify"
                else:
                    app = "System"

            notifications.append({
                "id": nid,
                "app": app,
                "summary": summary,
                "body": clean_body,
                "icon_path": icon_path,
                "time_str": time_str
            })
    except Exception:
        pass
    return notifications


def get_app_icon(app_name, summary="", body=""):
    a = (app_name or "").lower()
    text = (summary + " " + body).lower()
    if "screenshot" in a or "screenshot" in text:
        return "󰹑"
    elif "zen" in a or "browser" in a or "firefox" in a:
        return "󰈹"
    elif "discord" in a or "webcord" in a or "vesktop" in a:
        return "󰙯"
    elif "spotify" in a or "music" in a:
        return "󰓇"
    elif "quick" in a or "share" in a:
        return "󰒗"
    elif "alacritty" in a or "term" in a or "kitty" in a:
        return "󰆍"
    elif "telegram" in a:
        return "󰀨"
    elif "slack" in a:
        return "󰒱"
    elif "mail" in a or "thunderbird" in a or "ticket" in text:
        return "󰇮"
    elif "messaggio" in text or "whatsapp" in text or "chat" in text:
        return "󰭹"
    elif "wifi" in a or "network" in a:
        return "󰤨"
    elif "bluetooth" in a:
        return "󰂯"
    else:
        return "󰂚"


def focus_notification_target(app_name, summary="", body=""):
    app = (app_name or "").strip().lower()
    summary_lower = (summary or "").lower()
    body_lower = (body or "").lower()

    try:
        tree = json.loads(subprocess.check_output(["i3-msg", "-t", "get_tree"], text=True, stderr=subprocess.DEVNULL))
        def collect_windows(node):
            wins = []
            if node.get("window") and node.get("window_properties"):
                cls = (node.get("window_properties", {}).get("class") or "").lower()
                inst = (node.get("window_properties", {}).get("instance") or "").lower()
                title = (node.get("name") or "").lower()
                wins.append({"con_id": node["id"], "class": cls, "instance": inst, "title": title})
            for c in node.get("nodes", []) + node.get("floating_nodes", []):
                wins.extend(collect_windows(c))
            return wins

        windows = collect_windows(tree)
        target_id = None

        aliases = {
            "zen browser": "zen",
            "browser": "zen",
            "firefox": "zen",
            "google-chrome": "chrome",
            "discord": "discord",
            "telegram": "telegramdesktop",
            "terminal": "alacritty",
            "code": "code",
            "quick share": "rquickshare",
            "quickshare": "rquickshare",
            "rquickshare": "rquickshare",
        }
        search_terms = [app]
        if app in aliases:
            search_terms.append(aliases[app])

        for term in search_terms:
            if not term:
                continue
            for w in windows:
                if term in w["class"] or term in w["instance"] or term in w["title"]:
                    target_id = w["con_id"]
                    break
            if target_id:
                break

        if not target_id:
            words = [wrd for wrd in (summary_lower + " " + body_lower).split() if len(wrd) > 3]
            for wrd in words:
                for w in windows:
                    if wrd in w["title"] or wrd in w["class"]:
                        target_id = w["con_id"]
                        break
                if target_id:
                    break

        if not target_id and ("ticket" in summary_lower or "http" in body_lower or "zen" in app):
            for w in windows:
                if "zen" in w["class"] or "navigator" in w["instance"]:
                    target_id = w["con_id"]
                    break

        if target_id:
            subprocess.run(["i3-msg", f"[con_id=\"{target_id}\"] focus"], check=False)
            return True

        if "zen" in app or "browser" in app:
            subprocess.Popen(["flatpak", "run", "app.zen_browser.zen"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif "quick" in app:
            subprocess.Popen([os.path.expanduser("~/Applications/rquickshare")], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif app and app not in ("system", "notification"):
            subprocess.Popen([app], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except Exception:
        return False


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
        self.set_default_size(416, -1)
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
        self.quickshare_state = get_quickshare_state()
        self.media_info = get_media_info()
        self.notifications = get_notifications()

        # Focus settling flag
        self._settled = False

        self._build_ui()
        self._apply_css()

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
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        main_box.get_style_context().add_class("main-box")
        self.add(main_box)

        # 1. Header (User & Hostname & Settings)
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        header_box.get_style_context().add_class("header-box")

        user = os.environ.get("USER", "user")
        hostname = "borch"
        try:
            with open("/etc/hostname", "r") as f:
                hostname = f.read().strip()
        except Exception:
            pass

        user_lbl = Gtk.Label(label=f"{user}@{hostname}", xalign=0)
        user_lbl.get_style_context().add_class("header-user")
        user_lbl.set_valign(Gtk.Align.CENTER)
        header_box.pack_start(user_lbl, True, True, 0)

        # Settings App button (opens desktop-settings)
        settings_btn = Gtk.Button(label="󰒓")
        settings_btn.get_style_context().add_class("settings-btn")
        settings_btn.set_tooltip_text("Open Settings")
        settings_btn.set_valign(Gtk.Align.CENTER)
        settings_btn.connect("clicked", self._on_open_settings)
        header_box.pack_end(settings_btn, False, False, 0)

        main_box.pack_start(header_box, False, False, 0)
        main_box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)

        # 2. Quick Toggles Grid (Wi-Fi, Bluetooth, Mute, Mic, DND, Quick Share)
        grid = Gtk.Grid()
        grid.set_column_spacing(8)
        grid.set_row_spacing(8)
        grid.set_column_homogeneous(True)

        # Wi-Fi Pill
        self.wifi_btn, self.wifi_icon, self.wifi_sub, self.wifi_chev = self._create_toggle_pill(
            icon="󰤨" if self.wifi_state["enabled"] else "󰤮",
            title="Wi-Fi",
            status=self.wifi_state["ssid"],
            is_active=self.wifi_state["enabled"],
            has_chevron=True,
            on_toggle=self._on_toggle_wifi,
            on_chevron=self._on_wifi_chevron
        )
        self.wifi_btn.connect("button-press-event", self._on_wifi_right_click)
        grid.attach(self.wifi_btn, 0, 0, 1, 1)

        # Bluetooth Pill
        self.bt_btn, self.bt_icon, self.bt_sub, self.bt_chev = self._create_toggle_pill(
            icon="󰂯" if self.bt_state["powered"] else "󰂲",
            title="Bluetooth",
            status=self.bt_state["device"],
            is_active=self.bt_state["powered"],
            has_chevron=True,
            on_toggle=self._on_toggle_bt,
            on_chevron=self._on_bt_chevron
        )
        self.bt_btn.connect("button-press-event", self._on_bt_right_click)
        grid.attach(self.bt_btn, 1, 0, 1, 1)

        # Audio Mute Pill
        self.mute_btn, self.mute_icon, self.mute_sub, _ = self._create_toggle_pill(
            icon="󰝟" if self.audio_state["muted"] else "󰕾",
            title="Audio Out",
            status="Muted" if self.audio_state["muted"] else f"{self.audio_state['volume']}%",
            is_active=not self.audio_state["muted"],
            has_chevron=False,
            on_toggle=self._on_toggle_mute
        )
        grid.attach(self.mute_btn, 0, 1, 1, 1)

        # Mic Mute Pill
        self.mic_btn, self.mic_icon, self.mic_sub, _ = self._create_toggle_pill(
            icon="󰍭" if self.audio_state["mic_muted"] else "󰍬",
            title="Microphone",
            status="Muted" if self.audio_state["mic_muted"] else "Active",
            is_active=not self.audio_state["mic_muted"],
            has_chevron=False,
            on_toggle=self._on_toggle_mic
        )
        grid.attach(self.mic_btn, 1, 1, 1, 1)

        # DND Pill
        self.dnd_btn, self.dnd_icon, self.dnd_sub, _ = self._create_toggle_pill(
            icon="󱤓",
            title="Do Not Disturb",
            status="Active" if self.dnd_state else "Off",
            is_active=self.dnd_state,
            has_chevron=False,
            on_toggle=self._on_toggle_dnd
        )
        grid.attach(self.dnd_btn, 0, 2, 1, 1)

        # Quick Share Pill
        self.qs_btn, self.qs_icon, self.qs_sub, self.qs_chev = self._create_toggle_pill(
            icon="󰒗",
            title="Quick Share",
            status=self.quickshare_state["status"],
            is_active=self.quickshare_state["running"],
            has_chevron=True,
            on_toggle=self._on_toggle_quickshare,
            on_chevron=self._on_quickshare_chevron
        )
        grid.attach(self.qs_btn, 1, 2, 1, 1)

        main_box.pack_start(grid, False, False, 0)
        main_box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)

        # 3. Notifications Section
        notif_section = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        notif_section.get_style_context().add_class("notifications-section")

        self.notif_hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.notif_hdr.get_style_context().add_class("notif-header-bar")
        self.notif_hdr.set_no_show_all(True)

        self.notif_clear_btn = Gtk.Button(label="Clear")
        self.notif_clear_btn.get_style_context().add_class("notif-clear-btn")
        self.notif_clear_btn.set_tooltip_text("Clear all notifications")
        self.notif_clear_btn.connect("clicked", self._on_clear_all_notifications)
        self.notif_hdr.pack_end(self.notif_clear_btn, False, False, 0)
        notif_section.pack_start(self.notif_hdr, False, False, 0)

        self.notif_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.notif_scrolled = Gtk.ScrolledWindow()
        self.notif_scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.notif_scrolled.set_max_content_height(260)
        self.notif_scrolled.set_propagate_natural_height(True)
        self.notif_scrolled.add(self.notif_list_box)
        notif_section.pack_start(self.notif_scrolled, False, False, 0)

        self._populate_notifications()
        main_box.pack_start(notif_section, False, False, 0)

        # Media Player Card (Visible only when playing/paused)
        if self.media_info.get("active"):
            main_box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)
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

        main_box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 0)

        # 3. Session Actions (Bottom Row: Lock, Suspend, Reboot, Shutdown)
        power_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
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

    def _populate_notifications(self):
        for child in self.notif_list_box.get_children():
            self.notif_list_box.remove(child)

        if not self.notifications:
            self.notif_hdr.set_visible(False)
            empty_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            empty_box.get_style_context().add_class("notif-empty-box")

            empty_icon = Gtk.Label(label="󰂛")
            empty_icon.get_style_context().add_class("notif-empty-icon")
            empty_lbl = Gtk.Label(label="No notifications")
            empty_lbl.get_style_context().add_class("notif-empty-label")

            empty_box.pack_start(empty_icon, False, False, 0)
            empty_box.pack_start(empty_lbl, False, False, 0)
            self.notif_list_box.pack_start(empty_box, False, False, 0)
        else:
            self.notif_hdr.set_visible(True)
            self.notif_clear_btn.set_sensitive(True)
            for notif in self.notifications[:6]:
                card = self._create_notification_card(notif)
                self.notif_list_box.pack_start(card, False, False, 0)

        self.notif_list_box.show_all()

    def _create_notification_card(self, notif):
        event_box = Gtk.EventBox()
        event_box.get_style_context().add_class("notif-card")

        card_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        card_box.set_margin_start(14)
        card_box.set_margin_end(12)
        card_box.set_margin_top(12)
        card_box.set_margin_bottom(12)
        event_box.add(card_box)

        # 1. App Icon (Centrally balanced on the left)
        icon_char = get_app_icon(notif["app"], notif.get("summary", ""), notif.get("body", ""))
        app_icon_lbl = Gtk.Label(label=icon_char)
        app_icon_lbl.get_style_context().add_class("notif-icon")
        app_icon_lbl.set_valign(Gtk.Align.CENTER)
        app_icon_lbl.set_halign(Gtk.Align.CENTER)
        card_box.pack_start(app_icon_lbl, False, False, 0)

        # 2. Content Box (App + Bullet + Time, Title, Body)
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)

        # Header: App name and relative time grouped together
        hdr = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hdr.set_margin_bottom(2)

        display_app = notif["app"]
        if display_app.lower() in ("dunstify", "system"):
            if "screenshot" in notif.get("summary", "").lower():
                display_app = "Screenshot"
            elif "messaggio" in notif.get("body", "").lower():
                display_app = "Messages"
            else:
                display_app = "System"

        app_lbl = Gtk.Label(label=display_app.upper(), xalign=0)
        app_lbl.get_style_context().add_class("notif-app-name")
        hdr.pack_start(app_lbl, False, False, 0)

        dot_lbl = Gtk.Label(label="•")
        dot_lbl.get_style_context().add_class("notif-bullet")
        hdr.pack_start(dot_lbl, False, False, 0)

        time_lbl = Gtk.Label(label=notif["time_str"], xalign=0)
        time_lbl.get_style_context().add_class("notif-time")
        hdr.pack_start(time_lbl, False, False, 0)

        content_box.pack_start(hdr, False, False, 0)

        # Notification Title
        if notif["summary"]:
            title_lbl = Gtk.Label(label=notif["summary"], xalign=0)
            title_lbl.get_style_context().add_class("notif-title")
            title_lbl.set_ellipsize(Pango.EllipsizeMode.END)
            title_lbl.set_max_width_chars(32)
            title_lbl.set_margin_bottom(1)
            content_box.pack_start(title_lbl, False, False, 0)

        # Notification Body
        if notif["body"]:
            body_lbl = Gtk.Label(label=notif["body"], xalign=0)
            body_lbl.get_style_context().add_class("notif-body")
            body_lbl.set_ellipsize(Pango.EllipsizeMode.END)
            body_lbl.set_max_width_chars(36)
            content_box.pack_start(body_lbl, False, False, 0)

        card_box.pack_start(content_box, True, True, 0)

        # 3. Dismiss button (Cleanly aligned top-right)
        close_btn = Gtk.Button(label="󰅖")
        close_btn.get_style_context().add_class("notif-close-btn")
        close_btn.set_valign(Gtk.Align.START)
        close_btn.set_tooltip_text("Dismiss notification")

        def _on_dismiss(btn):
            nid = notif.get("id")
            if nid:
                subprocess.run(["dunstctl", "history-rm", str(nid)], check=False)
            self.notifications = [n for n in self.notifications if n.get("id") != nid]
            self._populate_notifications()

        close_btn.connect("clicked", _on_dismiss)
        card_box.pack_end(close_btn, False, False, 0)

        def _on_card_click(w, event):
            if event.button == 1:
                self.destroy()
                focus_notification_target(notif["app"], notif["summary"], notif["body"])
                return True
            return False

        event_box.connect("button-press-event", _on_card_click)
        return event_box

    def _on_clear_all_notifications(self, btn):
        subprocess.run(["dunstctl", "history-clear"], check=False)
        self.notifications = []
        self._populate_notifications()

    def _create_toggle_pill(self, icon, title, status, is_active, has_chevron=False, on_toggle=None, on_chevron=None):
        pill_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        pill_box.get_style_context().add_class("toggle-pill")
        if is_active:
            pill_box.get_style_context().add_class("active")

        # Main toggle button
        main_btn = Gtk.Button()
        main_btn.get_style_context().add_class("pill-main-btn")
        if has_chevron:
            main_btn.get_style_context().add_class("pill-main-btn-split")
        else:
            main_btn.get_style_context().add_class("pill-main-btn-full")

        if on_toggle:
            main_btn.connect("clicked", on_toggle)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        main_btn.add(btn_box)

        icon_lbl = Gtk.Label(label=icon)
        icon_lbl.get_style_context().add_class("pill-icon")
        btn_box.pack_start(icon_lbl, False, False, 0)

        txt_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=1)
        title_lbl = Gtk.Label(label=title, xalign=0)
        title_lbl.get_style_context().add_class("pill-title")
        title_lbl.set_ellipsize(Pango.EllipsizeMode.END)

        display_status = status
        if len(display_status) > 16:
            display_status = display_status[:14] + "..."
        status_lbl = Gtk.Label(label=display_status, xalign=0)
        status_lbl.get_style_context().add_class("pill-status")
        status_lbl.set_ellipsize(Pango.EllipsizeMode.END)

        txt_box.pack_start(title_lbl, False, False, 0)
        txt_box.pack_start(status_lbl, False, False, 0)
        btn_box.pack_start(txt_box, True, True, 0)

        pill_box.pack_start(main_btn, True, True, 0)

        chev_btn = None
        if has_chevron:
            chev_btn = Gtk.Button()
            chev_btn.get_style_context().add_class("pill-chevron-btn")
            chev_lbl = Gtk.Label(label="󰅂")
            chev_btn.add(chev_lbl)
            if on_chevron:
                chev_btn.connect("clicked", on_chevron)
            pill_box.pack_end(chev_btn, False, False, 0)

        return pill_box, icon_lbl, status_lbl, chev_btn

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

    def _on_wifi_chevron(self, btn):
        self._open_settings_page("wifi", ["alacritty", "--class", "FloatingWifi", "-e", "nmtui"])

    def _on_bt_chevron(self, btn):
        self._open_settings_page("bluetooth", ["alacritty", "--class", "FloatingBluetooth", "-e", "bluetoothctl"])

    def _on_quickshare_chevron(self, btn):
        self.destroy()
        subprocess.Popen(["/home/tonda/Applications/rquickshare"], start_new_session=True)
        time.sleep(0.1)
        subprocess.run(["i3-msg", '[class="(?i)rquickshare"] focus'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

    def _on_toggle_quickshare(self, btn):
        curr = self.quickshare_state["running"]
        new_state = not curr
        self.quickshare_state["running"] = new_state
        if new_state:
            self.qs_btn.get_style_context().add_class("active")
            self.qs_sub.set_text("Active")
        else:
            self.qs_btn.get_style_context().remove_class("active")
            self.qs_sub.set_text("Off")

        def _worker():
            if new_state:
                subprocess.Popen(["/home/tonda/Applications/rquickshare"], start_new_session=True)
            else:
                subprocess.run(["pkill", "-f", "rquickshare"], check=False)
            time.sleep(0.3)
            st = get_quickshare_state()
            def _apply():
                self.quickshare_state = st
                if st["running"]:
                    self.qs_btn.get_style_context().add_class("active")
                    self.qs_sub.set_text("Active")
                else:
                    self.qs_btn.get_style_context().remove_class("active")
                    self.qs_sub.set_text("Off")
                return False
            GLib.idle_add(_apply)

        threading.Thread(target=_worker, daemon=True).start()

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
    win.show_all()
    x, y = calculate_target_position(win, inset=10)
    win.move(x, y)
    win.set_keep_above(True)

    subprocess.run([
        "i3-msg",
        f'[class="(?i)control_center.*|ControlCenter"] border none, move position {x} {y}'
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, lambda: (win.destroy(), GLib.SOURCE_REMOVE)[1])

    Gtk.main()


if __name__ == "__main__":
    main()
