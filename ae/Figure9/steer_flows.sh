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
IFACE=${2:-$(ip route get 192.168.6.2 2>/dev/null | awk '{for(i=1;i<=NF;i++) if($i=="dev") print $(i+1); exit}')}

if [[ -z "${IFACE}" ]]; then
    # fallback: second non-lo interface
    IFACE=$(ip -o link show up | awk -F': ' '!/lo/{print $2; exit}')
fi

if [[ -z "${IFACE}" ]]; then
    echo "[!] Failed to detect a network interface"
    exit 1
fi

echo "[*] Steering dst-port 5200-5202 → RX queue $QUEUE on $IFACE"

# Disable irqbalance so it doesn't override our IRQ affinity
sudo systemctl stop irqbalance 2>/dev/null || true

# Disable GRO so each packet is processed individually in softirq
sudo ethtool -K "$IFACE" gro off 2>/dev/null && \
    echo "[*] GRO disabled on $IFACE" || true

# Reduce interrupt coalescing for more frequent softirq processing
sudo ethtool -C "$IFACE" adaptive-rx off rx-usecs 4 rx-frames 16 2>/dev/null && \
    echo "[*] Interrupt coalescing reduced" || true

# Enable ntuple filtering
sudo ethtool -K "$IFACE" ntuple on 2>/dev/null || true

# Add flow rules: steer TCP+UDP dst-port 5200/5201/5202 to the target queue
for port in 5200 5201 5202; do
    sudo ethtool -U "$IFACE" flow-type tcp4 dst-port "$port" action "$QUEUE" 2>/dev/null && \
        echo "  tcp4 dst-port $port → queue $QUEUE" || \
        echo "  [!] Failed to add tcp4 rule for port $port"
    sudo ethtool -U "$IFACE" flow-type udp4 dst-port "$port" action "$QUEUE" 2>/dev/null && \
        echo "  udp4 dst-port $port → queue $QUEUE" || \
        echo "  [!] Failed to add udp4 rule for port $port"
done

# Pin the target queue's IRQ to the same CPU for best locality
IRQ=$(grep -E "${IFACE}.*-${QUEUE}$|TxRx-${QUEUE}$|${IFACE}-${QUEUE}$" /proc/interrupts | awk -F: '{gsub(/ /,"",$1); print $1}' | head -1)
if [[ -z "$IRQ" ]]; then
    # Try broader match for mlx5 NICs (e.g., "mlx5_comp3@pci:...")
    IRQ=$(grep "${IFACE}" /proc/interrupts | awk -F: '{gsub(/ /,"",$1); print $1}' | sed -n "$((QUEUE+1))p")
fi
if [[ -n "$IRQ" ]]; then
    echo "$QUEUE" > "/proc/irq/$IRQ/smp_affinity_list" 2>/dev/null && \
        echo "[*] IRQ $IRQ (queue $QUEUE) pinned to CPU $QUEUE" || true
fi

echo ""
echo "[*] Current ntuple rules:"
sudo ethtool -u "$IFACE" 2>/dev/null | tail -20 || true

echo "[✓] Flow steering configured"