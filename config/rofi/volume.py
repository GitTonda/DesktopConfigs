#!/usr/bin/env python3
"""
Rofi Audio & Volume Dashboard
Catppuccin Mocha minimal terminal-style audio management applet for PipeWire / PulseAudio.
"""

import sys
import os
import subprocess
import shutil
import re


ROFI_THEME = os.path.expanduser("~/.config/rofi/volume.rasi")


def notify(title, message, urgency="normal", value=None):
    cmd = [
        "dunstify", "-a", "Audio Manager",
        "-r", "9966",
        "-u", urgency,
        "-h", "string:x-dunst-stack-tag:audio_status",
    ]
    if value is not None:
        cmd.extend(["-h", f"int:value:{value}"])
    cmd.extend([title, message])

    if shutil.which("dunstify"):
        subprocess.run(cmd, check=False)
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


def make_meter(pct, width=10):
    pct = max(0, min(100, pct))
    filled = int(round((pct / 100.0) * width))
    empty = width - filled
    return "■" * filled + "□" * empty


def get_audio_state():
    try:
        def_sink = subprocess.check_output(["pactl", "get-default-sink"], text=True).strip()
    except Exception:
        def_sink = ""

    try:
        def_source = subprocess.check_output(["pactl", "get-default-source"], text=True).strip()
    except Exception:
        def_source = ""

    # Parse all sinks
    sinks = []
    try:
        sinks_out = subprocess.check_output(["pactl", "list", "sinks"], text=True)
        curr = {}
        for line in sinks_out.splitlines():
            l = line.strip()
            if line.startswith("Sink #"):
                if curr:
                    sinks.append(curr)
                curr = {"id": line.split("#")[1].strip(), "vol": 100, "muted": False}
            elif l.startswith("Name:"):
                curr["name"] = l.split(":", 1)[1].strip()
            elif l.startswith("Description:"):
                curr["desc"] = l.split(":", 1)[1].strip()
            elif l.startswith("Mute:"):
                curr["muted"] = "yes" in l.lower()
            elif "Volume:" in l and "Base Volume:" not in l and "volume_set" not in curr:
                m = re.search(r"(\d+)%", l)
                if m:
                    curr["vol"] = int(m.group(1))
                    curr["volume_set"] = True
        if curr:
            sinks.append(curr)
    except Exception:
        pass

    # Parse all sources (microphones)
    sources = []
    try:
        sources_out = subprocess.check_output(["pactl", "list", "sources"], text=True)
        curr = {}
        for line in sources_out.splitlines():
            l = line.strip()
            if line.startswith("Source #"):
                if curr:
                    sources.append(curr)
                curr = {"id": line.split("#")[1].strip(), "vol": 100, "muted": False}
            elif l.startswith("Name:"):
                curr["name"] = l.split(":", 1)[1].strip()
            elif l.startswith("Description:"):
                curr["desc"] = l.split(":", 1)[1].strip()
            elif l.startswith("Mute:"):
                curr["muted"] = "yes" in l.lower()
            elif "Volume:" in l and "Base Volume:" not in l and "volume_set" not in curr:
                m = re.search(r"(\d+)%", l)
                if m:
                    curr["vol"] = int(m.group(1))
                    curr["volume_set"] = True
        if curr:
            sources.append(curr)
    except Exception:
        pass

    # Filter real input devices (exclude output monitor streams)
    inputs = [s for s in sources if not s.get("name", "").endswith(".monitor")]

    # Find active sink and source objects
    active_sink = next((s for s in sinks if s.get("name") == def_sink), None)
    if not active_sink and sinks:
        active_sink = sinks[0]

    active_source = next((s for s in inputs if s.get("name") == def_source), None)
    if not active_source and inputs:
        active_source = inputs[0]

    # Active sink inputs (playing apps)
    app_streams = []
    try:
        inputs_out = subprocess.check_output(["pactl", "list", "sink-inputs"], text=True)
        curr = {}
        for line in inputs_out.splitlines():
            l = line.strip()
            if line.startswith("Sink Input #"):
                if curr:
                    app_streams.append(curr)
                curr = {"id": line.split("#")[1].strip(), "vol": 100, "muted": False}
            elif l.startswith("application.name ="):
                curr["app"] = l.split("=", 1)[1].strip(' "')
            elif l.startswith("media.name ="):
                curr["media"] = l.split("=", 1)[1].strip(' "')
            elif l.startswith("Mute:"):
                curr["muted"] = "yes" in l.lower()
            elif "Volume:" in l and "volume_set" not in curr:
                m = re.search(r"(\d+)%", l)
                if m:
                    curr["vol"] = int(m.group(1))
                    curr["volume_set"] = True
        if curr:
            app_streams.append(curr)
    except Exception:
        pass

    return {
        "def_sink": def_sink,
        "def_source": def_source,
        "active_sink": active_sink,
        "active_source": active_source,
        "sinks": sinks,
        "sources": inputs,
        "app_streams": app_streams
    }


def set_sink_volume(vol_pct):
    vol_pct = max(0, min(100, vol_pct))
    subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{vol_pct}%"], check=False)
    # If unmuting when setting volume
    if vol_pct > 0:
        subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "0"], check=False)
    icon = "󰕾" if vol_pct >= 65 else ("󰖀" if vol_pct >= 30 else ("󰕿" if vol_pct > 0 else "󰝟"))
    notify(f"{icon} Output Volume: {vol_pct}%", f"Set default audio output to {vol_pct}%", value=vol_pct)


def toggle_sink_mute():
    subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"], check=False)
    # Check new state
    state = get_audio_state()
    sink = state["active_sink"]
    if sink and sink["muted"]:
        notify("󰝟 Audio Muted", "Audio output is currently muted", urgency="normal")
    else:
        vol = sink["vol"] if sink else 50
        notify("󰕾 Audio Unmuted", f"Playback resumed at {vol}%", value=vol)


def toggle_source_mute():
    subprocess.run(["pactl", "set-source-mute", "@DEFAULT_SOURCE@", "toggle"], check=False)
    state = get_audio_state()
    src = state["active_source"]
    if src and src["muted"]:
        notify("󰍭 Microphone Muted", "Audio input is currently muted", urgency="normal")
    else:
        vol = src["vol"] if src else 100
        notify("󰍬 Microphone Unmuted", f"Microphone active at {vol}%", value=vol)


def switch_output_device(sinks, current_def):
    items = []
    for s in sinks:
        is_active = s.get("name") == current_def
        status_prefix = "󰄬 " if is_active else "  "
        vol_str = f"{s.get('vol', 0)}%"
        icon = "󰋋" if any(w in s.get("desc", "").lower() for w in ["headphone", "headset", "bluetooth", "momentum", "ear"]) else "󰓃"
        items.append(f"{status_prefix}{icon}  {s.get('desc')} ({vol_str})")
    items.append("────────────────────────────────────────────────────────────")
    items.append("󰌍  Back to Audio Dashboard")

    choice = run_rofi("output device :~$", items)
    if choice and "Back to Audio Dashboard" not in choice and not choice.startswith("──"):
        for s in sinks:
            if s.get("desc") in choice:
                subprocess.run(["pactl", "set-default-sink", s["name"]], check=False)
                # Move active inputs to new sink
                try:
                    inputs_out = subprocess.check_output(["pactl", "list", "short", "sink-inputs"], text=True)
                    for line in inputs_out.splitlines():
                        in_id = line.split()[0]
                        subprocess.run(["pactl", "move-sink-input", in_id, s["name"]], check=False)
                except Exception:
                    pass
                notify("󰓃 Output Switched", f"Audio output switched to:\n{s.get('desc')}")
                break


def switch_input_device(sources, current_def):
    items = []
    for s in sources:
        is_active = s.get("name") == current_def
        status_prefix = "󰄬 " if is_active else "  "
        vol_str = f"{s.get('vol', 0)}%"
        items.append(f"{status_prefix}󰍬  {s.get('desc')} ({vol_str})")
    items.append("────────────────────────────────────────────────────────────")
    items.append("󰌍  Back to Audio Dashboard")

    choice = run_rofi("microphone device :~$", items)
    if choice and "Back to Audio Dashboard" not in choice and not choice.startswith("──"):
        for s in sources:
            if s.get("desc") in choice:
                subprocess.run(["pactl", "set-default-source", s["name"]], check=False)
                notify("󰍬 Microphone Switched", f"Default input switched to:\n{s.get('desc')}")
                break


def manage_app_streams(streams):
    if not streams:
        run_rofi("active streams :~$", ["  󰎆  No active application audio streams", "󰌍  Back to Dashboard"])
        return

    items = []
    for app in streams:
        app_name = app.get("app") or app.get("media") or f"Stream #{app['id']}"
        muted_str = " · Muted" if app.get("muted") else ""
        items.append(f"󰎆  {app_name:<20} Vol: {app['vol']}%{muted_str} (ID: {app['id']})")
    items.append("────────────────────────────────────────────────────────────")
    items.append("󰌍  Back to Audio Dashboard")

    choice = run_rofi("app streams :~$", items)
    if choice and "Back to Audio Dashboard" not in choice and not choice.startswith("──"):
        for app in streams:
            if f"(ID: {app['id']})" in choice:
                action = run_rofi(f"{app.get('app', 'app')} volume :~$", [
                    f"  󰕾  Set 100% Volume",
                    f"  󰖀  Set 75% Volume",
                    f"  󰖀  Set 50% Volume",
                    f"  󰕿  Set 25% Volume",
                    f"  󰝟  Toggle Mute",
                    "  󰌍  Cancel"
                ])
                if action:
                    if "100%" in action:
                        subprocess.run(["pactl", "set-sink-input-volume", app["id"], "100%"], check=False)
                    elif "75%" in action:
                        subprocess.run(["pactl", "set-sink-input-volume", app["id"], "75%"], check=False)
                    elif "50%" in action:
                        subprocess.run(["pactl", "set-sink-input-volume", app["id"], "50%"], check=False)
                    elif "25%" in action:
                        subprocess.run(["pactl", "set-sink-input-volume", app["id"], "25%"], check=False)
                    elif "Toggle Mute" in action:
                        subprocess.run(["pactl", "set-sink-input-mute", app["id"], "toggle"], check=False)
                break


def main():
    while True:
        state = get_audio_state()
        sink = state["active_sink"]
        src = state["active_source"]

        sink_vol = sink["vol"] if sink else 0
        sink_muted = sink["muted"] if sink else False
        sink_desc = sink.get("desc", "Default Audio Sink") if sink else "No active output"

        src_vol = src["vol"] if src else 0
        src_muted = src["muted"] if src else False
        src_desc = src.get("desc", "Default Microphone") if src else "No active input"

        vol_meter = make_meter(sink_vol if not sink_muted else 0)
        mic_meter = make_meter(src_vol if not src_muted else 0)

        out_status = "Muted" if sink_muted else f"{sink_vol}%"
        mic_status = "Muted" if src_muted else f"{src_vol}%"

        out_icon = "󰝟" if sink_muted else ("󰕾" if sink_vol >= 65 else ("󰖀" if sink_vol >= 30 else "󰕿"))
        mic_icon = "󰍭" if src_muted else "󰍬"

        active_apps = state["app_streams"]
        apps_summary = f"{len(active_apps)} app(s) playing" if active_apps else "Idle (no audio playing)"

        items = [
            f"{out_icon}  Active Output: {sink_desc}",
            f"󰕾  Output Volume: [{vol_meter}] {out_status}",
            f"{mic_icon}  Microphone:    [{mic_meter}] {mic_status} ({src_desc})",
            f"󰎆  Playing Audio: {apps_summary}",
            "────────────────────────────────────────────────────────────",
            f"󰝟  Toggle Output Mute ({'Unmute' if sink_muted else 'Mute'})",
            f"󰍭  Toggle Microphone Mute ({'Unmute' if src_muted else 'Mute'})",
            "󰓃  Switch Audio Output Device...",
            "󰍬  Switch Microphone / Input Source...",
            f"󰎆  Manage Per-Application Audio Streams ({len(active_apps)})...",
            "󰕾  Set Output Volume: 100% (Maximum)",
            "󰕾  Set Output Volume:  80% (High)",
            "󰖀  Set Output Volume:  60% (Medium)",
            "󰖀  Set Output Volume:  40% (Moderate)",
            "󰕿  Set Output Volume:  20% (Low)",
            "󰓅  Launch Interactive Terminal Mixer (alsamixer)",
            "󰆏  Copy Audio Diagnostics to Clipboard",
            "󰑐  Refresh Audio Dashboard"
        ]

        choice = run_rofi("󰕾 audio :~$", items)
        if not choice:
            break

        # Check if user typed a raw volume number e.g. "75" or "80%"
        m = re.match(r"^(\d+)\s*%?$", choice.strip())
        if m:
            val = int(m.group(1))
            set_sink_volume(val)
            continue

        if "Toggle Output Mute" in choice:
            toggle_sink_mute()
        elif "Toggle Microphone Mute" in choice:
            toggle_source_mute()
        elif "Switch Audio Output Device" in choice or "Active Output" in choice:
            switch_output_device(state["sinks"], state["def_sink"])
        elif "Switch Microphone" in choice or "Microphone:" in choice:
            switch_input_device(state["sources"], state["def_source"])
        elif "Manage Per-Application" in choice or "Playing Audio" in choice:
            manage_app_streams(state["app_streams"])
        elif "Set Output Volume: 100%" in choice:
            set_sink_volume(100)
        elif "Set Output Volume:  80%" in choice:
            set_sink_volume(80)
        elif "Set Output Volume:  60%" in choice:
            set_sink_volume(60)
        elif "Set Output Volume:  40%" in choice:
            set_sink_volume(40)
        elif "Set Output Volume:  20%" in choice:
            set_sink_volume(20)
        elif "Output Volume:" in choice:
            # Clicked volume gauge -> prompt quick volume selector
            vol_choice = run_rofi("set volume % :~$", [
                "  󰕾  100%", "  󰕾  90%", "  󰕾  80%", "  󰖀  70%", "  󰖀  60%",
                "  󰖀  50%", "  󰕿  40%", "  󰕿  30%", "  󰕿  20%", "  󰕿  10%",
                "  󰝟   0% (Mute)", "  󰌍  Back to Dashboard"
            ])
            if vol_choice and "Back" not in vol_choice:
                vm = re.search(r"(\d+)%", vol_choice)
                if vm:
                    set_sink_volume(int(vm.group(1)))
        elif "Launch Interactive Terminal Mixer" in choice:
            subprocess.Popen(["alacritty", "--class", "FloatingAudio", "-e", "alsamixer"])
            break
        elif "Copy Audio Diagnostics" in choice:
            sink_list = "\n".join([f"  - [{s.get('id')}] {s.get('desc')} (Vol: {s.get('vol')}%, Muted: {s.get('muted')})" for s in state['sinks']])
            src_list = "\n".join([f"  - [{s.get('id')}] {s.get('desc')} (Vol: {s.get('vol')}%, Muted: {s.get('muted')})" for s in state['sources']])
            app_list = "\n".join([f"  - {a.get('app', 'app')} (ID: {a['id']}, Vol: {a['vol']}%, Muted: {a['muted']})" for a in state['app_streams']]) or "  (None)"
            summary = (
                f"Audio Server: PipeWire 1.6.8\n"
                f"Default Sink: {sink_desc} (Vol: {sink_vol}%, Muted: {sink_muted})\n"
                f"Default Source: {src_desc} (Vol: {src_vol}%, Muted: {src_muted})\n"
                f"\nOutput Sinks:\n{sink_list}\n"
                f"\nInput Sources:\n{src_list}\n"
                f"\nActive App Streams:\n{app_list}\n"
            )
            if shutil.which("xclip"):
                p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE, text=True)
                p.communicate(summary)
                notify("Audio Diagnostics Copied", "Audio server details copied to clipboard.")
        elif "Refresh Audio Dashboard" in choice:
            continue
        else:
            continue


if __name__ == "__main__":
    main()
