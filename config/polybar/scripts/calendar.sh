#!/usr/bin/env bash
python3 -c '
import calendar, datetime, subprocess, re

now = datetime.datetime.now()
cal_lines = calendar.month(now.year, now.month).splitlines()
header = f"<span color=\"#89b4fa\"><b>{cal_lines[0].strip()}</b></span>"
weekdays = cal_lines[1]

body = "\n".join(cal_lines[2:])
# Highlight current day with bold blue
body_highlighted = re.sub(r"\b" + str(now.day) + r"\b", f"<span color=\"#89b4fa\"><b>{now.day}</b></span>", body)

full_msg = f"{header}\n<span color=\"#a6adc8\">{weekdays}</span>\n{body_highlighted}"
subprocess.run(["dunstify", "-r", "8888", "-t", "4500", "󰃭 Calendar", full_msg])
'
