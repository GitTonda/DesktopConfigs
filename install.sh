#!/usr/bin/env bash
set -e

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=========================================================="
echo "      Antigravity / Catppuccin Mocha Dotfiles Installer   "
echo "=========================================================="
echo ""

# 1. Package Installation
if command -v apt >/dev/null 2>&1; then
    echo "==> Detected Debian/Ubuntu/Pop!_OS. Installing packages..."
    sudo apt update
    sudo apt install -y \
        i3 \
        polybar \
        alacritty \
        picom \
        rofi \
        feh \
        dunst \
        maim \
        xclip \
        xdotool \
        brightnessctl \
        playerctl \
        ranger \
        mpv \
        ncdu \
        fonts-font-awesome \
        curl \
        unzip
elif command -v pacman >/dev/null 2>&1; then
    echo "==> Detected Arch Linux. Installing packages..."
    sudo pacman -Syu --needed --noconfirm \
        i3-wm \
        polybar \
        alacritty \
        picom \
        rofi \
        feh \
        dunst \
        maim \
        xclip \
        xdotool \
        brightnessctl \
        playerctl \
        ranger \
        mpv \
        ncdu \
        ttf-font-awesome \
        curl \
        unzip
elif command -v dnf >/dev/null 2>&1; then
    echo "==> Detected Fedora. Installing packages..."
    sudo dnf install -y \
        i3 \
        polybar \
        alacritty \
        picom \
        rofi \
        feh \
        dunst \
        maim \
        xclip \
        xdotool \
        brightnessctl \
        playerctl \
        ranger \
        mpv \
        ncdu \
        fontawesome-fonts \
        curl \
        unzip
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
    curl -sL "$FONT_URL" -o /tmp/JetBrainsMono.zip
    unzip -qo /tmp/JetBrainsMono.zip -d ~/.local/share/fonts/JetBrainsMono
    rm -f /tmp/JetBrainsMono.zip
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

# 4. Deploy Dotfiles
echo ""
echo "==> Deploying configurations..."
mkdir -p "$HOME/.config"
cp -r "$DOTFILES_DIR/config/"* "$HOME/.config/"
cp "$DOTFILES_DIR/home/.nanorc" "$HOME/.nanorc"

# 5. Deploy Wallpapers
echo "==> Deploying wallpapers..."
mkdir -p "$HOME/Pictures/Wallpapers"
cp -r "$DOTFILES_DIR/wallpapers/"* "$HOME/Pictures/Wallpapers/"

# 6. Ensure executable permissions on scripts
chmod +x "$HOME/.config/polybar/launch.sh"
chmod +x "$HOME/.config/rofi/powermenu.sh"

# 7. Initialize wallpaper
if [ -f "$HOME/Pictures/Wallpapers/waves_dark.jpg" ]; then
    feh --bg-fill "$HOME/Pictures/Wallpapers/waves_dark.jpg" 2>/dev/null || true
fi

echo ""
echo "=========================================================="
echo " Setup Complete! "
echo " You can now log into i3 and enjoy your rice."
echo "=========================================================="
