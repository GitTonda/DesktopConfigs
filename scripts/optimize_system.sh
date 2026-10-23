#!/usr/bin/env bash
set -e

# ==============================================================================
# System Optimization Script - Pop!_OS / Debian Minimal Performance
# ==============================================================================

if [ "$EUID" -ne 0 ]; then
    echo "[-] Please run as root: sudo bash $0"
    exit 1
fi

echo "=========================================================="
echo "          Optimizing System Daemons & Memory              "
echo "=========================================================="

# 1. Disable redundant background daemons
echo "[+] Disabling unnecessary background daemons..."

SERVICES_TO_DISABLE=(
    "ModemManager.service"        # Cellular modem manager (desktop has no WWAN)
    "cups-browsed.service"       # Remote CUPS printer discovery (high RAM / network chatter)
    "networkd-dispatcher.service"# Networkd dispatcher (Pop! uses NetworkManager)
    "apport.service"             # Automatic crash reporting daemon
)

for svc in "${SERVICES_TO_DISABLE[@]}"; do
    if systemctl list-unit-files "$svc" >/dev/null 2>&1; then
        echo "    -> Disabling and stopping $svc..."
        systemctl stop "$svc" 2>/dev/null || true
        systemctl disable "$svc" 2>/dev/null || true
    fi
done

# 2. Optimize systemd journal memory & disk footprint
echo "[+] Optimizing systemd-journald limits..."
mkdir -p /etc/systemd/journald.conf.d
cat << 'EOF' > /etc/systemd/journald.conf.d/00-limits.conf
[Journal]
SystemMaxUse=100M
RuntimeMaxUse=50M
MaxRetentionSec=1month
EOF
systemctl restart systemd-journald
journalctl --vacuum-size=100M 2>/dev/null || true

# 3. Kernel Sysctl Virtual Memory & IO Tuning
echo "[+] Applying kernel VM & responsiveness tuning..."
cat << 'EOF' > /etc/sysctl.d/99-performance.conf
# Retain directory and inode cache longer for snappier navigation
vm.vfs_cache_pressure = 50

# Flush dirty pages to disk in smaller, smooth intervals
vm.dirty_background_ratio = 5
vm.dirty_ratio = 10

# Inotify watches for modern dev tools and file managers
fs.inotify.max_user_watches = 524288
EOF
sysctl -p /etc/sysctl.d/99-performance.conf 2>/dev/null || true

# 4. Clean APT package cache and orphaned dependencies
echo "[+] Cleaning package manager caches..."
apt-get autoremove -y --purge >/dev/null 2>&1 || true
apt-get clean >/dev/null 2>&1 || true

echo ""
echo "=========================================================="
echo "          Optimization Complete!                          "
echo "=========================================================="
free -h
