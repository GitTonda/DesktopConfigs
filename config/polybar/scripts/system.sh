#!/usr/bin/env bash
# Polybar System helper script for CPU & RAM notifications

case "$1" in
    --notify-cpu)
        python3 -c '
import os, time, subprocess, glob

def read_stat():
    with open("/proc/stat") as f:
        fields = [float(x) for x in f.readline().strip().split()[1:8]]
    return fields[3] + fields[4], sum(fields)

i1, t1 = read_stat()
time.sleep(0.08)
i2, t2 = read_stat()
delta_total = t2 - t1
delta_idle = i2 - i1
util = max(0, min(100, int(round(100.0 * (1.0 - delta_idle / delta_total))))) if delta_total > 0 else 0

model = "CPU"
with open("/proc/cpuinfo") as f:
    for line in f:
        if "model name" in line:
            model = line.split(":", 1)[1].strip().replace("(R)", "").replace("(TM)", "").replace("Processor", "").replace("CPU", "").strip()
            break

temp = 0
for hwmon in glob.glob("/sys/class/hwmon/hwmon*"):
    try:
        with open(os.path.join(hwmon, "name")) as f:
            if "coretemp" in f.read() or "k10temp" in f.read():
                with open(os.path.join(hwmon, "temp1_input")) as tf:
                    temp = int(tf.read().strip()) // 1000
                break
    except Exception:
        pass

freqs = []
for p in glob.glob("/sys/devices/system/cpu/cpu*/cpufreq/scaling_cur_freq"):
    try:
        with open(p) as f:
            freqs.append(int(f.read().strip()) / 1000.0)
    except Exception:
        pass
avg_freq = f"{sum(freqs)/len(freqs)/1000.0:.2f} GHz" if freqs else "N/A"

with open("/proc/loadavg") as f:
    loadavg = ", ".join(f.read().strip().split()[:3])

temp_str = f"{temp}°C" if temp > 0 else "N/A"

body = f"<b>{model}</b>\n<b>Load:</b> {util}%  ·  <b>Temp:</b> {temp_str}\n<b>Freq:</b> {avg_freq}  ·  <b>LoadAvg:</b> {loadavg}"
subprocess.run([
    "dunstify", "-a", "System Monitor",
    "-r", "9956",
    "-u", "normal",
    "-h", f"int:value:{util}",
    "-h", "string:x-dunst-stack-tag:sys_cpu",
    "󰍛 CPU Telemetry",
    body
])
'
        ;;
    --notify-mem)
        python3 -c '
import os, subprocess

mem = {}
with open("/proc/meminfo") as f:
    for line in f:
        p = line.split(":")
        mem[p[0].strip()] = int(p[1].strip().split()[0])

tot = mem.get("MemTotal", 1) / (1024.0 * 1024.0)
avail = mem.get("MemAvailable", mem.get("MemFree", 0)) / (1024.0 * 1024.0)
used = tot - avail
pct = max(0, min(100, int(round((used / tot) * 100.0))))

swap_tot = mem.get("SwapTotal", 0) / (1024.0 * 1024.0)
swap_free = mem.get("SwapFree", 0) / (1024.0 * 1024.0)
swap_used = swap_tot - swap_free
swap_pct = int(round((swap_used / swap_tot) * 100.0)) if swap_tot > 0 else 0

body = f"<b>RAM:</b> {used:.1f} / {tot:.1f} GB ({pct}%)\n<b>Available:</b> {avail:.1f} GB\n<b>Swap:</b> {swap_used:.1f} / {swap_tot:.1f} GB ({swap_pct}%)"
subprocess.run([
    "dunstify", "-a", "System Monitor",
    "-r", "9957",
    "-u", "normal",
    "-h", f"int:value:{pct}",
    "-h", "string:x-dunst-stack-tag:sys_mem",
    "󰘚 Memory Telemetry",
    body
])
'
        ;;
    *)
        exec ~/.config/rofi/system.sh
        ;;
esac
