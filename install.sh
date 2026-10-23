#!/usr/bin/env bash
set -e

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================================="
echo "      Antigravity / Catppuccin Mocha Dotfiles Installer   "
echo "=========================================================="
echo ""

if [ "$EUID" -eq 0 ]; then
    echo "[-] Please run this installer as your regular user (with sudo access), NOT as root."
    echo "    Running as root would place configurations in /root instead of your home directory."
    exit 1
fi

# 1. Package Installation
if command -v pacman >/dev/null 2>&1; then
    echo "==> Detected Arch Linux. Installing complete desktop environment..."
    sudo pacman -Syu --needed --noconfirm \
        xorg-server \
        xorg-xinit \
        xorg-xrandr \
        xorg-xmodmap \
        mesa \
        i3-wm \
        polybar \
        alacritty \
        picom \
        rofi \
        feh \
        dunst \
        pipewire \
        pipewire-pulse \
        pipewire-alsa \
        wireplumber \
        alsa-utils \
        libpulse \
        networkmanager \
        brightnessctl \
        playerctl \
        maim \
        xclip \
        xdotool \
        ranger \
        mpv \
        ncdu \
        btop \
        nano \
        curl \
        unzip \
        git \
        python \
        ttf-jetbrains-mono-nerd \
        ttf-font-awesome \
        noto-fonts-emoji \
        ly

    # Ensure NetworkManager is enabled
    if command -v systemctl >/dev/null 2>&1; then
        echo "==> Enabling NetworkManager..."
        sudo systemctl enable NetworkManager.service 2>/dev/null || true
    fi

elif command -v apt >/dev/null 2>&1; then
    echo "==> Detected Debian/Ubuntu/Pop!_OS. Installing packages..."
    sudo apt update
    sudo apt install -y \
        xorg \
        xinit \
        x11-xserver-utils \
        x11-xkb-utils \
        i3 \
        polybar \
        alacritty \
        picom \
        rofi \
        feh \
        dunst \
        pipewire \
        pipewire-pulse \
        pipewire-alsa \
        wireplumber \
        alsa-utils \
        pulseaudio-utils \
        network-manager \
        brightnessctl \
        playerctl \
        maim \
        xclip \
        xdotool \
        ranger \
        mpv \
        ncdu \
        btop \
        nano \
        curl \
        unzip \
        git \
        python3 \
        fonts-font-awesome

elif command -v dnf >/dev/null 2>&1; then
    echo "==> Detected Fedora. Installing packages..."
    sudo dnf install -y \
        xorg-x11-server-Xorg \
        xorg-x11-xinit \
        i3 \
        polybar \
        alacritty \
        picom \
        rofi \
        feh \
        dunst \
        pipewire \
        pipewire-pulseaudio \
        wireplumber \
        alsa-utils \
        pulseaudio-utils \
        NetworkManager \
        brightnessctl \
        playerctl \
        maim \
        xclip \
        xdotool \
        ranger \
        mpv \
        ncdu \
        btop \
        nano \
        curl \
        unzip \
        git \
        python3 \
        fontawesome-fonts
else
    echo "==> Warning: Unknown package manager. Please ensure required packages are installed."
fi

# 2. Install JetBrainsMono Nerd Font if not present
echo ""
echo "==> Checking for JetBrainsMono Nerd Font..."
if ! fc-list : family | grep -qi "JetBrainsMono Nerd Font"; then
    echo "==> Downloading and installing JetBrainsMono Nerd Font..."
    mkdir -p ~/.local/share/fonts/JetBrainsMono
    FONT_URL="https://github.com/ryanoasis/nerd-fonts/releases/latest/download/JetBrainsMono.zip"
    TMP_FONT_DIR="$(mktemp -d)"
    curl -fsSL "$FONT_URL" -o "$TMP_FONT_DIR/JetBrainsMono.zip"
    unzip -qo "$TMP_FONT_DIR/JetBrainsMono.zip" -d ~/.local/share/fonts/JetBrainsMono
    rm -rf "$TMP_FONT_DIR"
    fc-cache -f ~/.local/share/fonts
    echo "==> Font installed successfully!"
else
    echo "==> JetBrainsMono Nerd Font is already installed."
fi

# 3. Backup existing configs
BACKUP_DIR="$HOME/.config_backup_$(date +%Y%m%d_%H%M%S)"
echo ""
echo "==> Backing up existing configurations to $BACKUP_DIR..."
mkdir -p "$BACKUP_DIR"

for app in i3 polybar alacritty rofi picom dunst; do
    if [ -d "$HOME/.config/$app" ] || [ -f "$HOME/.config/$app" ]; then
        mv "$HOME/.config/$app" "$BACKUP_DIR/" 2>/dev/null || true
    fi
done

if [ -f "$HOME/.nanorc" ]; then
    cp "$HOME/.nanorc" "$BACKUP_DIR/" 2>/dev/null || true
fi
if [ -f "$HOME/.xinitrc" ]; then
    cp "$HOME/.xinitrc" "$BACKUP_DIR/" 2>/dev/null || true
fi

# 4. Deploy Dotfiles
echo ""
echo "==> Deploying configurations..."
mkdir -p "$HOME/.config"
cp -r "$DOTFILES_DIR/config/"* "$HOME/.config/"
cp "$DOTFILES_DIR/home/.nanorc" "$HOME/.nanorc"
[ -f "$DOTFILES_DIR/home/.xinputrc" ] && cp "$DOTFILES_DIR/home/.xinputrc" "$HOME/.xinputrc"
[ -f "$DOTFILES_DIR/home/.xinitrc" ] && cp "$DOTFILES_DIR/home/.xinitrc" "$HOME/.xinitrc"
chmod +x "$HOME/.xinitrc" 2>/dev/null || true

# 5. Deploy Wallpapers
echo "==> Deploying wallpapers..."
mkdir -p "$HOME/Pictures/Wallpapers"
cp -r "$DOTFILES_DIR/wallpapers/"* "$HOME/Pictures/Wallpapers/"

# 6. Ensure executable permissions on scripts
chmod +x "$HOME/.config/polybar/launch.sh"
chmod +x "$HOME/.config/polybar/scripts/"*.sh 2>/dev/null || true
chmod +x "$HOME/.config/rofi/powermenu.sh"
chmod +x "$HOME/.config/rofi/wifi.sh" "$HOME/.config/rofi/wifi.py" 2>/dev/null || true
chmod +x "$HOME/.config/i3/screenshot.sh"

# 7. Initialize wallpaper & create persistent ~/.fehbg
if [ -f "$HOME/Pictures/Wallpapers/waves_dark.jpg" ]; then
    cat << 'EOF' > "$HOME/.fehbg"
#!/bin/sh
feh --no-fehbg --bg-fill "$HOME/Pictures/Wallpapers/waves_dark.jpg"
EOF
    chmod +x "$HOME/.fehbg"
    if [ -n "$DISPLAY" ]; then
        "$HOME/.fehbg" 2>/dev/null || true
    fi
fi

# 8. Setup Ly Display Manager (if installed)
if command -v ly >/dev/null 2>&1 || command -v ly-dm >/dev/null 2>&1; then
    echo "==> Deploying clean Ly configuration..."
    sudo mkdir -p /etc/ly
    [ -f "$DOTFILES_DIR/config/ly/config.ini" ] && sudo cp "$DOTFILES_DIR/config/ly/config.ini" /etc/ly/config.ini 2>/dev/null || true
    [ -f "$DOTFILES_DIR/config/ly/config.lua" ] && sudo cp "$DOTFILES_DIR/config/ly/config.lua" /etc/ly/config.lua 2>/dev/null || true

    if command -v systemctl >/dev/null 2>&1; then
        echo "==> Enabling Ly display manager..."
        if systemctl list-unit-files ly.service >/dev/null 2>&1; then
            sudo systemctl enable ly.service 2>/dev/null || true
        elif systemctl list-unit-files ly@.service >/dev/null 2>&1; then
            sudo systemctl enable ly@tty2.service 2>/dev/null || true
        fi
    fi
fi

echo ""
echo "=========================================================="
echo " Setup Complete! "
echo " You can now start the environment via Ly or run 'startx'."
echo "=========================================================="
