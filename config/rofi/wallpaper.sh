#!/usr/bin/env bash
set -e

WALLPAPER_DIR="$HOME/Pictures/Wallpapers"
ROFI_THEME="$HOME/.config/rofi/wallpaper.rasi"

if [ ! -d "$WALLPAPER_DIR" ]; then
    mkdir -p "$WALLPAPER_DIR"
fi

# Detect currently set wallpaper from ~/.fehbg
CURRENT_WALLPAPER=""
if [ -f "$HOME/.fehbg" ]; then
    CURRENT_WALLPAPER=$(grep -o "'[^']*'" "$HOME/.fehbg" | head -n 1 | tr -d "'")
fi

# Control options
opt_random="󰒍  [Random]   Pick a random wallpaper"
opt_gallery="󰹑  [Gallery]  Open visual thumbnail grid (feh)"
opt_folder="  [Folder]   Open wallpapers folder (Ranger)"
separator="──────────────────────────────────────────────"

# Build options list
options_list=("$opt_random" "$opt_gallery" "$opt_folder" "$separator")

# List image files
shopt -s nullglob
files=("$WALLPAPER_DIR"/*.{jpg,jpeg,png,webp,bmp})
shopt -u nullglob

declare -A file_map

for file in "${files[@]}"; do
    filename=$(basename "$file")
    if [ "$file" = "$CURRENT_WALLPAPER" ]; then
        label="󰄬  ${filename}   [Active]"
    else
        label="   ${filename}"
    fi
    options_list+=("$label")
    file_map["$label"]="$file"
done

# Prompt in Rofi
menu_text=$(printf "%s\n" "${options_list[@]}")
chosen=$(echo "$menu_text" | rofi -dmenu -i -p "󰸉 bg :~$" -theme "$ROFI_THEME")

if [ -z "$chosen" ] || [ "$chosen" = "$separator" ]; then
    exit 0
fi

set_wallpaper() {
    local target="$1"
    local name
    name=$(basename "$target")

    # Apply via feh
    feh --no-fehbg --bg-fill "$target"

    # Persist in ~/.fehbg
    cat << EOF > "$HOME/.fehbg"
#!/bin/sh
feh --no-fehbg --bg-fill '$target'
EOF
    chmod +x "$HOME/.fehbg"

    # Notify
    if command -v dunstify >/dev/null 2>&1; then
        dunstify -r 4444 -u normal -h string:x-dunst-stack-tag:wallpaper "󰸉 Wallpaper Set" "$name"
    fi
}

case "$chosen" in
    *"[Random]"*)
        if [ ${#files[@]} -gt 0 ]; then
            rand_idx=$(( RANDOM % ${#files[@]} ))
            set_wallpaper "${files[$rand_idx]}"
        fi
        ;;
    *"[Gallery]"*)
        # Launch feh thumbnail browser where clicking any thumbnail applies it as wallpaper
        feh -t -E 180 -y 140 -W 1080 -H 720 \
            --title "Wallpaper Gallery - Click to Apply" \
            --action "feh --no-fehbg --bg-fill '%f'; printf '#!/bin/sh\nfeh --no-fehbg --bg-fill \x27%%f\x27\n' > \$HOME/.fehbg; chmod +x \$HOME/.fehbg; dunstify -r 4444 '󰸉 Wallpaper Set' '%%n'" \
            "$WALLPAPER_DIR" &
        ;;
    *"[Folder]"*)
        alacritty --class FloatingTerm -e ranger "$WALLPAPER_DIR" &
        ;;
    *)
        selected_file="${file_map["$chosen"]}"
        if [ -n "$selected_file" ] && [ -f "$selected_file" ]; then
            set_wallpaper "$selected_file"
        fi
        ;;
esac
