#!/usr/bin/env bash
# ==============================================================================
# Antigravity Bootstrap Installer
# Quick-start one-liner for bootstrapping Arch Linux into a rice machine.
# ==============================================================================

set -e

REPO_URL="https://github.com/GitTonda/DesktopConfigs.git"

# Discover appropriate target directory
if [ -d "$HOME/DesktopConfigs/.git" ]; then
    TARGET_DIR="$HOME/DesktopConfigs"
elif [ -d "${XDG_DATA_HOME:-$HOME/.local/share}/dotfiles/.git" ]; then
    TARGET_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/dotfiles"
elif [ -d "$HOME/dotfiles/.git" ]; then
    TARGET_DIR="$HOME/dotfiles"
else
    TARGET_DIR="$HOME/DesktopConfigs"
fi

# ------------------------------------------------------------------------------
# Colors & Visual Formatting
# ------------------------------------------------------------------------------
PEACH='\033[38;2;250;179;135m'
BLUE='\033[38;2;137;180;250m'
GREEN='\033[38;2;166;227;161m'
MAUVE='\033[38;2;203;166;247m'
RED='\033[38;2;243;139;168m'
YELLOW='\033[38;2;249;226;175m'
SUBTEXT='\033[38;2;166;173;200m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${PEACH}${BOLD}"
echo "  ┌──────────────────────────────────────────────────────────────┐"
echo "  │        Antigravity / Catppuccin Mocha Bootstrap              │"
echo "  │       One-Line Fast Setup for Modern Arch Linux PCs          │"
echo "  └──────────────────────────────────────────────────────────────┘"
echo -e "${NC}"

# Root verification
if [ "$EUID" -eq 0 ]; then
    echo -e "${RED}${BOLD}[✖] Error: Do not run this bootstrap script as root.${NC}"
    echo -e "    Configurations must be placed in a regular user's home directory.\n"
    echo -e "    ${BOLD}If you just installed Arch Linux and are logged in as root:${NC}"
    echo -e "      1. pacman -S --needed sudo"
    echo -e "      2. useradd -m -G wheel,video,audio,input -s /bin/bash <username>"
    echo -e "      3. passwd <username>"
    echo -e "      4. echo '%wheel ALL=(ALL:ALL) ALL' > /etc/sudoers.d/wheel"
    echo -e "      5. su - <username>"
    echo -e "      6. curl -fsSL https://raw.githubusercontent.com/GitTonda/DesktopConfigs/main/bootstrap.sh | bash\n"
    exit 1
fi

# Sudo check
if ! command -v sudo >/dev/null 2>&1; then
    echo -e "${RED}${BOLD}[✖] Error: 'sudo' is required.${NC} Please install sudo and grant user privileges."
    exit 1
fi

# Ensure git and curl are available
if ! command -v git >/dev/null 2>&1 || ! command -v curl >/dev/null 2>&1; then
    echo -e "  ${BLUE}${BOLD}==> Installing required prerequisites (git, curl)...${NC}"
    if command -v pacman >/dev/null 2>&1; then
        sudo pacman -Syu --needed --noconfirm git curl
    elif command -v apt >/dev/null 2>&1; then
        sudo apt update && sudo apt install -y git curl
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf install -y git curl
    else
        echo -e "${RED}[✖] Error: Please install git and curl, then re-run.${NC}"
        exit 1
    fi
fi

# Clone or synchronize repository
if [ -d "$TARGET_DIR/.git" ]; then
    echo -e "  ${BLUE}==> Existing repository found at ${SUBTEXT}${TARGET_DIR}${BLUE}. Updating...${NC}"
    cd "$TARGET_DIR"
    git pull origin main || true
else
    echo -e "  ${BLUE}==> Cloning repository into ${SUBTEXT}${TARGET_DIR}${BLUE}...${NC}"
    mkdir -p "$(dirname "$TARGET_DIR")"
    git clone "$REPO_URL" "$TARGET_DIR"
    cd "$TARGET_DIR"
fi

# Execute main installer attached to controlling terminal tty
chmod +x ./install.sh
echo -e "  ${GREEN}✔ Handing over control to the main installer...${NC}\n"
exec ./install.sh "$@" </dev/tty
