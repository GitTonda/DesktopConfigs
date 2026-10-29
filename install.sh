#!/usr/bin/env bash
# ==============================================================================
# Antigravity / Catppuccin Mocha Desktop Setup Suite
# Fast, Minimalist, High-Performance Linux Desktop Experience
# ==============================================================================

set -e

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
START_TIME=$(date +%s)

# ------------------------------------------------------------------------------
# Catppuccin Mocha Palette (Truecolor ANSI 24-bit)
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
DIM='\033[2m'
NC='\033[0m' # Reset

# ------------------------------------------------------------------------------
# Fluid Terminal Spinner & Task Runner
# ------------------------------------------------------------------------------
run_task() {
    local msg="$1"
    shift
    if [ -t 1 ] && [ "$NON_INTERACTIVE" = false ]; then
        "$@" >/dev/null 2>&1 &
        local pid=$!
        local spin="⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        while kill -0 "$pid" 2>/dev/null; do
            for (( i=0; i<${#spin}; i++ )); do
                printf "\r  ${PEACH}%s${NC} ${SUBTEXT}%s...${NC}" "${spin:$i:1}" "$msg"
                sleep 0.05
                kill -0 "$pid" 2>/dev/null || break
            done
        done
        wait "$pid"
        local exit_code=$?
        if [ $exit_code -eq 0 ]; then
            printf "\r  ${GREEN}${BOLD}✔${NC} ${SUBTEXT}%s${NC}\033[K\n" "$msg"
        else
            printf "\r  ${RED}${BOLD}✖${NC} ${RED}%s (failed)${NC}\033[K\n" "$msg"
        fi
        return $exit_code
    else
        "$@" >/dev/null 2>&1
        local exit_code=$?
        if [ $exit_code -eq 0 ]; then
            echo -e "  ${GREEN}✔${NC} ${SUBTEXT}${msg}${NC}"
        else
            echo -e "  ${RED}✖${NC} ${RED}${msg} (failed)${NC}"
        fi
        return $exit_code
    fi
}

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

print_banner() {
    echo ""
    echo -e "${MAUVE}      ___         __  _                        _  __           ${NC}"
    echo -e "${BLUE}     /   |  ____ / /_(_)___ __________ __   __(_)/ /___  __    ${NC}"
    echo -e "${TEAL}    / /| | / __ \\/ __/ / __ \`/ ___/ __ \`/ | / / / __/ / / /    ${NC}"
    echo -e "${GREEN}   / ___ |/ / / / /_/ / /_/ / /  / /_/ /| |/ / / /_/ /_/ /     ${NC}"
    echo -e "${PEACH}  /_/  |_/_/ /_/\\__/_/\\__, /_/   \\__,_/ |___/_/\\__/\\__, /      ${NC}"
    echo -e "${PEACH}                     /____/                       /____/       ${NC}"
    echo ""
    echo -e "  ${SURFACE}┌─────────────────────────────────────────────────────────────┐${NC}"
    echo -e "  ${SURFACE}│${NC}  ${BOLD}⚡ ANTIGRAVITY OS${NC} ${SUBTEXT}·${NC} ${PEACH}Catppuccin Mocha Arch Linux Rice${NC}       ${SURFACE}│${NC}"
    echo -e "  ${SURFACE}│${NC}  ${TEAL}◆${NC} ${SUBTEXT}i3-wm${NC}   ${BLUE}◇${NC} ${SUBTEXT}Polybar${NC}   ${MAUVE}◆${NC} ${SUBTEXT}Fastfetch${NC}   ${PEACH}◇${NC} ${SUBTEXT}Zen${NC}   ${GREEN}◆${NC} ${SUBTEXT}0px Borders${NC}       ${SURFACE}│${NC}"
    echo -e "  ${SURFACE}└─────────────────────────────────────────────────────────────┘${NC}"
    echo ""
}

print_help() {
    print_banner
    cat << EOF
Usage: ./install.sh [OPTIONS]

Options:
  -y, --yes, --unattended   Non-interactive mode (auto-accept all prompts)
  -c, --configs-only        Synchronize dotfiles, themes, & fonts only (skip packages)
  --dry-run                 Run simulation mode without writing modifications to disk
  -h, --help                Display this cheat-sheet and exit

Description:
  High-performance installer suite for Arch Linux and compatible distros.
  Configures i3wm, Polybar, Alacritty, Thunar, Zen Browser, Fastfetch, Starship,
  dynamic wallpaper-driven Catppuccin Mocha styling, and idle lock management.
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
    echo -e "${RED}${BOLD}[✖] Error: Do not execute this installer as root.${NC}"
    echo "    Configurations must be deployed in your standard user environment."
    echo "    Elevated sudo privileges are requested automatically when needed."
    exit 1
fi

print_banner

# ------------------------------------------------------------------------------
# System Telemetry & Hardware Probing
# ------------------------------------------------------------------------------
HOST_NAME="$(cat /etc/hostname 2>/dev/null || uname -n)"
KERNEL="$(uname -r)"
CPU_MODEL=$(grep -m1 "model name" /proc/cpuinfo 2>/dev/null | cut -d: -f2 | sed -E "s/^[ \t]+//; s/\(R\)|\(TM\)//g; s/CPU //g; s/@.*//g" || echo "Generic CPU")
RAM_STATS=$(free -h 2>/dev/null | awk '/^Mem:/ {print $3 "/" $2}')
DISK_STATS=$(df -h / 2>/dev/null | awk 'NR==2 {print $3 "/" $2 " (" $5 ")"}')

DETECTED_GPU="Integrated / Generic"
if command -v lspci >/dev/null 2>&1; then
    if lspci | grep -Ei "vga|3d|display" | grep -iq "nvidia"; then
        DETECTED_GPU="NVIDIA Dedicated"
    elif lspci | grep -Ei "vga|3d|display" | grep -iq "amd|radeon"; then
        DETECTED_GPU="AMD Radeon"
    elif lspci | grep -Ei "vga|3d|display" | grep -iq "intel"; then
        DETECTED_GPU="Intel Iris / UHD"
    fi
fi

CHASSIS_TYPE="Desktop"
if [ -d /sys/class/power_supply ]; then
    if ls -d /sys/class/power_supply/BAT* >/dev/null 2>&1; then
        BAT_CAP="$(cat /sys/class/power_supply/BAT*/capacity 2>/dev/null | head -n1 || true)"
        CHASSIS_TYPE="Laptop (${BAT_CAP:-100}% Bat)"
    fi
fi

DISPLAY_RES="Headless / TTY"
if [ -n "$DISPLAY" ] && command -v xrandr >/dev/null 2>&1; then
    CURRENT_RES="$(xrandr --current 2>/dev/null | grep '\*' | awk '{print $1}' | head -n1 || true)"
    [ -n "$CURRENT_RES" ] && DISPLAY_RES="${CURRENT_RES} (X11)"
fi

echo -e "  ${SURFACE}┌── ${PEACH}${BOLD}SYSTEM TELEMETRY${NC} ${SURFACE}─────────────────────────────────────────┐${NC}"
printf "  ${SURFACE}│${NC}  ${SUBTEXT}%-9s${NC} ${BOLD}%-23s${NC} ${SUBTEXT}%-8s${NC} ${TEAL}%-18s${NC} ${SURFACE}│${NC}\n" "Host" "${USER}@${HOST_NAME}" "Kernel" "$KERNEL"
printf "  ${SURFACE}│${NC}  ${SUBTEXT}%-9s${NC} ${BOLD}%-23s${NC} ${SUBTEXT}%-8s${NC} ${GREEN}%-18s${NC} ${SURFACE}│${NC}\n" "CPU" "${CPU_MODEL:0:23}" "Memory" "$RAM_STATS"
printf "  ${SURFACE}│${NC}  ${SUBTEXT}%-9s${NC} ${BLUE}%-23s${NC} ${SUBTEXT}%-8s${NC} ${MAUVE}%-18s${NC} ${SURFACE}│${NC}\n" "GPU" "$DETECTED_GPU" "Disk (/)" "$DISK_STATS"
printf "  ${SURFACE}│${NC}  ${SUBTEXT}%-9s${NC} ${PEACH}%-23s${NC} ${SUBTEXT}%-8s${NC} ${BLUE}%-18s${NC} ${SURFACE}│${NC}\n" "Chassis" "$CHASSIS_TYPE" "Display" "$DISPLAY_RES"
echo -e "  ${SURFACE}└─────────────────────────────────────────────────────────────┘${NC}"
echo ""

# ------------------------------------------------------------------------------
# Interactive Confirmation
# ------------------------------------------------------------------------------
if [ "$NON_INTERACTIVE" = false ] && [ "$DRY_RUN" = false ]; then
    if [ -t 0 ] || [ -c /dev/tty ]; then
        echo -e -n "  ${BOLD}Ready to execute Antigravity desktop setup? [Y/n]: ${NC}"
        read -r REPLY </dev/tty || REPLY="y"
        REPLY=${REPLY:-y}
        if [[ ! "$REPLY" =~ ^[Yy]$ ]]; then
            echo -e "\n  ${YELLOW}Setup cancelled by user.${NC}\n"
            exit 0
        fi
    fi
fi

if [ "$DRY_RUN" = true ]; then
    echo -e "  ${YELLOW}${BOLD}==> DRY RUN MODE: Execution simulated. Zero disk modifications.${NC}\n"
fi

# ------------------------------------------------------------------------------
# Sudo Session Keep-Alive Loop (Zero Interruptions)
# ------------------------------------------------------------------------------
if [ "$CONFIGS_ONLY" = false ] && [ "$DRY_RUN" = false ]; then
    if ! sudo -n true 2>/dev/null; then
        echo -e "  ${BLUE}${BOLD}==> Requesting administrative authorization (sudo)...${NC}"
        sudo -v
    fi

    # Keep authorization token alive in background until installer terminates
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
    step_info "Configs-only mode enabled: bypassing system package synchronization."
elif [ "$DRY_RUN" = true ]; then
    step_info "Dry run: would audit conflicts, optimize pacman, and install packages."
elif command -v pacman >/dev/null 2>&1; then
    # Clean any legacy conflicting audio packages
    CONFLICTING_AUDIO=$(pacman -Qq 2>/dev/null | grep -E '^(pulseaudio|jack2|pipewire-media-session)' || true)
    if [ -n "$CONFLICTING_AUDIO" ]; then
        step_warn "Purging conflicting legacy audio packages: $CONFLICTING_AUDIO"
        sudo pacman -Rdd --noconfirm $CONFLICTING_AUDIO 2>/dev/null || true
    fi

    # Optimize pacman.conf for multi-threaded speed & candy
    if grep -q "^#ParallelDownloads" /etc/pacman.conf || ! grep -q "ILoveCandy" /etc/pacman.conf; then
        step_sub "Optimizing /etc/pacman.conf (ParallelDownloads = 8, Color, ILoveCandy)..."
        sudo sed -i 's/^#ParallelDownloads.*/ParallelDownloads = 8/' /etc/pacman.conf 2>/dev/null || true
        sudo sed -i 's/^#Color/Color/' /etc/pacman.conf 2>/dev/null || true
        sudo sed -i 's/^#VerbosePkgLists/VerbosePkgLists/' /etc/pacman.conf 2>/dev/null || true
        grep -q "ILoveCandy" /etc/pacman.conf || sudo sed -i '/^Color/a ILoveCandy' /etc/pacman.conf 2>/dev/null || true
    fi

    PACMAN_PKGS=(
        base-devel git curl unzip which
        xorg-server xorg-xinit xorg-xrandr xorg-xmodmap xorg-xauth xorg-xrdb xorg-xwininfo xorg-xset xf86-input-libinput
        mesa i3-wm polybar alacritty picom rofi feh dunst libnotify
        pipewire pipewire-pulse pipewire-alsa wireplumber alsa-utils libpulse
        networkmanager bluez bluez-utils brightnessctl playerctl maim xclip xdotool xdg-utils
        thunar thunar-volman thunar-archive-plugin thunar-media-tags-plugin file-roller tumbler ffmpegthumbnailer poppler-glib webp-pixbuf-loader gvfs gvfs-mtp
        ranger mpv ncdu btop nvtop uv nano python ffmpeg
        ttf-jetbrains-mono-nerd otf-font-awesome noto-fonts-emoji
        starship fastfetch eza bat fzf zoxide ripgrep fd
        papirus-icon-theme gnome-themes-extra adw-gtk-theme xsettingsd xss-lock imagemagick pacman-contrib ly
        python-gobject gtk3
    )

    # Hardware acceleration driver additions
    if [ "$DETECTED_GPU" = "NVIDIA Dedicated" ]; then
        step_sub "Hardware Acceleration: Adding NVIDIA user utilities..."
        PACMAN_PKGS+=(nvidia-utils)
    elif [ "$DETECTED_GPU" = "AMD Radeon" ]; then
        step_sub "Hardware Acceleration: Adding AMD Vulkan and Xorg drivers..."
        PACMAN_PKGS+=(vulkan-radeon xf86-video-amdgpu)
    elif [ "$DETECTED_GPU" = "Intel Iris / UHD" ]; then
        step_sub "Hardware Acceleration: Adding Intel Vulkan drivers..."
        PACMAN_PKGS+=(vulkan-intel)
    fi

    step_sub "Synchronizing packages via Pacman..."
    if ! sudo pacman -Syu --needed --noconfirm "${PACMAN_PKGS[@]}"; then
        step_warn "Pacman interactive prompt required. Connecting to tty..."
        sudo pacman -Syu --needed "${PACMAN_PKGS[@]}" </dev/tty
    fi
    step_success "Arch Linux core desktop suite synchronized"

    # AUR Helper bootstrap (if missing)
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

    # Hardware permissions and groups
    step_sub "Configuring hardware permissions for user '$USER'..."
    sudo usermod -a -G video,audio,input "$USER" 2>/dev/null || true

    # Disable conflicting legacy display managers
    for dm in gdm sddm lightdm lxdm; do
        if systemctl is-enabled "$dm.service" >/dev/null 2>&1; then
            step_sub "Disabling conflicting display manager: $dm..."
            sudo systemctl disable "$dm.service" 2>/dev/null || true
        fi
    done

    # Enable essential systemd services & maintenance timers
    if command -v systemctl >/dev/null 2>&1; then
        sudo systemctl enable NetworkManager.service 2>/dev/null || true
        sudo systemctl enable bluetooth.service 2>/dev/null || true
        sudo systemctl enable fstrim.timer 2>/dev/null || true
        sudo systemctl enable paccache.timer 2>/dev/null || true
        step_success "NetworkManager, Bluetooth & SSD/Cache maintenance timers enabled"
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

if [ -d "$HOME/.local/share/fonts/JetBrainsMono" ] || fc-list : family | grep -qi "JetBrainsMono Nerd Font"; then
    step_success "JetBrainsMono Nerd Font is verified and active"
elif [ "$DRY_RUN" = true ]; then
    step_info "Dry run: would retrieve JetBrainsMono Nerd Font"
else
    install_fonts() {
        mkdir -p "$HOME/.local/share/fonts/JetBrainsMono"
        local font_url="https://github.com/ryanoasis/nerd-fonts/releases/latest/download/JetBrainsMono.zip"
        local tmp_font="$(mktemp -d)"
        if curl -fsSL "$font_url" -o "$tmp_font/JetBrainsMono.zip"; then
            unzip -qo "$tmp_font/JetBrainsMono.zip" -d "$HOME/.local/share/fonts/JetBrainsMono"
            fc-cache -f "$HOME/.local/share/fonts"
        fi
        rm -rf "$tmp_font"
    }
    run_task "Downloading and compiling JetBrainsMono Nerd Font cache" install_fonts
fi

# ==============================================================================
# 3. Safe Configuration Backup
# ==============================================================================
step_header "3/8" "💾 Safe Configuration Backup"

BACKUP_DIR="$HOME/.config_backup_$(date +%Y%m%d_%H%M%S)"
if [ "$DRY_RUN" = true ]; then
    step_info "Dry run: would create backup archive at $BACKUP_DIR"
else
    backup_existing_configs() {
        mkdir -p "$BACKUP_DIR"
        for app in i3 polybar alacritty rofi picom dunst fastfetch zen Thunar xsettingsd control-center; do
            if [ -d "$HOME/.config/$app" ] || [ -f "$HOME/.config/$app" ]; then
                cp -a "$HOME/.config/$app" "$BACKUP_DIR/" 2>/dev/null || true
            fi
        done
        [ -f "$HOME/.nanorc" ] && cp "$HOME/.nanorc" "$BACKUP_DIR/" 2>/dev/null || true
        [ -f "$HOME/.bashrc" ] && cp "$HOME/.bashrc" "$BACKUP_DIR/" 2>/dev/null || true
        [ -f "$HOME/.xinitrc" ] && cp "$HOME/.xinitrc" "$BACKUP_DIR/" 2>/dev/null || true
    }
    run_task "Backing up active configuration profiles" backup_existing_configs
    step_info "Backup safely stored in: ${SUBTEXT}${BACKUP_DIR}${NC}"
fi

# ==============================================================================
# 4. Dotfiles Deployment & Multi-Device Manager
# ==============================================================================
step_header "4/8" "🎨 Catppuccin Mocha Dotfiles & CLI Tools"

if [ "$DRY_RUN" = true ]; then
    step_info "Dry run: would deploy dotfiles into ~/.config and wire CLI tools"
else
    deploy_dotfiles() {
        mkdir -p "$HOME/.config"
        cp -r "$DOTFILES_DIR/config/"* "$HOME/.config/"
        cp "$DOTFILES_DIR/home/.nanorc" "$HOME/.nanorc"
        [ -f "$DOTFILES_DIR/home/.bashrc" ] && cp "$DOTFILES_DIR/home/.bashrc" "$HOME/.bashrc"
        [ -f "$DOTFILES_DIR/home/.xinputrc" ] && cp "$DOTFILES_DIR/home/.xinputrc" "$HOME/.xinputrc"
        [ -f "$DOTFILES_DIR/home/.xinitrc" ] && cp "$DOTFILES_DIR/home/.xinitrc" "$HOME/.xinitrc"
        chmod +x "$HOME/.xinitrc" 2>/dev/null || true

        # Link CLI management tools
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

        cat << 'EOF' > "$HOME/.local/share/applications/ori.desktop"
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

        cat << 'EOF' > "$HOME/.local/share/applications/wallpaper-picker.desktop"
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

        # Optimized batch permission configuration
        chmod +x \
            "$HOME/.config/polybar/launch.sh" "$HOME/.config/polybar/scripts/"*.sh \
            "$HOME/.config/dunst/launch.sh" "$HOME/.config/dunst/scripts/"*.sh \
            "$HOME/.config/rofi/"*.sh "$HOME/.config/rofi/"*.py \
            "$HOME/.config/control-center/"*.sh "$HOME/.config/control-center/"*.py \
            "$HOME/.config/theme/"*.sh "$HOME/.config/i3/"*.sh \
            "$HOME/.config/zen/setup-zen.sh" "$DOTFILES_DIR/scripts/"* 2>/dev/null || true
    }
    run_task "Deploying Catppuccin Mocha configurations & CLI tools" deploy_dotfiles
fi

# ==============================================================================
# 5. Zen Browser Custom Integration
# ==============================================================================
step_header "5/8" "🌐 Zen Browser Custom Integration"

if [ "$DRY_RUN" = true ]; then
    step_info "Dry run: would synchronize Zen Browser profile and userChrome.css"
elif [ -x "$HOME/.config/zen/setup-zen.sh" ]; then
    run_task "Configuring Zen Browser profile and square userChrome.css" "$HOME/.config/zen/setup-zen.sh"
fi

if command -v uv >/dev/null 2>&1 && [ "$DRY_RUN" = false ]; then
    uv tool install nvitop 2>/dev/null || true
fi

# ==============================================================================
# 6. Sudo Asterisk Feedback & Security
# ==============================================================================
step_header "6/8" "🔐 Sudo Password Feedback & Security"

if [ "$CONFIGS_ONLY" = true ]; then
    step_info "Configs-only mode enabled: bypassing /etc/sudoers.d modification."
elif [ "$DRY_RUN" = true ]; then
    step_info "Dry run: would deploy /etc/sudoers.d/01_pwfeedback"
elif [ -f "$DOTFILES_DIR/etc/sudoers.d/01_pwfeedback" ] && sudo -n true 2>/dev/null; then
    configure_pwfeedback() {
        sudo mkdir -p /etc/sudoers.d
        sudo cp "$DOTFILES_DIR/etc/sudoers.d/01_pwfeedback" /etc/sudoers.d/01_pwfeedback
        sudo chmod 0440 /etc/sudoers.d/01_pwfeedback
        if ! sudo visudo -c >/dev/null 2>&1; then
            sudo rm -f /etc/sudoers.d/01_pwfeedback
            return 1
        fi

        # Deploy kernel sysctl performance optimizations
        if [ -f "$DOTFILES_DIR/etc/sysctl.d/99-performance.conf" ]; then
            sudo mkdir -p /etc/sysctl.d
            sudo cp "$DOTFILES_DIR/etc/sysctl.d/99-performance.conf" /etc/sysctl.d/99-performance.conf
            sudo sysctl --system >/dev/null 2>&1 || true
        fi

        # Deploy systemd journal log capping
        if [ -f "$DOTFILES_DIR/etc/systemd/journald.conf.d/00-journal-size.conf" ]; then
            sudo mkdir -p /etc/systemd/journald.conf.d
            sudo cp "$DOTFILES_DIR/etc/systemd/journald.conf.d/00-journal-size.conf" /etc/systemd/journald.conf.d/00-journal-size.conf
            sudo systemctl restart systemd-journald 2>/dev/null || true
        fi
    }
    run_task "Enabling visual password feedback & kernel performance tuning" configure_pwfeedback
fi

# ==============================================================================
# 7. Theme Initialization & Lockscreen Cache
# ==============================================================================
step_header "7/8" "🖼️  Wallpaper & Dynamic Accent Theme"

if [ "$DRY_RUN" = true ]; then
    step_info "Dry run: would apply wallpaper and generate blurred lockscreen"
else
    init_theming() {
        # Configure Papirus Catppuccin folders if root permit cached
        if command -v papirus-folders >/dev/null 2>&1 && sudo -n true 2>/dev/null; then
            papirus-folders -C cat-mocha-peach --theme Papirus-Dark 2>/dev/null || true
        fi

        local default_wallpaper="$HOME/Pictures/Wallpapers/waves_dark.jpg"
        [ ! -f "$default_wallpaper" ] && default_wallpaper="$HOME/Pictures/Wallpapers/wavy_lines.png"

        if [ -x "$HOME/.config/theme/apply-theme.sh" ] && [ -f "$default_wallpaper" ]; then
            "$HOME/.config/theme/apply-theme.sh" "$default_wallpaper" 2>/dev/null || true
        elif [ -f "$default_wallpaper" ]; then
            cat << EOF > "$HOME/.fehbg"
#!/bin/sh
feh --no-fehbg --bg-fill "$default_wallpaper"
EOF
            chmod +x "$HOME/.fehbg"
            [ -n "$DISPLAY" ] && "$HOME/.fehbg" 2>/dev/null || true
        fi
    }
    run_task "Initializing wallpaper palette & lockscreen blur cache" init_theming
fi

# ==============================================================================
# 8. Display Manager & Services
# ==============================================================================
step_header "8/8" "🚀 Ly Display Manager & Boot Targets"

if [ "$CONFIGS_ONLY" = true ]; then
    step_info "Configs-only mode enabled: bypassing display manager system service."
elif [ "$DRY_RUN" = true ]; then
    step_info "Dry run: would configure Ly display manager service"
elif command -v ly >/dev/null 2>&1 || command -v ly-dm >/dev/null 2>&1; then
    setup_display_manager() {
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
        fi
    }
    run_task "Configuring Ly display manager on tty2 (graphical.target)" setup_display_manager
fi

# ==============================================================================
# Installation Complete Summary & Telemetry
# ==============================================================================
END_TIME=$(date +%s)
TOTAL_ELAPSED=$(( END_TIME - START_TIME ))

echo ""
echo -e "  ${GREEN}${BOLD}┌─────────────────────────────────────────────────────────────┐${NC}"
printf "  ${GREEN}${BOLD}│${NC}  ${GREEN}✔${NC} ${BOLD}%-40s${NC} ${SUBTEXT}%14s${NC}  ${GREEN}${BOLD}│${NC}\n" "Installation Completed Successfully!" "${TOTAL_ELAPSED}s elapsed"
echo -e "  ${GREEN}${BOLD}│${NC}  ${SUBTEXT}All desktop configurations & components are synchronized   ${NC}  ${GREEN}${BOLD}│${NC}"
echo -e "  ${GREEN}${BOLD}└─────────────────────────────────────────────────────────────┘${NC}"
echo ""

echo -e "  ${BOLD}Installed Environment Matrix:${NC}"
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

echo -e "  ${BOLD}Multi-Device Maintenance Workflow:${NC}"
echo -e "    ${SUBTEXT}• Update local PC from GitHub : ${TEAL}update-desktop${NC} or ${TEAL}dotfiles pull${NC}"
echo -e "    ${SUBTEXT}• Push local tweaks to GitHub : ${TEAL}dotfiles push \"message\"${NC}"
echo -e "    ${SUBTEXT}• Check sync status           : ${TEAL}dotfiles status${NC}"
echo ""

# Desktop Notification on Completion
if [ -n "$DISPLAY" ] && command -v dunstify >/dev/null 2>&1; then
    dunstify -u normal -r 9922 -h string:x-dunst-stack-tag:antigravity "⚡ Antigravity OS Ready" "Desktop suite synchronized in ${TOTAL_ELAPSED}s!" 2>/dev/null || true
fi

# Interactive Next Step
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
    echo -e "  ${PEACH}To start your session now, run: ${BOLD}startx${NC} or reboot into Ly."
    echo ""
fi
