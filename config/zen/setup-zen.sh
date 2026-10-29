#!/usr/bin/env bash
# ==============================================================================
# Zen Browser Rice & Extensions Setup Script
# Automates profiles deployment, policies, userChrome, and extensions
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
    for dist_dir in "/opt/zen-browser-bin/distribution" "/usr/lib/zen-browser/distribution"; do
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

PROFILES=()
for base in "${SEARCH_DIRS[@]}"; do
    if [ -d "$base" ]; then
        while IFS= read -r -d '' p; do
            # Add directory if it contains prefs.js or compatibility.ini or matches profile patterns
            if [ -f "$p/prefs.js" ] || [ -f "$p/compatibility.ini" ] || [[ "$(basename "$p")" =~ (default|Default|release) ]]; then
                PROFILES+=("$p")
            fi
        done < <(find "$base" -maxdepth 1 -mindepth 1 -type d -print0)
    fi
done

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
