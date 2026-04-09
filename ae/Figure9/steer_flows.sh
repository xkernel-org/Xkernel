#!/bin/bash
# steer_flows.sh — Steer iperf3 flows (dst port 5200-5202) to a specific RX queue
#                  using ethtool -U (ntuple / flow-director rules).
#
# Usage:
#   sudo bash steer_flows.sh [QUEUE] [IFACE]
#
# Examples:
#   sudo bash steer_flows.sh 3 ens1f1np1    # steer ports 5200-5202 → queue 3
#   sudo bash steer_flows.sh 5              # auto-detect interface

set -euo pipefail

QUEUE=${1:-3}
IFACE=${2:-$(ip -o link show up | awk -F': ' 'NR==2{print $2}')}

if [[ -z "${IFACE}" ]]; then
    echo "[!] Failed to detect a network interface"
    exit 1
fi

echo "[*] Steering dst-port 5200-5202 → RX queue $QUEUE on $IFACE"

# Disable irqbalance so it doesn't override our IRQ affinity
sudo systemctl stop irqbalance 2>/dev/null || true

# Enable ntuple filtering
sudo ethtool -K "$IFACE" ntuple on 2>/dev/null || true

# Add flow rules: steer TCP dst-port 5200/5201/5202 to the target queue
for port in 5200 5201 5202; do
    sudo ethtool -U "$IFACE" flow-type tcp4 dst-port "$port" action "$QUEUE" 2>/dev/null && \
        echo "  tcp4 dst-port $port → queue $QUEUE" || \
        echo "  [!] Failed to add rule for port $port"
done

# Pin the target queue's IRQ to the same CPU for best locality
# Find the IRQ for queue $QUEUE (e.g., mlx5_comp0@pci:... or ens1f1-TxRx-$QUEUE)
IRQ=$(grep -E "${IFACE}.*-${QUEUE}$|TxRx-${QUEUE}$" /proc/interrupts | awk -F: '{gsub(/ /,"",$1); print $1}' | head -1)
if [[ -n "$IRQ" ]]; then
    echo "$QUEUE" > "/proc/irq/$IRQ/smp_affinity_list" 2>/dev/null && \
        echo "[*] IRQ $IRQ (queue $QUEUE) pinned to CPU $QUEUE" || true
fi

echo ""
echo "[*] Current ntuple rules:"
sudo ethtool -u "$IFACE" 2>/dev/null | tail -20 || true

echo "[✓] Flow steering configured"