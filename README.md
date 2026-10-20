# Catppuccin Mocha Minimal Rice (i3 + Polybar + Alacritty)

A clean, distraction-free, and high-performance Linux desktop environment built on **i3wm**, themed in **Catppuccin Mocha** with **JetBrainsMono Nerd Font**.

Designed for power users, developers, and keyboard-driven workflows. Fully portable and ready to deploy on any PC or laptop.

---

## 💻 The Stack

| Component | Software | Description |
|---|---|---|
| **Window Manager** | `i3` (with native gaps) | Lightweight, manual tiling window manager |
| **Status Bar** | `polybar` | Clean bar with auto-detecting Wi-Fi, Ethernet, CPU, RAM, Audio, and Laptop Battery support |
| **Terminal** | `alacritty` | Fast, GPU-accelerated terminal with authentic Mocha colors and blur |
| **Compositor** | `picom` | Smooth GLX backend with tear-free VSync, soft shadows, and subtle fading |
| **App Launcher** | `rofi` | Sleek centered modal launcher with search |
| **Power Menu** | `rofi` | Minimal horizontal card powermenu (`Sleep`, `Reboot`, `Power`, `Logout`) |
| **Notifications** | `dunst` | Low-profile monospace notification popups |
| **Screenshots** | `maim` + `xclip` | Instant crop-and-copy straight to clipboard |
| **File Manager** | `ranger` | Terminal-based 3-pane file manager |
| **Resource Monitor** | `btop` | Terminal system usage monitor |
| **Media Player** | `mpv` | Borderless, GPU-accelerated video/audio player |
| **Text Editor** | `nano` | Modernized with mouse selection enabled and syntax highlighting |

---

## ⌨️ Keybindings Cheat-Sheet

Modifier Key: **`Super`** (Windows Key)

### Applications
| Shortcut | Action |
|---|---|
| `Super + Return` | Launch Terminal (**Alacritty**) |
| `Super + Shift + Return` | Launch File Manager (**Ranger**) |
| `Super + Shift + M` | Launch System Monitor (**btop**) |
| `Super + D` | Application Launcher (**Rofi**) |
| `Super + Q` | **Close / Kill focused window** |
| `F13` or `Print` or `Super + Shift + S` | **Instant Crop & Copy Screenshot to Clipboard** |
| `Shift + Print` | Full-screen screenshot to clipboard |
| `Super + Escape` or `Super + Shift + E` | **Power Menu** (Sleep, Reboot, Shutdown, Logout) |

### Navigation & Tiling
| Shortcut | Action |
|---|---|
| `Super + H / J / K / L` | Focus window (Vim keys: Left / Down / Up / Right) |
| `Super + Left / Down / Up / Right` | Focus window (Arrow keys) |
| `Super + Shift + H / J / K / L` | Move window (Vim keys) |
| `Super + Shift + Left / Down / Up / Right` | Move window (Arrow keys) |
| `Super + B` | Split Horizontally |
| `Super + V` | Split Vertically |
| `Super + F` | Toggle Fullscreen |
| `Super + Shift + Space` | Toggle Floating mode |
| `Super + 1 - 0` | Switch to Workspace 1 - 10 |
| `Super + Shift + 1 - 0` | Move container to Workspace 1 - 10 |
| `Super + R` | Enter Window Resize mode (`Escape` or `Enter` to exit) |
| `Super + Shift + R` | Restart i3 in-place |

### Audio & Brightness
| Shortcut | Action |
|---|---|
| `XF86AudioRaiseVolume` | Volume +5% |
| `XF86AudioLowerVolume` | Volume -5% |
| `XF86AudioMute` | Toggle Audio Mute |
| `XF86AudioMicMute` | Toggle Mic Mute |
| `XF86AudioPlay` | Media Play / Pause (`playerctl`) |
| `XF86AudioNext` | Media Next Track |
| `XF86AudioPrev` | Media Previous Track |
| `XF86MonBrightnessUp` | Brightness +10% |
| `XF86MonBrightnessDown` | Brightness -10% |

---

## 🚀 One-Command Installation (On Laptop or New PC)

To clone and replicate this exact rice on your laptop:

```bash
# 1. Clone your dotfiles repository
git clone https://github.com/<your-username>/dotfiles.git ~/dotfiles

# 2. Run the automated installer
cd ~/dotfiles
./install.sh
```

### What `install.sh` handles automatically:
1. Detects your package manager (`apt`, `pacman`, or `dnf`) and installs all required software.
2. Automatically downloads and installs **JetBrainsMono Nerd Font** if not present.
3. Creates a timestamped backup of any existing configs in `~/.config_backup_<timestamp>`.
4. Deploys configs to `~/.config/` and `~/.nanorc`.
5. Deploys wallpapers to `~/Pictures/Wallpapers/` and sets the default with `feh`.
6. Sets execution permissions on Polybar and Rofi scripts.

---

## 🎨 Changing Wallpapers

All wallpapers reside in `~/Pictures/Wallpapers/`.

To change the wallpaper:
```bash
feh --bg-fill ~/Pictures/Wallpapers/<filename>
```
`feh` automatically saves your selection to `~/.fehbg`, and i3 restores it on every boot automatically.
