# Catppuccin Mocha Minimal Rice (i3 + Polybar + Alacritty)

A clean, distraction-free, and high-performance Linux desktop environment built on **i3wm**, themed in **Catppuccin Mocha** with **JetBrainsMono Nerd Font**.

Designed for power users, developers, and keyboard-driven workflows. Fully portable and ready to deploy on any PC or laptop running **Arch Linux**, **Pop!_OS/Debian/Ubuntu**, or **Fedora**.

---

## 💻 The Stack

| Component | Software | Description |
|---|---|---|
| **Display Manager** | `ly` | Minimal TUI terminal console display manager |
| **Window Manager** | `i3` (with native gaps) | Lightweight, manual tiling window manager (crisp squared borders) |
| **Status Bar** | `polybar` | Clean bar with interactive Wi-Fi, Ethernet, CPU, RAM, Audio, Calendar, and Battery modules |
| **Terminal** | `alacritty` | Fast, GPU-accelerated terminal with authentic Mocha colors and blur |
| **Compositor** | `picom` | Smooth GLX backend with tear-free VSync, crisp squared window edges |
| **App Launcher** | `rofi` | Terminal-vibe CLI popup matching Alacritty palette |
| **Wi-Fi Manager** | `rofi` + `nmcli` | Dedicated native terminal Wi-Fi scanner, connector, and selector |
| **Power Menu** | `rofi` | Monospace terminal modal with direct [1]-[4] key selection |
| **Notifications** | `dunst` | Low-profile monospace notification popups with Pango markup |
| **Screenshots** | `maim` + `xclip` | Instant crop-and-copy straight to clipboard with desktop notifications |
| **File Manager** | `ranger` | Terminal-based 3-pane file manager |
| **Resource Monitor** | `btop` | Terminal system usage monitor |
| **Audio Mixer** | `alsamixer` + `pipewire` | Interactive modal mixer & PulseAudio compatibility |
| **Media Player** | `mpv` | Borderless, GPU-accelerated video/audio player |
| **Text Editor** | `nano` | Modernized with mouse selection enabled and syntax highlighting |

---

## ⌨️ Keybindings Cheat-Sheet

Modifier Key: **`Super`** (Windows Key)

### Applications & Applets
| Shortcut | Action |
|---|---|
| `Super + Return` | Launch Terminal (**Alacritty**) |
| `Super + Shift + Return` | Launch File Manager (**Ranger**) |
| `Super + D` | Application Launcher (**Rofi**) |
| `Super + Shift + W` | Interactive Wi-Fi Applet (**Rofi Wi-Fi**) |
| `Super + Shift + B` | Wallpaper Selector (**Rofi / Visual Gallery**) |
| `Super + Shift + A` | Audio Mixer Modal (**Alsamixer**) |
| `Super + Shift + M` | System Monitor Modal (**btop**) |
| `Super + Q` | **Close / Kill focused window** |
| `F13` or `Print` or `Super + Shift + S` | **Instant Crop & Copy Screenshot to Clipboard** |
| `Shift + Print` | Full-screen screenshot to clipboard |
| `Super + Escape` or `Super + Shift + E` | **Power Menu** (Sleep, Reboot, Shutdown, Logout) |

### Top Bar Click Actions
| Module | Left Click | Right Click | Scroll |
|---|---|---|---|
| **Date (`󰃭`)** | Monthly Calendar Popup | Monthly Calendar Popup | - |
| **Volume (`󰕾` / `󰝟`)** | Toggle Mute | Audio Mixer Modal (`alsamixer`) | Volume Up / Down 5% |
| **Wi-Fi (`󰤨`)** | Rofi Wi-Fi Menu (scan & connect) | Network Connections (`nmtui`) | - |
| **Ethernet (`󰈀`)** | Network Connections (`nmtui`) | Network Connections (`nmtui`) | - |
| **CPU (`󰍛`) & RAM (`󰘚`)** | Launch `btop` Monitor | Launch `btop` Monitor | - |
| **Power (`󰐥`)** | Power Menu | Power Menu | - |

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

### Audio & Brightness Hardware Keys
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

## 🚀 One-Command Installation (Fresh Arch or Any Machine)

### Option A: Direct Bootstrap (from empty TTY)
On a fresh Arch Linux install (or any clean Linux installation):
```bash
curl -fsSL https://raw.githubusercontent.com/GitTonda/DesktopConfigs/main/bootstrap.sh | bash
```

### Option B: Manual Clone & Run
```bash
# 1. Clone your dotfiles repository
git clone https://github.com/GitTonda/DesktopConfigs.git ~/dotfiles

# 2. Run the automated installer
cd ~/dotfiles
chmod +x ./install.sh
./install.sh
```

### What `install.sh` handles automatically on Arch:
1. **Full X11 & Audio Stack:** Installs `xorg-server`, `xorg-xinit`, `pipewire`, `pipewire-pulse`, `wireplumber`, and `alsa-utils`.
2. **Desktop & Rice Packages:** Installs `i3-wm`, `polybar`, `alacritty`, `picom`, `rofi`, `feh`, `dunst`, `btop`, `ranger`, `mpv`.
3. **Fonts:** Installs `ttf-jetbrains-mono-nerd`, `ttf-font-awesome`, and `noto-fonts-emoji` natively via pacman.
4. **Networking:** Installs `networkmanager` and automatically enables `NetworkManager.service`.
5. **Display Manager:** Installs `ly`, deploys corner-free styling, and enables `ly.service`.
6. **Dotfiles & Wallpapers:** Deploys all configurations to `~/.config/`, sets up `~/.xinitrc`, copies wallpapers, and makes helper scripts executable.

---

## ⚡ System Optimization

To disable redundant background daemons, limit systemd journal size to 100MB, and apply kernel responsiveness sysctl tuning:
```bash
sudo bash ~/dotfiles/scripts/optimize_system.sh
```

---

## 🎨 Changing Wallpapers

Place any image in `~/Pictures/Wallpapers/` and set it with:
```bash
feh --bg-fill ~/Pictures/Wallpapers/your_wallpaper.jpg
```
The wallpaper will automatically persist across reboots via `~/.fehbg`.
