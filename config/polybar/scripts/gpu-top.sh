#!/usr/bin/env bash

# Dedicated GPU TUI Monitor launcher
if command -v nvitop >/dev/null 2>&1; then
    exec nvitop "$@"
elif [ -x "$HOME/.local/bin/nvitop" ]; then
    exec "$HOME/.local/bin/nvitop" "$@"
elif command -v nvtop >/dev/null 2>&1; then
    exec nvtop "$@"
elif command -v nvidia-smi >/dev/null 2>&1; then
    exec watch -n 1 -c nvidia-smi
elif command -v btop >/dev/null 2>&1; then
    exec btop
else
    exec top
fi
