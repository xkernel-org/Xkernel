#!/bin/bash
# steer_flows.sh — Redirect all NIC RX flows to a single CPU core
#
# Usage: sudo bash steer_flows.sh [CPU] [IFACE]

CPU=${1:-3}
IFACE=${2:-$(ip -o link show up | awk -F': ' 'NR==2{print $2}')}

echo "[*] Steering all RX flows on $IFACE → CPU $CPU"

# Disable irqbalance so it doesn't override our settings
systemctl stop irqbalance 2>/dev/null || true

# Set RPS (Receive Packet Steering) to target CPU
CPU_MASK=$(printf '%x' $((1 << CPU)))
for rxq in /sys/class/net/"$IFACE"/queues/rx-*/rps_cpus; do
    echo "$CPU_MASK" > "$rxq" 2>/dev/null && echo "  $rxq → $CPU_MASK"
done

# Also pin NIC IRQs to the target CPU if possible
for irq_dir in /proc/irq/*/; do
    if grep -ql "$IFACE" "$irq_dir/affinity_list" 2>/dev/null || \
       grep -ql "$IFACE" /proc/interrupts 2>/dev/null; then
        irq_num=$(basename "$irq_dir")
        echo "$CPU" > "$irq_dir/smp_affinity_list" 2>/dev/null && \
            echo "  IRQ $irq_num → CPU $CPU"
    fi
done

echo "[✓] Flow steering configured"
