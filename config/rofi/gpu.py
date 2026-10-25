#!/usr/bin/env python3
"""
Rofi GPU Dashboard & Performance Control Card
Catppuccin Mocha minimal terminal-style GPU management applet.
"""

import sys
import os
import subprocess
import shutil

ROFI_THEME = os.path.expanduser("~/.config/rofi/gpu.rasi")


def notify(title, message, urgency="normal"):
    if shutil.which("dunstify"):
        subprocess.run([
            "dunstify", "-a", "GPU Monitor",
            "-r", "9944",
            "-u", urgency,
            "-h", "string:x-dunst-stack-tag:gpu_status",
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


def make_meter(pct, width=10):
    pct = max(0, min(100, pct))
    filled = int(round((pct / 100.0) * width))
    empty = width - filled
    return "■" * filled + "□" * empty


def get_nvidia_data():
    query_cmd = [
        "nvidia-smi",
        "--query-gpu=name,driver_version,temperature.gpu,utilization.gpu,memory.used,memory.total,power.draw,power.limit,fan.speed,clocks.current.graphics,clocks.max.graphics",
        "--format=csv,noheader,nounits"
    ]
    try:
        out = subprocess.check_output(query_cmd, text=True, stderr=subprocess.DEVNULL).strip()
        if not out:
            return None
        parts = [p.strip() for p in out.split(",")]
        if len(parts) >= 11:
            name, driver, temp, util, vram_u, vram_t, pwr, pwr_lim, fan, clk, clk_max = parts
            return {
                "name": name,
                "driver": driver,
                "temp": int(temp) if temp.isdigit() else 0,
                "util": int(util) if util.isdigit() else 0,
                "vram_used_mb": float(vram_u) if vram_u.replace('.', '', 1).isdigit() else 0.0,
                "vram_tot_mb": float(vram_t) if vram_t.replace('.', '', 1).isdigit() else 1.0,
                "power_w": float(pwr) if pwr.replace('.', '', 1).isdigit() else 0.0,
                "power_limit_w": float(pwr_lim) if pwr_lim.replace('.', '', 1).isdigit() else 0.0,
                "fan": int(fan) if fan.isdigit() else 0,
                "clk": int(clk) if clk.isdigit() else 0,
                "clk_max": int(clk_max) if clk_max.isdigit() else 0,
            }
    except Exception:
        pass
    return None


def get_gpu_processes():
    procs = []
    try:
        out = subprocess.check_output(["nvidia-smi"], text=True, stderr=subprocess.DEVNULL)
        in_procs = False
        for line in out.splitlines():
            if "Processes:" in line:
                in_procs = True
                continue
            if in_procs and line.startswith("|") and not line.startswith("+") and not line.startswith("|="):
                cols = line.strip("|").split()
                if len(cols) >= 5 and cols[0].isdigit():
                    mem = cols[-1]
                    p_name = cols[-2]
                    p_type = cols[-3]
                    pid = cols[-4]
                    
                    # Try reading cleaner process name from /proc/<pid>/comm
                    comm_name = None
                    try:
                        with open(f"/proc/{pid}/comm", "r") as f:
                            comm_name = f.read().strip()
                    except Exception:
                        pass
                    
                    display_name = comm_name if comm_name else os.path.basename(p_name)
                    procs.append({
                        "pid": pid,
                        "type": p_type,
                        "name": display_name,
                        "raw_path": p_name,
                        "mem": mem
                    })
    except Exception:
        pass
    return procs


def get_power_mode():
    try:
        out = subprocess.check_output(["nvidia-settings", "-q", "[gpu:0]/GPUPowerMizerMode"], text=True, stderr=subprocess.DEVNULL)
        if "): 1." in out:
            return "Prefer Max Perf"
        elif "): 0." in out:
            return "Adaptive"
        elif "): 2." in out:
            return "Auto (Default)"
    except Exception:
        pass
    return "Standard"


def inspect_processes(procs):
    if not procs:
        run_rofi("active apps :~$", ["  󰋔  No active graphical processes found on GPU"])
        return "back"

    items = []
    for p in procs:
        items.append(f"󰒋  PID {p['pid']:<7} {p['name']:<18} ({p['mem']})")
    items.append("────────────────────────────────────────────────────────────")
    items.append("󰌍  Back to Dashboard")

    choice = run_rofi("active apps :~$", items)
    if not choice or "Back to Dashboard" in choice:
        return "back"
    if not choice.startswith("──"):
        for p in procs:
            if f"PID {p['pid']}" in choice:
                action = run_rofi(f"pid {p['pid']} ({p['name']}) :~$", [
                    f"  󰗨  Kill process (SIGKILL {p['pid']})",
                    "  󰌍  Cancel"
                ])
                if action and "Kill" in action:
                    try:
                        subprocess.run(["kill", "-9", p['pid']], check=False)
                        notify("Process Terminated", f"Killed PID {p['pid']} ({p['name']})")
                    except Exception as e:
                        notify("Process Error", str(e), urgency="critical")
                break
    return None


def main():
    data = get_nvidia_data()
    if not data:
        run_rofi("gpu :~$", [
            "󰢮  No active NVIDIA GPU detected or driver unavailable",
            "󰌍  Exit"
        ])
        return

    vram_used_gb = data["vram_used_mb"] / 1024.0
    vram_tot_gb = data["vram_tot_mb"] / 1024.0
    vram_pct = int(round((data["vram_used_mb"] / data["vram_tot_mb"]) * 100.0))
    power_pct = int(round((data["power_w"] / max(1.0, data["power_limit_w"])) * 100.0))

    load_meter = make_meter(data["util"])
    vram_meter = make_meter(vram_pct)

    # Thermal status
    if data["temp"] >= 80:
        thermal_status = f"{data['temp']}°C (Hot! Fan: {data['fan']}%)"
    elif data["temp"] >= 65:
        thermal_status = f"{data['temp']}°C (Warm · Fan: {data['fan']}%)"
    else:
        thermal_status = f"{data['temp']}°C (Cool · Fan: {data['fan']}%)"

    procs = get_gpu_processes()
    power_mode = get_power_mode()

    items = [
        f"󰢮  {data['name']} (Driver: {data['driver']})",
        f"󰍛  GPU Load:     [{load_meter}] {data['util']:2d}% ({data['clk']} MHz)",
        f"󰘚  VRAM Usage:   [{vram_meter}] {vram_used_gb:.1f} / {vram_tot_gb:.1f} GB ({vram_pct}%)",
        f"󱤓  Temperature:  {thermal_status}",
        f"󱐋  Power Draw:   {data['power_w']:.0f}W / {data['power_limit_w']:.0f}W ({power_pct}%) · Mode: {power_mode}",
        f"󰒋  Active Apps:  {len(procs)} processes running on GPU",
        "────────────────────────────────────────────────────────────",
        "󰓅  Launch Live Terminal Monitor (nvitop)",
        "󰒓  Launch NVIDIA Settings Control Panel",
        "󱐋  Switch Power Profile...",
        "󰆏  Copy GPU Telemetry to Clipboard",
        "󰑐  Refresh Dashboard"
    ]

    choice = run_rofi("󰢮 gpu :~$", items)
    if not choice:
        return

    if "Launch Live Terminal Monitor" in choice:
        subprocess.Popen(["alacritty", "--class", "FloatingGPU", "-e", os.path.expanduser("~/.config/polybar/scripts/gpu-top.sh")])
    elif "Launch NVIDIA Settings Control Panel" in choice:
        subprocess.Popen(["nvidia-settings"])
    elif "Switch Power Profile" in choice:
        profile_choice = run_rofi("power profile :~$", [
            "  󱐋  Prefer Maximum Performance (Locks highest clocks)",
            "  󰌍  Adaptive (Dynamically scales clock speeds)",
            "  󰌍  Auto (Driver default policy)",
            "  󰌍  Back to Dashboard"
        ])
        if profile_choice:
            if "Back" in profile_choice:
                main()
            elif "Maximum Performance" in profile_choice:
                subprocess.run(["nvidia-settings", "-a", "[gpu:0]/GPUPowerMizerMode=1"], check=False, stdout=subprocess.DEVNULL)
                notify("GPU Power Mode", "Power mode set to: Prefer Maximum Performance")
            elif "Adaptive" in profile_choice:
                subprocess.run(["nvidia-settings", "-a", "[gpu:0]/GPUPowerMizerMode=0"], check=False, stdout=subprocess.DEVNULL)
                notify("GPU Power Mode", "Power mode set to: Adaptive")
            elif "Auto" in profile_choice:
                subprocess.run(["nvidia-settings", "-a", "[gpu:0]/GPUPowerMizerMode=2"], check=False, stdout=subprocess.DEVNULL)
                notify("GPU Power Mode", "Power mode set to: Auto")
    elif "Copy GPU Telemetry to Clipboard" in choice:
        proc_list = "\n".join([f"  - {p['name']} (PID: {p['pid']}, VRAM: {p['mem']})" for p in procs])
        summary = (
            f"GPU: {data['name']}\n"
            f"Driver: {data['driver']}\n"
            f"Utilization: {data['util']}%\n"
            f"Temperature: {data['temp']}°C (Fan: {data['fan']}%)\n"
            f"VRAM: {vram_used_gb:.2f} GB / {vram_tot_gb:.2f} GB ({vram_pct}%)\n"
            f"Power Draw: {data['power_w']:.1f}W / {data['power_limit_w']:.1f}W\n"
            f"Clock: {data['clk']} MHz / {data['clk_max']} MHz\n"
            f"Active Processes ({len(procs)}):\n{proc_list}\n"
        )
        if shutil.which("xclip"):
            p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE, text=True)
            p.communicate(summary)
            notify("GPU Telemetry Copied", "Hardware stats copied to system clipboard.")
    elif "Active Apps" in choice or "Active processes" in choice or "GPU Load" in choice or "VRAM Usage" in choice:
        if inspect_processes(procs) == "back":
            main()
    elif "Refresh Dashboard" in choice:
        main()


if __name__ == "__main__":
    main()
