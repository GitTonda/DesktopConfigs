# Catppuccin Mocha Rice Design System & Token Architecture

A unified, reusable design specification and token dictionary defining the visual identity of the desktop environment (i3wm, Polybar, Dunst, Control Center, Desktop Settings, Quick Share, Thunar, and Alacritty).

---

## 1. Core Principles

1. **Strict 0px Geometry:**
   - Absolute `border-radius: 0px` across all UI elements, containers, cards, buttons, switches, dialogs, badges, and popups.
2. **Refined 1px Hierarchy:**
   - Thin, crisp `1px` structural borders using Catppuccin Surface0 (`#313244`) or semi-transparent accent borders (`rgba(accent, 0.45)`). Avoid heavy 2px+ borders.
3. **Dynamic Wallpaper Accent Integration:**
   - Primary accent color is dynamically synchronized from Polybar / Wallpaper (`~/.config/polybar/colors.ini` / `~/.config/theme/accent.color`).
   - Standard accent states:
     - Full Accent: `@accent@`
     - Dim Accent (Translucent Fill): `rgba(accent_r, accent_g, accent_b, 0.18)`
     - Border Accent: `rgba(accent_r, accent_g, accent_b, 0.45)`
4. **Monospace Typography Rhythm:**
   - Primary Font: `JetBrainsMono Nerd Font` (fallbacks: `JetBrains Mono`, `monospace`).
   - Micro Section Titles: `8pt` - `8.5pt` (`10-11px`), uppercase, bold/semibold, letter-spacing `0.5px` - `0.6px`, muted color (`#a6adc8`).
   - Primary Text: `9.5pt` - `10pt` (`13-14px`), semibold/regular, `#cdd6f4`.
   - Secondary / Subtext: `8pt` - `8.5pt` (`11-12px`), `#6c7086` or `#a6adc8`.
5. **Standardized Header Action Buttons (`.header-btn`):**
   - Square dimensions: `26x26px` (GTK desktop) or `28x28px` (Web/Tauri).
   - Base appearance: `background: rgba(30, 30, 46, 0.70); border: 1px solid #313244; color: #a6adc8;`.
   - Hover appearance (Utility / Settings): `background: rgba(49, 50, 68, 0.85); border-color: @accent@; color: @accent@;`.
   - Hover appearance (Danger / Close / Power): `background: rgba(243, 139, 168, 0.20); border-color: #f38ba8; color: #f38ba8;`.

---

## 2. Token Dictionary

### 2.1 Primitive Color Tokens (Catppuccin Mocha)

| Token Name | Hex Code | Role |
|---|---|---|
| `color-crust` | `#11111b` | Deepest background (bars, titlebars, statusbars) |
| `color-mantle` | `#181825` | Secondary background (sidebars, toolbars) |
| `color-base` | `#1e1e2e` | Primary content background (file view, editors, cards) |
| `color-surface0` | `#313244` | Default container border, inactive pills, switch trough |
| `color-surface1` | `#45475a` | Subtle button background, scrollbar sliders |
| `color-surface2` | `#585b70` | Interactive hover borders, muted icons |
| `color-overlay0` | `#6c7086` | Secondary text, captions, inactive status indicators |
| `color-subtext0` | `#a6adc8` | Section titles, item descriptions |
| `color-subtext1` | `#bac2de` | High-contrast secondary text |
| `color-text` | `#cdd6f4` | Primary high-readability text |
| `color-red` | `#f38ba8` | Danger, error, close buttons, urgent alerts |
| `color-green` | `#a6e3a1` | Success, connected badges, active transfers |
| `color-yellow` | `#f9e2af` | Warning, pending transfers |
| `color-peach` | `#fab387` | Warm wallpaper accent default |
| `color-blue` | `#89b4fa` | Cool wallpaper accent default |
| `color-mauve` | `#cba6f7` | Purple wallpaper accent |

### 2.2 Semantic Tokens

| Semantic Token | Value / Mapping | Usage |
|---|---|---|
| `--sys-bg-window` | `rgba(17, 17, 27, @opacity@)` / `#11111b` | Top-level window backdrop |
| `--sys-bg-sidebar` | `rgba(24, 24, 37, 0.70)` / `#181825` | Left sidebar background |
| `--sys-bg-card` | `rgba(30, 30, 46, 0.70)` | Standard card/pill surface |
| `--sys-bg-card-hover` | `rgba(49, 50, 68, 0.85)` | Card and row hover fill |
| `--sys-border` | `#313244` | Default divider and card border |
| `--sys-border-hover` | `#585b70` | Subtle hover border |
| `--sys-border-accent` | `rgba(accent, 0.45)` | Refined outer window & active border |
| `--sys-accent` | `${colors.accent}` | Dynamic primary accent |
| `--sys-accent-dim` | `rgba(accent, 0.18)` | Active toggle pill fill |
| `--sys-accent-text` | `#11111b` | High-contrast text on solid accent fill |
| `--sys-text-primary` | `#cdd6f4` | Main headings, titles, active labels |
| `--sys-text-muted` | `#6c7086` | Metadata, timestamps, inactive states |
| `--sys-danger` | `#f38ba8` | Close, disconnect, delete actions |

---

## 3. Component Specifications

### 3.1 Window Shell
- **Window Border:** `1px solid @accent_border@` (never 2px).
- **Window Background:** `rgba(17, 17, 27, @opacity@)`.
- **Corner Radius:** `0px`.

### 3.2 Header Bar
- **Height:** `40px` - `44px`.
- **Left Branding:** App icon (`14-16px` color `@accent@`) + uppercase title (`11-12px bold #cdd6f4`) + optional hostname pill.
- **Right Action Buttons:**
  - Standardized `.header-btn` (square `26x26px` or `28x28px`).
  - Spacing between header buttons: `6px`.
  - Margin from window border: `0px` (aligned flush with content padding).

### 3.3 Sidebar Navigation
- **Width:** `200px` - `240px`.
- **Background:** `rgba(17, 17, 27, 0.85)` / `#181825`.
- **Row Height:** `36px` - `40px`.
- **Default State:** Transparent background, `color: #a6adc8`, `border-left: 3px solid transparent`.
- **Hover State:** `background: rgba(49, 50, 68, 0.40); color: #cdd6f4;`.
- **Active / Selected State:**
  - `background: rgba(49, 50, 68, 0.85);`
  - `color: #ffffff;`
  - `border-left: 3px solid @accent@;`
  - Icon highlighted in `@accent@`.

### 3.4 Cards & Content Panes
- **Card Fill:** `rgba(30, 30, 46, 0.70)`.
- **Card Border:** `1px solid #313244`.
- **Card Padding:** `10px 14px` (outer), `8px 0px` (internal rows).
- **Separators:** `1px solid #313244; margin: 6px 0px;`.

### 3.5 Form Controls & Interactive Inputs
- **Switches:**
  - Trough: `min-width: 44px; min-height: 22px; background: #313244; border: 1px solid #45475a; border-radius: 0px;`.
  - Checked Trough: `background: @accent@; border-color: @accent@;`.
  - Slider: `18x18px; border-radius: 0px; background: #cdd6f4;` (checked slider: `#11111b`).
- **Sliders / Scales:**
  - Trough: `6px` flat height, `#313244`, accent progress fill.
  - Thumb: `14x14px` square `#cdd6f4` with `1px solid #11111b`.
- **Buttons (`.btn` / `.action-btn`):**
  - Height: `28px` - `32px`.
  - Fill: `rgba(30, 30, 46, 0.70)` or `#313244`.
  - Border: `1px solid #45475a`.
  - Hover: `background: @accent@; border-color: @accent@; color: #11111b;`.

---

## 4. Cross-Platform Reusability Guide

### 4.1 GTK3 / GTK4 Applications
Import or load `gtk.css` with token definitions:
```css
@define-color base_bg #1e1e2e;
@define-color mantle_bg #181825;
@define-color crust_bg #11111b;
@define-color surface_bg #313244;
@define-color surface_hover #45475a;
@define-color border_color #313244;
@define-color text_color #cdd6f4;
@define-color text_dim #a6adc8;
@define-color accent_color @accent@;
```

### 4.2 Web / Tauri Applications (Tailwind / PostCSS)
Map semantic CSS variables directly in `:root`:
```css
:root {
  --sys-bg: #11111b;
  --sys-mantle: #181825;
  --sys-base: #1e1e2e;
  --sys-surface: rgba(30, 30, 46, 0.70);
  --sys-surface-hover: rgba(49, 50, 68, 0.85);
  --sys-border: #313244;
  --sys-border-hover: #585b70;
  --sys-accent: #ffaa45;
  --sys-accent-dim: rgba(255, 170, 69, 0.18);
  --sys-accent-text: #11111b;
  --sys-text: #cdd6f4;
  --sys-subtext: #a6adc8;
  --sys-muted: #6c7086;
  --sys-red: #f38ba8;
  --sys-green: #a6e3a1;
}
```
