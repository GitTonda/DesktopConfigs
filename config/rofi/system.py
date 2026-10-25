#!/usr/bin/env python3
"""
Rofi System & Resource Dashboard
Catppuccin Mocha minimal terminal-style CPU, RAM, and Process management applet.
"""

import sys
import os
import subprocess
import shutil
import time
import glob


ROFI_THEME = os.path.expanduser("~/.config/rofi/system.rasi")


def notify(title, message, urgency="normal"):
    if shutil.which("dunstify"):
        subprocess.run([
            "dunstify", "-a", "System Monitor",
            "-r", "9955",
            "-u", urgency,
            "-h", "string:x-dunst-stack-tag:system_status",
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


def get_cpu_data():
    model = "Generic x86_64 CPU"
    cores = os.cpu_count() or 1
    try:
        with open("/proc/cpuinfo", "r") as f:
            for line in f:
                if "model name" in line:
                    raw = line.split(":", 1)[1].strip()
                    model = (
                        raw.replace("(R)", "")
                        .replace("(TM)", "")
                        .replace("Processor", "")
                        .replace("CPU", "")
                        .strip()
                    )
                    break
    except Exception:
        pass

    # Utilization sampling
    def read_stat():
        with open("/proc/stat", "r") as f:
            fields = [float(x) for x in f.readline().strip().split()[1:8]]
        idle = fields[3] + fields[4]
        total = sum(fields)
        return idle, total

    try:
        i1, t1 = read_stat()
        time.sleep(0.08)
        i2, t2 = read_stat()
        delta_total = t2 - t1
        delta_idle = i2 - i1
        if delta_total > 0:
            util = max(0, min(100, int(round(100.0 * (1.0 - delta_idle / delta_total)))))
        else:
            util = 0
    except Exception:
        util = 0

    # Frequency
    freqs = []
    for p in glob.glob("/sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq"):
        try:
            with open(p, "r") as f:
                freqs.append(int(f.read().strip()) / 1000.0)
        except Exception:
            pass
    avg_freq = sum(freqs) / len(freqs) if freqs else 0.0

    # Temperature
    temp = 0
    for hwmon in glob.glob("/sys/class/hwmon/hwmon*"):
        try:
            name_file = os.path.join(hwmon, "name")
            if os.path.exists(name_file):
                with open(name_file, "r") as f:
                    name = f.read().strip()
                if "coretemp" in name or "k10temp" in name or "zenpower" in name:
                    temp_inputs = glob.glob(os.path.join(hwmon, "temp*_input"))
                    if temp_inputs:
                        with open(temp_inputs[0], "r") as tf:
                            temp = int(tf.read().strip()) // 1000
                        break
        except Exception:
            pass

    # Load average
    try:
        with open("/proc/loadavg", "r") as f:
            load_parts = f.read().strip().split()[:3]
            loadavg = ", ".join(load_parts)
    except Exception:
        loadavg = "N/A"

    return {
        "model": model,
        "cores": cores,
        "util": util,
        "avg_freq_mhz": int(round(avg_freq)),
        "temp": temp,
        "loadavg": loadavg
    }


def get_memory_data():
    mem = {}
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                parts = line.split(":")
                mem[parts[0].strip()] = int(parts[1].strip().split()[0])
    except Exception:
        return None

    tot = mem.get("MemTotal", 1) / (1024.0 * 1024.0)
    avail = mem.get("MemAvailable", mem.get("MemFree", 0)) / (1024.0 * 1024.0)
    used = tot - avail
    pct = max(0, min(100, int(round((used / tot) * 100.0))))

    swap_tot = mem.get("SwapTotal", 0) / (1024.0 * 1024.0)
    swap_free = mem.get("SwapFree", 0) / (1024.0 * 1024.0)
    swap_used = swap_tot - swap_free
    swap_pct = int(round((swap_used / swap_tot) * 100.0)) if swap_tot > 0 else 0

    return {
        "used_gb": used,
        "total_gb": tot,
        "avail_gb": avail,
        "pct": pct,
        "swap_used_gb": swap_used,
        "swap_tot_gb": swap_tot,
        "swap_pct": swap_pct,
    }


def get_disk_data(path="/"):
    try:
        st = os.statvfs(path)
        tot = (st.f_blocks * st.f_frsize) / (1024.0 ** 3)
        avail = (st.f_bavail * st.f_frsize) / (1024.0 ** 3)
        used = tot - avail
        pct = int(round((used / tot) * 100.0))
        return {
            "used_gb": used,
            "total_gb": tot,
            "avail_gb": avail,
            "pct": pct,
        }
    except Exception:
        return {"used_gb": 0, "total_gb": 1, "avail_gb": 1, "pct": 0}


def get_uptime():
    try:
        with open("/proc/uptime", "r") as f:
            sec = float(f.read().split()[0])
        hrs = int(sec // 3600)
        mins = int((sec % 3600) // 60)
        if hrs > 0:
            return f"{hrs}h {mins}m"
        return f"{mins}m"
    except Exception:
        return "N/A"


def get_top_processes(sort_by="cpu", limit=12):
    sort_flag = "-%cpu" if sort_by == "cpu" else "-%mem"
    try:
        out = subprocess.check_output(
            ["ps", "-eo", "pid,user,%cpu,%mem,comm", f"--sort={sort_flag}"],
            text=True, stderr=subprocess.DEVNULL
        )
        procs = []
        for line in out.strip().splitlines()[1:]:
            parts = line.split(None, 4)
            if len(parts) == 5:
                pid, user, cpu, mem, comm = parts
                if comm in ["ps", "grep", "sed"]:
                    continue
                # Try reading cleaner process name
                display_name = comm
                try:
                    with open(f"/proc/{pid}/comm", "r") as cf:
                        display_name = cf.read().strip()
                except Exception:
                    pass
                procs.append({
                    "pid": pid,
                    "user": user,
                    "cpu": float(cpu) if cpu.replace('.', '', 1).isdigit() else 0.0,
                    "mem": float(mem) if mem.replace('.', '', 1).isdigit() else 0.0,
                    "name": display_name
                })
                if len(procs) >= limit:
                    break
        return procs
    except Exception:
        return []


def inspect_processes(sort_by="cpu"):
    procs = get_top_processes(sort_by=sort_by, limit=15)
    if not procs:
        run_rofi("active apps :~$", ["  󰋔  No running processes detected"])
        return "back"

    items = []
    for p in procs:
        val_str = f"CPU: {p['cpu']:4.1f}% · RAM: {p['mem']:3.1f}%"
        items.append(f"󰒋  PID {p['pid']:<6} {p['name']:<18} ({val_str})")
    items.append("────────────────────────────────────────────────────────────")
    toggle_label = "󰘚  Sort by Memory (%MEM)" if sort_by == "cpu" else "󰍛  Sort by Processor (%CPU)"
    items.append(toggle_label)
    items.append("󰌍  Back to System Dashboard")

    prompt_str = f"top apps ({sort_by}) :~$"
    choice = run_rofi(prompt_str, items)
    if not choice or "Back to System Dashboard" in choice:
        return "back"

    if "Sort by" in choice:
        return inspect_processes(sort_by="mem" if sort_by == "cpu" else "cpu")

    if choice.startswith("──"):
        return "back"

    # Process chosen
    for p in procs:
        if f"PID {p['pid']}" in choice:
            action = run_rofi(f"pid {p['pid']} ({p['name']}) :~$", [
                f"  󰗨  Kill process (SIGKILL {p['pid']})",
                f"  󰜎  Terminate gracefully (SIGTERM {p['pid']})",
                "  󰌍  Cancel"
            ])
            if action and "Kill process" in action:
                subprocess.run(["kill", "-9", p['pid']], check=False)
                notify("Process Terminated", f"Sent SIGKILL to PID {p['pid']} ({p['name']})")
            elif action and "Terminate gracefully" in action:
                subprocess.run(["kill", "-15", p['pid']], check=False)
                notify("Process Terminated", f"Sent SIGTERM to PID {p['pid']} ({p['name']})")
            break
    return None


def drop_system_caches():
    try:
        if shutil.which("pkexec"):
            cmd = "sync && echo 3 > /proc/sys/vm/drop_caches"
            subprocess.run(["pkexec", "sh", "-c", cmd], check=False)
            notify("Memory Cleaned", "Dropped pagecache, dentries, and inodes buffers.")
        else:
            notify("Clean Buffers", "Superuser privileges required to drop system caches.", urgency="low")
    except Exception as e:
        notify("Cache Error", str(e), urgency="critical")


def main():
    cpu = get_cpu_data()
    mem = get_memory_data()
    disk = get_disk_data("/")
    uptime = get_uptime()

    if not cpu or not mem:
        run_rofi("system :~$", ["󰍛  Unable to read system metrics", "󰌍  Exit"])
        return

    cpu_meter = make_meter(cpu["util"])
    ram_meter = make_meter(mem["pct"])
    swap_meter = make_meter(mem["swap_pct"])
    disk_meter = make_meter(disk["pct"])

    # Thermal label
    if cpu["temp"] >= 80:
        thermal_str = f"{cpu['temp']}°C (Hot!)"
    elif cpu["temp"] >= 65:
        thermal_str = f"{cpu['temp']}°C (Warm)"
    elif cpu["temp"] > 0:
        thermal_str = f"{cpu['temp']}°C (Cool)"
    else:
        thermal_str = "Normal"

    freq_str = f"{cpu['avg_freq_mhz'] / 1000.0:.2f} GHz" if cpu['avg_freq_mhz'] >= 1000 else f"{cpu['avg_freq_mhz']} MHz"

    top_procs = get_top_processes(sort_by="cpu", limit=4)
    top_str = ", ".join([f"{p['name']} ({p['cpu']:.0f}%)" for p in top_procs])

    items = [
        f"󰍛  {cpu['model']} ({cpu['cores']} Threads)",
        f"󰍛  CPU Load:     [{cpu_meter}] {cpu['util']:2d}% ({freq_str})",
        f"󱤓  Thermal:      {thermal_str} · Load: {cpu['loadavg']}",
        f"󰘚  RAM Usage:    [{ram_meter}] {mem['used_gb']:.1f} / {mem['total_gb']:.1f} GB ({mem['pct']}%)",
        f"󰓅  Swap Usage:   [{swap_meter}] {mem['swap_used_gb']:.1f} / {mem['swap_tot_gb']:.1f} GB ({mem['swap_pct']}%)",
        f"󰋊  Root Disk:    [{disk_meter}] {disk['used_gb']:.0f} / {disk['total_gb']:.0f} GB ({disk['pct']}%) · Free: {disk['avail_gb']:.0f}G",
        f"󱑂  System Up:    {uptime} · Top: {top_str}",
        "────────────────────────────────────────────────────────────",
        "󰒋  Inspect & Manage Heavy Processes...",
        "󰓅  Launch Live Terminal Monitor (btop)",
        "󰚥  System Summary & Hardware Specs (Fastfetch)",
        "󰃢  Drop PageCache & Free Unused RAM",
        "󰆏  Copy System Telemetry to Clipboard",
        "󰑐  Refresh Dashboard"
    ]

    choice = run_rofi("󰍛 system :~$", items)
    if not choice:
        return

    if "Launch Live Terminal Monitor" in choice:
        subprocess.Popen(["alacritty", "--class", "FloatingBtop", "-e", "btop"])
    elif "Inspect & Manage Heavy Processes" in choice:
        if inspect_processes(sort_by="cpu") == "back":
            main()
    elif "System Summary & Hardware Specs" in choice:
        subprocess.Popen(["alacritty", "--class", "FloatingTerm", "-e", "bash", "-c", "fastfetch; echo ''; read -n 1 -s -r -p 'Press any key to close...'"])
    elif "Drop PageCache" in choice:
        drop_system_caches()
    elif "Copy System Telemetry" in choice:
        proc_lines = "\n".join([f"  - {p['name']} (PID: {p['pid']}, CPU: {p['cpu']}%, RAM: {p['mem']}%)" for p in top_procs])
        summary = (
            f"OS: Pop!_OS 24.04 LTS\n"
            f"CPU: {cpu['model']} ({cpu['cores']} Threads)\n"
            f"CPU Load: {cpu['util']}% ({freq_str}, {thermal_str})\n"
            f"Load Average: {cpu['loadavg']}\n"
            f"RAM: {mem['used_gb']:.2f} / {mem['total_gb']:.2f} GB ({mem['pct']}%)\n"
            f"Swap: {mem['swap_used_gb']:.2f} / {mem['swap_tot_gb']:.2f} GB\n"
            f"Disk (/): {disk['used_gb']:.1f} / {disk['total_gb']:.1f} GB ({disk['pct']}%)\n"
            f"Uptime: {uptime}\n"
            f"Top Processes:\n{proc_lines}\n"
        )
        if shutil.which("xclip"):
            p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE, text=True)
            p.communicate(summary)
            notify("System Telemetry Copied", "Hardware telemetry copied to system clipboard.")
    elif "Refresh Dashboard" in choice:
        main()
    elif any(header in choice for header in ["CPU Load", "RAM Usage", "Swap Usage", "Root Disk", "Top:"]):
        if inspect_processes(sort_by="mem" if "RAM" in choice else "cpu") == "back":
            main()


if __name__ == "__main__":
    main()
