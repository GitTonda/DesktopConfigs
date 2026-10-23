#!/usr/bin/env bash
set -e

REPO_URL="https://github.com/GitTonda/DesktopConfigs.git"
TARGET_DIR="$HOME/dotfiles"

echo "=========================================================="
echo "    Bootstrap: Antigravity Catppuccin Mocha Setup         "
echo "=========================================================="
echo ""

# Ensure git is installed
if ! command -v git >/dev/null 2>&1; then
    echo "==> Git is required. Installing git..."
    if command -v pacman >/dev/null 2>&1; then
        sudo pacman -Syu --needed --noconfirm git
    elif command -v apt >/dev/null 2>&1; then
        sudo apt update && sudo apt install -y git
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y git
    else
        echo "[-] Error: Please install git and re-run."
        exit 1
    fi
fi

# Clone or update repository
if [ -d "$TARGET_DIR/.git" ]; then
    echo "==> Existing dotfiles repository found at $TARGET_DIR. Updating..."
    cd "$TARGET_DIR"
    git pull origin main
else
    echo "==> Cloning repository to $TARGET_DIR..."
    git clone "$REPO_URL" "$TARGET_DIR"
    cd "$TARGET_DIR"
fi

# Run installer
chmod +x ./install.sh
./install.sh
