#!/usr/bin/env bash
# ==============================================================================
# Zen Browser Rice & Extensions Setup Script
# Automates installation, profiles deployment, policies, userChrome, and extensions
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CHROME_SRC="$SCRIPT_DIR/chrome"
EXT_SRC="$SCRIPT_DIR/extensions"
USER_JS_SRC="$SCRIPT_DIR/user.js"
POLICIES_SRC="$SCRIPT_DIR/policies.json"

BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m'

echo -e "${BLUE}${BOLD}==> Setting up Zen Browser configurations and extensions...${NC}"

# 0. Automatically Install Zen Browser if missing
ensure_zen_installed() {
    if command -v zen-browser >/dev/null 2>&1 || command -v zen >/dev/null 2>&1 || \
       (command -v flatpak >/dev/null 2>&1 && flatpak list --app 2>/dev/null | grep -q "app.zen_browser.zen"); then
        return 0
    fi

    echo -e "${YELLOW}${BOLD}==> Zen Browser is not installed. Installing automatically...${NC}"

    if command -v yay >/dev/null 2>&1; then
        echo -e "${BLUE}==> Installing zen-browser-bin via yay...${NC}"
        yay -S --needed --noconfirm zen-browser-bin dbus-glib || true
    elif command -v paru >/dev/null 2>&1; then
        echo -e "${BLUE}==> Installing zen-browser-bin via paru...${NC}"
        paru -S --needed --noconfirm zen-browser-bin dbus-glib || true
    elif command -v pacman >/dev/null 2>&1 && command -v git >/dev/null 2>&1; then
        echo -e "${BLUE}==> Building zen-browser-bin from AUR...${NC}"
        sudo pacman -S --needed --noconfirm dbus-glib base-devel 2>/dev/null || true
        TMP_DIR=$(mktemp -d)
        if git clone https://aur.archlinux.org/zen-browser-bin.git "$TMP_DIR/zen-browser-bin"; then
            (cd "$TMP_DIR/zen-browser-bin" && makepkg -si --noconfirm) || true
        fi
        rm -rf "$TMP_DIR"
    elif command -v flatpak >/dev/null 2>&1; then
        echo -e "${BLUE}==> Installing Zen Browser via Flatpak...${NC}"
        flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo 2>/dev/null || true
        flatpak install -y flathub app.zen_browser.zen || true
    else
        echo -e "${BLUE}==> Downloading official Zen Browser release tarball...${NC}"
        mkdir -p "$HOME/.local/opt"
        curl -fsSL "https://github.com/zen-browser/desktop/releases/latest/download/zen.linux-x86_64.tar.xz" | tar -xJ -C "$HOME/.local/opt" 2>/dev/null || true
        if [ -x "$HOME/.local/opt/zen/zen" ]; then
            mkdir -p "$HOME/.local/bin"
            ln -sf "$HOME/.local/opt/zen/zen" "$HOME/.local/bin/zen"
            ln -sf "$HOME/.local/opt/zen/zen" "$HOME/.local/bin/zen-browser"
        fi
    fi

    # Ensure symlinks exist in ~/.local/bin
    mkdir -p "$HOME/.local/bin"
    if command -v zen-browser >/dev/null 2>&1; then
        ln -sf "$(command -v zen-browser)" "$HOME/.local/bin/zen" 2>/dev/null || true
    elif command -v zen >/dev/null 2>&1; then
        ln -sf "$(command -v zen)" "$HOME/.local/bin/zen-browser" 2>/dev/null || true
    fi
}

ensure_zen_installed

# 1. Apply Flatpak Cursor and Theme Overrides if flatpak is installed
if command -v flatpak >/dev/null 2>&1; then
    if flatpak list --app 2>/dev/null | grep -q "app.zen_browser.zen"; then
        echo -e "${BLUE}==> Configuring Flatpak permissions & cursor overrides...${NC}"
        flatpak override --user --filesystem=~/.icons:ro app.zen_browser.zen 2>/dev/null || true
        flatpak override --user --filesystem=~/.local/share/icons:ro app.zen_browser.zen 2>/dev/null || true
        flatpak override --user --env=XCURSOR_THEME=Bibata-Modern-Classic app.zen_browser.zen 2>/dev/null || true
        flatpak override --user --env=XCURSOR_SIZE=24 app.zen_browser.zen 2>/dev/null || true
    fi
fi

# 2. Deploy Enterprise Policies if native distribution directory exists
if [ -f "$POLICIES_SRC" ]; then
    for dist_dir in "/opt/zen-browser-bin/distribution" "/usr/lib/zen-browser/distribution" "$HOME/.local/opt/zen/distribution"; do
        if [ -d "$dist_dir" ]; then
            if [ -w "$dist_dir" ]; then
                cp "$POLICIES_SRC" "$dist_dir/policies.json"
                echo -e "${GREEN}✔ Installed policies.json to $dist_dir${NC}"
            elif sudo -n true 2>/dev/null; then
                sudo cp "$POLICIES_SRC" "$dist_dir/policies.json"
                echo -e "${GREEN}✔ Installed policies.json to $dist_dir via sudo${NC}"
            fi
        fi
    done
fi

# 3. Ensure Extensions exist (download if missing)
mkdir -p "$EXT_SRC"
declare -A EXTENSIONS=(
    ["{446900e4-71c2-419f-a6a7-df9c091e268b}.xpi"]="https://addons.mozilla.org/firefox/downloads/latest/bitwarden-password-manager/latest.xpi"
    ["uBlock0@raymondhill.net.xpi"]="https://addons.mozilla.org/firefox/downloads/latest/ublock-origin/latest.xpi"
    ["addon@darkreader.org.xpi"]="https://addons.mozilla.org/firefox/downloads/latest/darkreader/latest.xpi"
)

for ext_id in "${!EXTENSIONS[@]}"; do
    ext_file="$EXT_SRC/$ext_id"
    if [ ! -f "$ext_file" ]; then
        url="${EXTENSIONS[$ext_id]}"
        echo -e "${YELLOW}==> Downloading missing extension $ext_id...${NC}"
        curl -sL "$url" -o "$ext_file" || echo "Warning: Failed to download $ext_id"
    fi
done

# 4. Locate Zen profiles across Flatpak and native installations
SEARCH_DIRS=(
    "$HOME/.var/app/app.zen_browser.zen/.zen"
    "$HOME/.zen"
)

scan_profiles() {
    PROFILES=()
    for base in "${SEARCH_DIRS[@]}"; do
        if [ -d "$base" ]; then
            while IFS= read -r -d '' p; do
                if [ -f "$p/prefs.js" ] || [ -f "$p/compatibility.ini" ] || [[ "$(basename "$p")" =~ (default|Default|release) ]]; then
                    PROFILES+=("$p")
                fi
            done < <(find "$base" -maxdepth 1 -mindepth 1 -type d -print0)
        fi
    done
}

scan_profiles

# If no profile exists yet, initialize default profile with a short headless run
if [ ${#PROFILES[@]} -eq 0 ]; then
    ZEN_BIN=""
    if command -v zen-browser >/dev/null 2>&1; then
        ZEN_BIN="$(command -v zen-browser)"
    elif command -v zen >/dev/null 2>&1; then
        ZEN_BIN="$(command -v zen)"
    elif [ -x "$HOME/.local/bin/zen" ]; then
        ZEN_BIN="$HOME/.local/bin/zen"
    elif [ -x "$HOME/.local/bin/zen-browser" ]; then
        ZEN_BIN="$HOME/.local/bin/zen-browser"
    fi

    if [ -n "$ZEN_BIN" ]; then
        echo -e "${BLUE}==> Initializing default Zen profile structure...${NC}"
        timeout 5s "$ZEN_BIN" --headless --screenshot /tmp/zen_init.png about:blank >/dev/null 2>&1 || true
        pkill -f zen-bin >/dev/null 2>&1 || true
        rm -f /tmp/zen_init.png 2>/dev/null || true
        scan_profiles
    fi
fi

ZEN_RUNNING=0
if pgrep -i -f "zen-bin|zen-browser" >/dev/null 2>&1; then
    ZEN_RUNNING=1
fi

if [ ${#PROFILES[@]} -eq 0 ]; then
    echo -e "${YELLOW}Notice: No existing Zen profiles found yet. Run 'zen-browser' once to initialize.${NC}"
else
    for prof in "${PROFILES[@]}"; do
        echo -e "${BLUE}==> Deploying to profile: $(basename "$prof")...${NC}"
        
        # Clean stale locks if Zen is not running
        if [ "$ZEN_RUNNING" -eq 0 ]; then
            rm -f "$prof/.parentlock" "$prof/lock" 2>/dev/null || true
        fi
        
        # Deploy chrome folder
        mkdir -p "$prof/chrome"
        cp -r "$CHROME_SRC/"* "$prof/chrome/"
        
        # Deploy user.js
        if [ -f "$USER_JS_SRC" ]; then
            cp "$USER_JS_SRC" "$prof/user.js"
        fi
        
        # Deploy extensions
        mkdir -p "$prof/extensions"
        cp -r "$EXT_SRC/"*.xpi "$prof/extensions/" 2>/dev/null || true

        # Ensure legacy stylesheet & border preferences in prefs.js if it exists
        if [ -f "$prof/prefs.js" ]; then
            grep -q "toolkit.legacyUserProfileCustomizations.stylesheets" "$prof/prefs.js" || \
                echo 'user_pref("toolkit.legacyUserProfileCustomizations.stylesheets", true);' >> "$prof/prefs.js"
            grep -q "zen.theme.border-radius" "$prof/prefs.js" || \
                echo 'user_pref("zen.theme.border-radius", 0);' >> "$prof/prefs.js"
            grep -q "zen.theme.content-element-separation" "$prof/prefs.js" || \
                echo 'user_pref("zen.theme.content-element-separation", 0);' >> "$prof/prefs.js"
        fi
    done
fi

# 5. Trigger active desktop theme update for Zen
WALLPAPER=""
if [ -f "$HOME/.fehbg" ]; then
    WALLPAPER=$(grep -oE "'/.*'" "$HOME/.fehbg" | tr -d "'" | head -n1)
fi

if [ -f "$HOME/.config/theme/apply-theme.sh" ] && [ -n "$WALLPAPER" ] && [ -f "$WALLPAPER" ]; then
    echo -e "${BLUE}==> Synchronizing Zen Browser colors with active wallpaper & accent...${NC}"
    "$HOME/.config/theme/apply-theme.sh" "$WALLPAPER" >/dev/null 2>&1 || true
fi

echo -e "${GREEN}${BOLD}✔ Zen Browser setup completed successfully!${NC}"
