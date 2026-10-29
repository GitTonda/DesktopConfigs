#
# ~/.bashrc - Modern Terminal Rice (Catppuccin Mocha)
#

# If not running interactively, don't do anything
[[ $- != *i* ]] && return

# User paths
export PATH="$HOME/.local/bin:$PATH"

# Default Editor and Pager
export EDITOR="nano"
export VISUAL="nano"
export PAGER="less"

# ------------------------------------------------------------------------------
# Aliases
# ------------------------------------------------------------------------------
# Coreutils replacements
if command -v eza >/dev/null 2>&1; then
    alias ls='eza --icons --group-directories-first'
    alias ll='eza -la --icons --group-directories-first --git'
    alias l='eza -l --icons --group-directories-first'
    alias la='eza -a --icons --group-directories-first'
    alias tree='eza --tree --icons'
else
    alias ls='ls --color=auto'
    alias ll='ls -lah --color=auto'
fi

if command -v bat >/dev/null 2>&1; then
    alias cat='bat --paging=never'
    alias catt='bat'
fi

if command -v rg >/dev/null 2>&1; then
    alias grep='rg --color=auto'
else
    alias grep='grep --color=auto'
fi

if command -v fd >/dev/null 2>&1; then
    alias find='fd'
fi

# Dotfiles Management
alias update-desktop='dotfiles pull'
alias dotfiles-pull='dotfiles pull'
alias dotfiles-push='dotfiles push'
alias dotfiles-status='dotfiles status'

# ------------------------------------------------------------------------------
# FZF (Fuzzy Finder) Configuration & Catppuccin Mocha Theme
# ------------------------------------------------------------------------------
if command -v fzf >/dev/null 2>&1; then
    export FZF_DEFAULT_OPTS=" \
    --color=bg+:#313244,bg:#1e1e2e,spinner:#f5e0dc,hl:#f38ba8 \
    --color=fg:#cdd6f4,header:#f38ba8,info:#cba6f7,pointer:#f5e0dc \
    --color=marker:#f5e0dc,fg+:#cdd6f4,prompt:#cba6f7,hl+:#f38ba8 \
    --prompt='❯ ' \
    --pointer='◆' \
    --marker='✓' \
    --layout=reverse \
    --border \
    --height=45%"

    if command -v fd >/dev/null 2>&1; then
        export FZF_DEFAULT_COMMAND="fd --type f --hidden --exclude .git --exclude node_modules"
        export FZF_CTRL_T_COMMAND="$FZF_DEFAULT_COMMAND"
        export FZF_ALT_C_COMMAND="fd --type d --hidden --exclude .git --exclude node_modules"
    fi

    if command -v bat >/dev/null 2>&1; then
        export FZF_CTRL_T_OPTS="--preview 'bat --style=numbers --color=always --line-range :300 {} 2>/dev/null || cat {}'"
    fi

    if command -v eza >/dev/null 2>&1; then
        export FZF_ALT_C_OPTS="--preview 'eza --tree --level=2 --icons --color=always {} 2>/dev/null || ls -la {}'"
    fi

    # Shell bindings
    [ -f /usr/share/fzf/key-bindings.bash ] && source /usr/share/fzf/key-bindings.bash
    [ -f /usr/share/fzf/completion.bash ] && source /usr/share/fzf/completion.bash
fi

# ------------------------------------------------------------------------------
# Zoxide (Smart directory jumper: 'z <dir>')
# ------------------------------------------------------------------------------
if command -v zoxide >/dev/null 2>&1; then
    eval "$(zoxide init bash)"
fi

# ------------------------------------------------------------------------------
# Starship Prompt
# ------------------------------------------------------------------------------
if command -v starship >/dev/null 2>&1; then
    eval "$(starship init bash)"
fi
