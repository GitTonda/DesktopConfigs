#!/usr/bin/env bash
# ==============================================================================
# Antigravity / Catppuccin Mocha Desktop Setup
# Fast, Minimalist, and Complete Linux Desktop Installation Suite
# ==============================================================================

set -e

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ------------------------------------------------------------------------------
# Catppuccin Mocha Color Palette & Styling
# ------------------------------------------------------------------------------
PEACH='\033[38;2;250;179;135m'
BLUE='\033[38;2;137;180;250m'
GREEN='\033[38;2;166;227;161m'
MAUVE='\033[38;2;203;166;247m'
RED='\033[38;2;243;139;168m'
YELLOW='\033[38;2;249;226;175m'
TEAL='\033[38;2;148;226;213m'
LAVENDER='\033[38;2;180;190;254m'
SUBTEXT='\033[38;2;166;173;200m'
SURFACE='\033[38;2;49;50;68m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# ------------------------------------------------------------------------------
# Helper Formatting Functions
# ------------------------------------------------------------------------------
step_header() {
    local step="$1"
    local title="$2"
    echo ""
    echo -e "  ${MAUVE}${BOLD}[${step}]${NC} ${BOLD}${title}${NC}"
}

step_sub() {
    echo -e "        ${SUBTEXT}├─ ${1}${NC}"
}

step_success() {
    echo -e "        ${GREEN}${BOLD}✔${NC} ${SUBTEXT}${1}${NC}"
}

step_info() {
    echo -e "        ${BLUE}ℹ${NC} ${SUBTEXT}${1}${NC}"
}

step_warn() {
    echo -e "        ${YELLOW}⚠${NC} ${YELLOW}${1}${NC}"
}

step_error() {
    echo -e "        ${RED}✖${NC} ${RED}${1}${NC}"
}

print_banner() {
    echo -e "${PEACH}${BOLD}"
    echo "  ┌──────────────────────────────────────────────────────────────┐"
    echo "  │        Antigravity / Catppuccin Mocha Desktop Setup          │"
    echo "  │            Fast, Minimalist & Modern Arch Linux Rice         │"
    echo "  └──────────────────────────────────────────────────────────────┘"
    echo -e "${NC}"
}

print_help() {
    print_banner
    cat << EOF
Usage: ./install.sh [OPTIONS]

Options:
  -y, --yes, --unattended   Automatically accept all prompts without waiting
  -c, --configs-only        Deploy dotfiles, themes, and configs only (skip packages)
  --dry-run                 Simulate the installation without modifying system
  -h, --help                Show this help message and exit

Description:
  Automated setup and deployment suite for Arch Linux (and compatible distros).
  Deploys i3-wm, Polybar, Alacritty, Thunar, Zen Browser, Fastfetch, Starship,
  dynamic Catppuccin Mocha theming, lockscreen, and power management.
EOF
    exit 0
}

# ------------------------------------------------------------------------------
# Argument Parsing
# ------------------------------------------------------------------------------
NON_INTERACTIVE=false
CONFIGS_ONLY=false
DRY_RUN=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        -y|--yes|--unattended)
            NON_INTERACTIVE=true
            shift
            ;;
        -c|--configs-only)
            CONFIGS_ONLY=true
            shift
            ;;
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        -h|--help)
            print_help
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use ./install.sh --help for available options."
            exit 1
            ;;
    esac
done

# ------------------------------------------------------------------------------
# Root Safety Check
# ------------------------------------------------------------------------------
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}${BOLD}[✖] Error: Do not run this installer as root.${NC}"
    echo "    Configurations must be installed for your regular user."
    echo "    Sudo privileges will be requested automatically when required."
    exit 1
fi

print_banner

# ------------------------------------------------------------------------------
# Hardware & Environment Probing
# ------------------------------------------------------------------------------
DETECTED_OS="Unknown"
if [ -f /etc/os-release ]; then
    DETECTED_OS=$(grep -E '^PRETTY_NAME=' /etc/os-release | cut -d= -f2 | tr -d '"')
fi

DETECTED_GPU="Integrated / Generic"
if command -v lspci >/dev/null 2>&1; then
    if lspci | grep -Ei "vga|3d|display" | grep -iq "nvidia"; then
        DETECTED_GPU="NVIDIA"
    elif lspci | grep -Ei "vga|3d|display" | grep -iq "amd|radeon"; then
        DETECTED_GPU="AMD Radeon"
    elif lspci | grep -Ei "vga|3d|display" | grep -iq "intel"; then
        DETECTED_GPU="Intel Graphics"
    fi
fi

CHASSIS_TYPE="Desktop"
if [ -d /sys/class/power_supply ]; then
    if ls -d /sys/class/power_supply/BAT* >/dev/null 2>&1; then
        CHASSIS_TYPE="Laptop (Battery detected)"
    fi
fi

HOST_NAME="$(cat /etc/hostname 2>/dev/null || uname -n)"
echo -e "  ${BOLD}System Diagnosis:${NC}"
echo -e "    ${SUBTEXT}• User & Host : ${TEAL}${USER}@${HOST_NAME}${NC}"
echo -e "    ${SUBTEXT}• Operating Sys: ${BLUE}${DETECTED_OS}${NC}"
echo -e "    ${SUBTEXT}• Graphics GPU : ${PEACH}${DETECTED_GPU}${NC}"
echo -e "    ${SUBTEXT}• Form Factor  : ${LAVENDER}${CHASSIS_TYPE}${NC}"
echo -e "    ${SUBTEXT}• Dotfiles Dir : ${SUBTEXT}${DOTFILES_DIR}${NC}"
echo ""

# ------------------------------------------------------------------------------
# Interactive Confirmation
# ------------------------------------------------------------------------------
if [ "$NON_INTERACTIVE" = false ] && [ "$DRY_RUN" = false ]; then
    if [ -t 0 ] || [ -c /dev/tty ]; then
        echo -e -n "  ${BOLD}Ready to install Antigravity desktop suite? [Y/n]: ${NC}"
        read -r REPLY </dev/tty || REPLY="y"
        REPLY=${REPLY:-y}
        if [[ ! "$REPLY" =~ ^[Yy]$ ]]; then
            echo -e "\n  ${YELLOW}Installation cancelled by user.${NC}\n"
            exit 0
        fi
    fi
fi

if [ "$DRY_RUN" = true ]; then
    echo -e "  ${YELLOW}${BOLD}==> DRY RUN MODE: No changes will be written to disk.${NC}\n"
fi

# ------------------------------------------------------------------------------
# Sudo Authentication & Keep-Alive Loop
# ------------------------------------------------------------------------------
if [ "$CONFIGS_ONLY" = false ] && [ "$DRY_RUN" = false ]; then
    echo -e "  ${BLUE}${BOLD}==> Validating administrative privileges (sudo)...${NC}"
    sudo -v

    # Keep sudo timestamp active in background for long downloads
    while true; do
        sudo -n true
        sleep 50
        kill -0 "$$" || exit
    done 2>/dev/null &
    SUDO_KEEP_ALIVE_PID=$!
    trap 'kill $SUDO_KEEP_ALIVE_PID 2>/dev/null || true' EXIT INT TERM
fi

# ==============================================================================
# 1. Package Installation
# ==============================================================================
step_header "1/8" "📦 Package Manager & Desktop Environment"

if [ "$CONFIGS_ONLY" = true ]; then
    step_info "Configs-only mode active: skipping package installation."
elif [ "$DRY_RUN" = true ]; then
    step_info "Dry run: would install pacman packages and AUR dependencies."
elif command -v pacman >/dev/null 2>&1; then
    step_sub "Auditing legacy audio stacks (pulseaudio vs pipewire)..."
    CONFLICTING_AUDIO=$(pacman -Qq 2>/dev/null | grep -E '^(pulseaudio|jack2|pipewire-media-session)' || true)
    if [ -n "$CONFLICTING_AUDIO" ]; then
        step_warn "Removing conflicting legacy audio packages: $CONFLICTING_AUDIO"
        sudo pacman -Rdd --noconfirm $CONFLICTING_AUDIO 2>/dev/null || true
    fi

    step_sub "Optimizing /etc/pacman.conf (ParallelDownloads, Color, ILoveCandy)..."
    sudo sed -i 's/^#ParallelDownloads/ParallelDownloads/' /etc/pacman.conf 2>/dev/null || true
    sudo sed -i 's/^#Color/Color/' /etc/pacman.conf 2>/dev/null || true
    sudo sed -i 's/^#VerbosePkgLists/VerbosePkgLists/' /etc/pacman.conf 2>/dev/null || true
    grep -q "ILoveCandy" /etc/pacman.conf || sudo sed -i '/^Color/a ILoveCandy' /etc/pacman.conf 2>/dev/null || true

    PACMAN_PKGS=(
        base-devel
        git
        curl
        unzip
        which
        xorg-server
        xorg-xinit
        xorg-xrandr
        xorg-xmodmap
        xorg-xauth
        xorg-xrdb
        xorg-xwininfo
        xorg-xset
        xf86-input-libinput
        mesa
        i3-wm
        polybar
        alacritty
        picom
        rofi
        feh
        dunst
        libnotify
        pipewire
        pipewire-pulse
        pipewire-alsa
        wireplumber
        alsa-utils
        libpulse
        networkmanager
        bluez
        bluez-utils
        brightnessctl
        playerctl
        maim
        xclip
        xdotool
        xdg-utils
        thunar
        thunar-volman
        thunar-archive-plugin
        thunar-media-tags-plugin
        file-roller
        tumbler
        ffmpegthumbnailer
        poppler-glib
        webp-pixbuf-loader
        gvfs
        gvfs-mtp
        ranger
        mpv
        ncdu
        btop
        nvtop
        uv
        nano
        python
        ffmpeg
        ttf-jetbrains-mono-nerd
        otf-font-awesome
        noto-fonts-emoji
        starship
        fastfetch
        eza
        bat
        fzf
        zoxide
        ripgrep
        fd
        papirus-icon-theme
        gnome-themes-extra
        adw-gtk-theme
        xsettingsd
        xss-lock
        imagemagick
        ly
    )

    # Hardware-specific driver additions
    if [ "$DETECTED_GPU" = "NVIDIA" ]; then
        step_sub "Adding NVIDIA userspace utilities..."
        PACMAN_PKGS+=(nvidia-utils)
    elif [ "$DETECTED_GPU" = "AMD Radeon" ]; then
        step_sub "Adding AMD Vulkan and Xorg acceleration drivers..."
        PACMAN_PKGS+=(vulkan-radeon xf86-video-amdgpu)
    elif [ "$DETECTED_GPU" = "Intel Graphics" ]; then
        step_sub "Adding Intel Vulkan hardware acceleration drivers..."
        PACMAN_PKGS+=(vulkan-intel)
    fi

    step_sub "Installing packages via pacman..."
    if ! sudo pacman -Syu --needed --noconfirm "${PACMAN_PKGS[@]}"; then
        step_warn "Pacman requested manual confirmation. Retrying with controlling tty..."
        sudo pacman -Syu --needed "${PACMAN_PKGS[@]}" </dev/tty
    fi
    step_success "Arch Linux core desktop packages synchronized"

    # AUR Helper & AUR Packages
    if ! command -v yay >/dev/null 2>&1; then
        step_sub "Bootstrapping yay (AUR helper)..."
        TMP_YAY=$(mktemp -d)
        if git clone https://aur.archlinux.org/yay-bin.git "$TMP_YAY" 2>/dev/null || git clone https://aur.archlinux.org/yay.git "$TMP_YAY"; then
            (cd "$TMP_YAY" && makepkg -si --noconfirm) || true
        fi
        rm -rf "$TMP_YAY"
    fi

    if command -v yay >/dev/null 2>&1; then
        step_sub "Synchronizing AUR packages (i3lock-color, papirus-folders-catppuccin)..."
        yay -S --needed --noconfirm i3lock-color papirus-folders-catppuccin-git 2>/dev/null || true
        step_success "AUR packages installed"
    fi

    # Hardware permissions
    step_sub "Configuring hardware permissions for user '$USER'..."
    sudo usermod -a -G video,audio,input "$USER" 2>/dev/null || true

    # Disable conflicting display managers
    for dm in gdm sddm lightdm lxdm; do
        if systemctl is-enabled "$dm.service" >/dev/null 2>&1; then
            step_sub "Disabling conflicting display manager: $dm..."
            sudo systemctl disable "$dm.service" 2>/dev/null || true
        fi
    done

    # Enable core system services
    if command -v systemctl >/dev/null 2>&1; then
        step_sub "Enabling NetworkManager & Bluetooth daemons..."
        sudo systemctl enable NetworkManager.service 2>/dev/null || true
        sudo systemctl enable bluetooth.service 2>/dev/null || true
    fi

elif command -v apt >/dev/null 2>&1; then
    step_info "Debian / Ubuntu detected. Installing base packages..."
    if dpkg -l 2>/dev/null | grep -q "^ii\s*pulseaudio\s"; then
        sudo apt remove -y pulseaudio 2>/dev/null || true
    fi
    sudo apt update
    sudo apt install -y \
        xorg xinit x11-xserver-utils x11-xkb-utils i3 polybar alacritty picom rofi \
        feh dunst pipewire pipewire-pulse pipewire-alsa wireplumber alsa-utils pulseaudio-utils \
        network-manager bluez rfkill brightnessctl playerctl maim xclip xdotool xdg-utils \
        ranger mpv ncdu btop nvtop nano curl unzip git python3 ffmpeg fonts-font-awesome papirus-icon-theme
    step_success "Debian packages installed"

elif command -v dnf >/dev/null 2>&1; then
    step_info "Fedora detected. Installing base packages..."
    if rpm -q pulseaudio >/dev/null 2>&1; then
        sudo dnf swap -y pulseaudio pipewire-pulseaudio 2>/dev/null || true
    fi
    sudo dnf install -y \
        xorg-x11-server-Xorg xorg-x11-xinit i3 polybar alacritty picom rofi feh dunst \
        pipewire pipewire-pulseaudio wireplumber alsa-utils pulseaudio-utils NetworkManager \
        bluez bluez-tools brightnessctl playerctl maim xclip xdotool xdg-utils ranger mpv \
        ncdu btop nvtop nano curl unzip git python3 ffmpeg fontawesome-fonts papirus-icon-theme
    step_success "Fedora packages installed"
fi

# ==============================================================================
# 2. Typography & Fonts
# ==============================================================================
step_header "2/8" "🔤 JetBrainsMono Nerd Font & Icons"

if fc-list : family | grep -qi "JetBrainsMono Nerd Font"; then
    step_success "JetBrainsMono Nerd Font is already installed"
elif [ "$DRY_RUN" = true ]; then
    step_info "Dry run: would download JetBrainsMono Nerd Font"
else
    step_sub "Downloading JetBrainsMono Nerd Font from GitHub..."
    mkdir -p ~/.local/share/fonts/JetBrainsMono
    FONT_URL="https://github.com/ryanoasis/nerd-fonts/releases/latest/download/JetBrainsMono.zip"
    TMP_FONT_DIR="$(mktemp -d)"
    if curl -fsSL "$FONT_URL" -o "$TMP_FONT_DIR/JetBrainsMono.zip"; then
        unzip -qo "$TMP_FONT_DIR/JetBrainsMono.zip" -d ~/.local/share/fonts/JetBrainsMono
        fc-cache -f ~/.local/share/fonts
        step_success "Font installed and cache updated"
    fi
    rm -rf "$TMP_FONT_DIR"
fi

# ==============================================================================
# 3. Safe Configuration Backup
# ==============================================================================
step_header "3/8" "💾 Safe Configuration Backup"

BACKUP_DIR="$HOME/.config_backup_$(date +%Y%m%d_%H%M%S)"
if [ "$DRY_RUN" = true ]; then
    step_info "Dry run: would create backup at $BACKUP_DIR"
else
    mkdir -p "$BACKUP_DIR"
    BACKED_UP_COUNT=0
    for app in i3 polybar alacritty rofi picom dunst fastfetch zen Thunar; do
        if [ -d "$HOME/.config/$app" ] || [ -f "$HOME/.config/$app" ]; then
            cp -a "$HOME/.config/$app" "$BACKUP_DIR/" 2>/dev/null || true
            BACKED_UP_COUNT=$((BACKED_UP_COUNT + 1))
        fi
    done
    [ -f "$HOME/.nanorc" ] && cp "$HOME/.nanorc" "$BACKUP_DIR/" 2>/dev/null || true
    [ -f "$HOME/.bashrc" ] && cp "$HOME/.bashrc" "$BACKUP_DIR/" 2>/dev/null || true
    [ -f "$HOME/.xinitrc" ] && cp "$HOME/.xinitrc" "$BACKUP_DIR/" 2>/dev/null || true

    step_success "Saved $BACKED_UP_COUNT active configuration directories to: $BACKUP_DIR"
fi

# ==============================================================================
# 4. Dotfiles Deployment & Multi-Device Manager
# ==============================================================================
step_header "4/8" "🎨 Catppuccin Mocha Dotfiles & CLI Tools"

if [ "$DRY_RUN" = true ]; then
    step_info "Dry run: would copy dotfiles into ~/.config and configure ~/.local/bin"
else
    mkdir -p "$HOME/.config"
    cp -r "$DOTFILES_DIR/config/"* "$HOME/.config/"
    cp "$DOTFILES_DIR/home/.nanorc" "$HOME/.nanorc"
    [ -f "$DOTFILES_DIR/home/.bashrc" ] && cp "$DOTFILES_DIR/home/.bashrc" "$HOME/.bashrc"
    [ -f "$DOTFILES_DIR/home/.xinputrc" ] && cp "$DOTFILES_DIR/home/.xinputrc" "$HOME/.xinputrc"
    [ -f "$DOTFILES_DIR/home/.xinitrc" ] && cp "$DOTFILES_DIR/home/.xinitrc" "$HOME/.xinitrc"
    chmod +x "$HOME/.xinitrc" 2>/dev/null || true

    # Link CLI management utilities
    mkdir -p "$HOME/.local/bin"
    chmod +x "$DOTFILES_DIR/scripts/dotfiles"
    ln -sf "$DOTFILES_DIR/scripts/dotfiles" "$HOME/.local/bin/dotfiles"
    ln -sf "$DOTFILES_DIR/scripts/dotfiles" "$HOME/.local/bin/update-desktop"
    ln -sf "$DOTFILES_DIR/scripts/dotfiles" "$HOME/.local/bin/desktop-update"
    ln -sf "$DOTFILES_DIR/scripts/ori" "$HOME/.local/bin/ori" 2>/dev/null || true
    ln -sf "$DOTFILES_DIR/scripts/ori-window" "$HOME/.local/bin/ori-window" 2>/dev/null || true
    ln -sf "$HOME/.config/rofi/shortcuts.py" "$HOME/.local/bin/shortcuts-manager"

    # Ensure ~/.local/bin is in PATH for bash
    if [ -f "$HOME/.bashrc" ] && ! grep -q '\.local/bin' "$HOME/.bashrc"; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    fi

    # System-wide binary links if sudo permits
    if command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
        sudo ln -sf "$DOTFILES_DIR/scripts/dotfiles" "/usr/local/bin/update-desktop" 2>/dev/null || true
        sudo ln -sf "$DOTFILES_DIR/scripts/dotfiles" "/usr/local/bin/desktop-update" 2>/dev/null || true
        sudo ln -sf "$HOME/.config/rofi/shortcuts.py" "/usr/local/bin/shortcuts-manager" 2>/dev/null || true
    fi

    # Desktop Launchers
    mkdir -p "$HOME/.local/share/applications" "$HOME/.local/share/icons"
    [ -f "$DOTFILES_DIR/icons/ori.svg" ] && cp "$DOTFILES_DIR/icons/ori.svg" "$HOME/.local/share/icons/ori.svg"

    cat << EOF > "$HOME/.local/share/applications/ori.desktop"
[Desktop Entry]
Version=1.0
Type=Application
Name=Ori
GenericName=Local AI Assistant & System Co-Pilot
Comment=Autonomous Local AI Assistant for Linux System Monitoring & Modifications
Exec=$HOME/.local/bin/ori-window
Icon=$HOME/.local/share/icons/ori.svg
Terminal=false
Categories=Utility;System;Development;ArtificialIntelligence;
StartupNotify=true
StartupWMClass=FloatingOri
Keywords=ai;assistant;ollama;ori;system;monitor;plan;local;
EOF

    cat << EOF > "$HOME/.local/share/applications/wallpaper-picker.desktop"
[Desktop Entry]
Type=Application
Name=Wallpaper Selector
Comment=Change desktop wallpaper with Rofi or Visual Gallery
Exec=$HOME/.config/rofi/wallpaper.sh
Icon=preferences-desktop-wallpaper
Terminal=false
Categories=Utility;Settings;DesktopSettings;
Keywords=wallpaper;background;feh;catppuccin;
EOF

    # Wallpapers
    mkdir -p "$HOME/Pictures/Wallpapers"
    cp -r "$DOTFILES_DIR/wallpapers/"* "$HOME/Pictures/Wallpapers/"

    # Custom Icons
    if [ -d "$DOTFILES_DIR/icons" ]; then
        mkdir -p "$HOME/.local/share/icons/hicolor/scalable/apps"
        cp -r "$DOTFILES_DIR/icons/"* "$HOME/.local/share/icons/" 2>/dev/null || true
        cp -r "$DOTFILES_DIR/icons/"*.svg "$HOME/.local/share/icons/hicolor/scalable/apps/" 2>/dev/null || true
        command -v gtk-update-icon-cache >/dev/null 2>&1 && gtk-update-icon-cache "$HOME/.local/share/icons/hicolor" 2>/dev/null || true
    fi

    # Make scripts executable
    chmod +x "$HOME/.config/polybar/launch.sh" 2>/dev/null || true
    chmod +x "$HOME/.config/polybar/scripts/"*.sh 2>/dev/null || true
    chmod +x "$HOME/.config/dunst/launch.sh" 2>/dev/null || true
    chmod +x "$HOME/.config/dunst/scripts/"*.sh 2>/dev/null || true
    chmod +x "$HOME/.config/rofi/"*.sh "$HOME/.config/rofi/"*.py 2>/dev/null || true
    chmod +x "$HOME/.config/theme/apply-theme.sh" 2>/dev/null || true
    chmod +x "$HOME/.config/i3/screenshot.sh" "$HOME/.config/i3/lock.sh" 2>/dev/null || true
    chmod +x "$HOME/.config/zen/setup-zen.sh" 2>/dev/null || true

    step_success "Configurations and helper scripts deployed with executable permissions"
fi

# ==============================================================================
# 5. Zen Browser Custom Integration
# ==============================================================================
step_header "5/8" "🌐 Zen Browser Custom Integration"

if [ "$DRY_RUN" = true ]; then
    step_info "Dry run: would run setup-zen.sh"
elif [ -x "$HOME/.config/zen/setup-zen.sh" ]; then
    step_sub "Configuring Zen Browser profile and Catppuccin Mocha userChrome.css..."
    "$HOME/.config/zen/setup-zen.sh" 2>/dev/null || true
    step_success "Zen Browser enterprise policies and theme configured"
fi

if command -v uv >/dev/null 2>&1 && [ "$DRY_RUN" = false ]; then
    uv tool install nvitop 2>/dev/null || true
fi

# ==============================================================================
# 6. Sudo Asterisk Feedback & Security
# ==============================================================================
step_header "6/8" "🔐 Sudo Password Feedback & Security"

if [ "$CONFIGS_ONLY" = true ]; then
    step_info "Configs-only mode active: skipping /etc/sudoers.d modification."
elif [ "$DRY_RUN" = true ]; then
    step_info "Dry run: would deploy /etc/sudoers.d/01_pwfeedback"
elif [ -f "$DOTFILES_DIR/etc/sudoers.d/01_pwfeedback" ] && sudo -n true 2>/dev/null; then
    step_sub "Deploying visual asterisk feedback ('*') in terminal sudo prompts..."
    sudo mkdir -p /etc/sudoers.d
    sudo cp "$DOTFILES_DIR/etc/sudoers.d/01_pwfeedback" /etc/sudoers.d/01_pwfeedback
    sudo chmod 0440 /etc/sudoers.d/01_pwfeedback
    if sudo visudo -c >/dev/null 2>&1; then
        step_success "Visual feedback enabled for sudo password input"
    else
        sudo rm -f /etc/sudoers.d/01_pwfeedback
        step_warn "Sudoers validation failed, reverted safely."
    fi
fi

# ==============================================================================
# 7. Theme Initialization & Lockscreen Cache
# ==============================================================================
step_header "7/8" "🖼️  Wallpaper & Dynamic Accent Theme"

if [ "$DRY_RUN" = true ]; then
    step_info "Dry run: would apply wallpaper and generate lockscreen cache"
else
    # Set Papirus Catppuccin folders if available and root access is cached
    if command -v papirus-folders >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
        papirus-folders -C cat-mocha-peach --theme Papirus-Dark 2>/dev/null || true
    fi

    # Initialize wallpaper & dynamic theme
    DEFAULT_WALLPAPER="$HOME/Pictures/Wallpapers/waves_dark.jpg"
    [ ! -f "$DEFAULT_WALLPAPER" ] && DEFAULT_WALLPAPER="$HOME/Pictures/Wallpapers/wavy_lines.png"

    if [ -x "$HOME/.config/theme/apply-theme.sh" ] && [ -f "$DEFAULT_WALLPAPER" ]; then
        step_sub "Applying wallpaper and generating dynamic theme..."
        "$HOME/.config/theme/apply-theme.sh" "$DEFAULT_WALLPAPER" 2>/dev/null || true
        step_success "Wallpaper applied and lockscreen cache initialized"
    elif [ -f "$DEFAULT_WALLPAPER" ]; then
        cat << EOF > "$HOME/.fehbg"
#!/bin/sh
feh --no-fehbg --bg-fill "$DEFAULT_WALLPAPER"
EOF
        chmod +x "$HOME/.fehbg"
        [ -n "$DISPLAY" ] && "$HOME/.fehbg" 2>/dev/null || true
    fi
fi

# ==============================================================================
# 8. Display Manager & Services
# ==============================================================================
step_header "8/8" "🚀 Ly Display Manager & Boot Targets"

if [ "$CONFIGS_ONLY" = true ]; then
    step_info "Configs-only mode active: skipping display manager system configuration."
elif [ "$DRY_RUN" = true ]; then
    step_info "Dry run: would configure Ly display manager service"
elif command -v ly >/dev/null 2>&1 || command -v ly-dm >/dev/null 2>&1; then
    step_sub "Configuring Ly Display Manager..."
    sudo mkdir -p /etc/ly
    [ -f "$DOTFILES_DIR/config/ly/config.ini" ] && sudo cp "$DOTFILES_DIR/config/ly/config.ini" /etc/ly/config.ini 2>/dev/null || true
    [ -f "$DOTFILES_DIR/config/ly/config.lua" ] && sudo cp "$DOTFILES_DIR/config/ly/config.lua" /etc/ly/config.lua 2>/dev/null || true

    if command -v systemctl >/dev/null 2>&1; then
        sudo systemctl set-default graphical.target 2>/dev/null || true
        if systemctl list-unit-files 'ly@*.service' 2>/dev/null | grep -q "ly@"; then
            sudo systemctl disable getty@tty2.service 2>/dev/null || true
            sudo systemctl enable ly@tty2.service 2>/dev/null || true
        elif systemctl list-unit-files ly.service 2>/dev/null | grep -q "ly.service"; then
            sudo systemctl enable ly.service 2>/dev/null || true
        else
            sudo systemctl disable getty@tty2.service 2>/dev/null || true
            sudo systemctl enable ly@tty2.service 2>/dev/null || sudo systemctl enable ly.service 2>/dev/null || true
        fi
        step_success "Ly display manager enabled on boot (graphical.target)"
    fi
fi

# ==============================================================================
# Installation Complete Summary
# ==============================================================================
echo ""
echo -e "${GREEN}${BOLD}  ┌──────────────────────────────────────────────────────────────┐${NC}"
echo -e "${GREEN}${BOLD}  │                   ✔ Installation Completed!                  │${NC}"
echo -e "${GREEN}${BOLD}  │      All components have been configured and synchronized    │${NC}"
echo -e "${GREEN}${BOLD}  └──────────────────────────────────────────────────────────────┘${NC}"
echo ""
echo -e "  ${BOLD}Installed Suite Components:${NC}"
echo -e "    ${SUBTEXT}• Window Manager : ${BLUE}i3-wm${NC} ${SUBTEXT}(0px square borders, Catppuccin Mocha)${NC}"
echo -e "    ${SUBTEXT}• Status Bar     : ${PEACH}Polybar${NC} ${SUBTEXT}(Dynamic accent, interactive applets)${NC}"
echo -e "    ${SUBTEXT}• Terminal Suite : ${MAUVE}Alacritty${NC} ${SUBTEXT}+ Fastfetch + Starship + eza/bat/fzf/zoxide${NC}"
echo -e "    ${SUBTEXT}• File Manager   : ${TEAL}Thunar${NC} ${SUBTEXT}(0px square borders, Papirus Catppuccin icons)${NC}"
echo -e "    ${SUBTEXT}• Web Browser    : ${LAVENDER}Zen Browser${NC} ${SUBTEXT}(Catppuccin Mocha theme, square tabs)${NC}"
echo -e "    ${SUBTEXT}• Idle & Locking : ${YELLOW}i3lock-color${NC} ${SUBTEXT}(xss-lock, DPMS sleep 10m/15m/20m)${NC}"
echo -e "    ${SUBTEXT}• Display Manager: ${GREEN}Ly${NC} ${SUBTEXT}(Minimalist TUI login on tty2)${NC}"
echo ""
echo -e "  ${BOLD}Essential Keyboard Shortcuts:${NC}"
echo -e "    ${BOLD}Super + Return${NC}         ${SUBTEXT}→ Terminal (Alacritty)${NC}"
echo -e "    ${BOLD}Super + F2 / Ctrl+b${NC}    ${SUBTEXT}→ Web Browser (Zen Browser)${NC}"
echo -e "    ${BOLD}Super + Shift + Return${NC} ${SUBTEXT}→ File Manager (Thunar)${NC}"
echo -e "    ${BOLD}Super + d${NC}              ${SUBTEXT}→ Application Launcher (Rofi)${NC}"
echo -e "    ${BOLD}Super + /${NC}              ${SUBTEXT}→ Keybindings Cheatsheet (Rofi)${NC}"
echo -e "    ${BOLD}Super + Ctrl + l${NC}       ${SUBTEXT}→ Lock Desktop Session${NC}"
echo -e "    ${BOLD}Super + Shift + e${NC}      ${SUBTEXT}→ Power Menu (Sleep/Reboot/Shutdown)${NC}"
echo ""
echo -e "  ${BOLD}Multi-Device Maintenance:${NC}"
echo -e "    ${SUBTEXT}• Update local PC from GitHub : ${TEAL}update-desktop${NC} or ${TEAL}dotfiles pull${NC}"
echo -e "    ${SUBTEXT}• Push local tweaks to GitHub : ${TEAL}dotfiles push \"message\"${NC}"
echo -e "    ${SUBTEXT}• Check sync status           : ${TEAL}dotfiles status${NC}"
echo ""

# Interactive next step
if [ -n "$DISPLAY" ]; then
    if [ "$NON_INTERACTIVE" = false ] && [ "$DRY_RUN" = false ] && ([ -t 0 ] || [ -c /dev/tty ]); then
        echo -e -n "  ${BOLD}Reload desktop environment now? [Y/n]: ${NC}"
        read -r RELOAD </dev/tty || RELOAD="y"
        REPLY=${RELOAD:-y}
        if [[ "$REPLY" =~ ^[Yy]$ ]]; then
            i3-msg reload >/dev/null 2>&1 || true
            "$HOME/.config/polybar/launch.sh" >/dev/null 2>&1 || true
            dunstctl reload >/dev/null 2>&1 || true
            echo -e "  ${GREEN}✔ Desktop reloaded successfully!${NC}\n"
        fi
    fi
else
    echo -e "  ${PEACH}To start your session now, run: ${BOLD}startx${NC} or reboot to let Ly handle it."
    echo ""
fi
