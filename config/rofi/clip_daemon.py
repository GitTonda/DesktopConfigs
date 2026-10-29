#!/usr/bin/env python3
"""
Lightweight Clipboard Daemon for Rofi
Maintains clean history of recent clipboard entries in ~/.cache/rofi_clipboard.json
"""

import os
import sys
import time
import json
import subprocess

CACHE_FILE = os.path.expanduser("~/.cache/rofi_clipboard.json")
MAX_ENTRIES = 80


def load_history():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_history(history):
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def get_current_clip():
    try:
        res = subprocess.run(
            ["xclip", "-o", "-selection", "clipboard"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            check=False,
            timeout=1
        )
        if res.returncode == 0:
            return res.stdout
    except Exception:
        pass
    return None


def sanitize_preview(text):
    first_line = text.strip().splitlines()[0] if text.strip() else ""
    first_line = " ".join(first_line.split())
    if len(first_line) > 75:
        first_line = first_line[:72] + "..."
    line_count = len(text.strip().splitlines())
    if line_count > 1:
        first_line += f"  [{line_count} lines]"
    return first_line


def main():
    history = load_history()
    last_clip = history[0]["raw"] if history else ""

    while True:
        try:
            curr = get_current_clip()
            if curr and curr.strip() and curr != last_clip:
                last_clip = curr
                preview = sanitize_preview(curr)
                # Remove if already exists (to move to top)
                history = [item for item in history if item.get("raw") != curr]
                history.insert(0, {
                    "preview": preview,
                    "raw": curr,
                    "time": int(time.time())
                })
                history = history[:MAX_ENTRIES]
                save_history(history)
        except Exception:
            pass
        time.sleep(0.75)


if __name__ == "__main__":
    main()
