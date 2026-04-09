#!/bin/bash
# steer_irqs_by_pci.sh — Pin NIC IRQs to one or more CPUs by matching PCI BDF
#
# Usage:
#   sudo bash steer_irqs_by_pci.sh [CPU_SPEC] [IFACE]
#
# Examples:
#   sudo bash steer_irqs_by_pci.sh 3 ens1f1np1
#   sudo bash steer_irqs_by_pci.sh 0-19 ens1f1np1
#   sudo bash steer_irqs_by_pci.sh 0,2,4-7 ens1f1np1

set -euo pipefail

CPU_SPEC=${1:-3}
IFACE=${2:-$(ip -o link show up | awk -F': ' 'NR==2{print $2}')}

if [[ -z "${IFACE}" ]]; then
    echo "[!] Failed to detect a network interface"
    exit 1
fi

if [[ ! -e "/sys/class/net/$IFACE/device" ]]; then
    echo "[!] Interface $IFACE does not have a device symlink"
    exit 1
fi

echo "[*] Steering NIC IRQs for $IFACE → CPUs $CPU_SPEC"

# Disable irqbalance so it doesn't override our settings
systemctl stop irqbalance 2>/dev/null || true

# Resolve PCI device path, e.g.
# /sys/devices/pci0000:00/0000:00:03.0/0000:03:00.1
PCI_PATH=$(readlink -f "/sys/class/net/$IFACE/device")
PCI_BDF=$(basename "$PCI_PATH")

if [[ ! "$PCI_BDF" =~ ^[0-9a-fA-F]{4}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}\.[0-7]$ ]]; then
    echo "[!] Failed to parse PCI BDF from: $PCI_PATH"
    exit 1
fi

echo "[*] PCI device path: $PCI_PATH"
echo "[*] PCI BDF: $PCI_BDF"

# Find IRQs in /proc/interrupts that belong to this PCI function
IRQ_LIST=$(
    awk -v bdf="$PCI_BDF" '
        index($0, "@pci:" bdf) {
            gsub(/:/, "", $1)
            print $1
        }
    ' /proc/interrupts | sort -u
)

if [[ -z "$IRQ_LIST" ]]; then
    echo "[!] No IRQs matched @pci:$PCI_BDF in /proc/interrupts"
    exit 1
fi

echo "[*] Matching IRQs:"
while read -r irq; do
    [[ -n "$irq" ]] && echo "  IRQ $irq"
done <<< "$IRQ_LIST"

# Pin matched IRQs to the requested CPU list/range
while read -r irq_num; do
    [[ -z "$irq_num" ]] && continue
    irq_file="/proc/irq/$irq_num/smp_affinity_list"
    if [[ -w "$irq_file" ]]; then
        echo "$CPU_SPEC" > "$irq_file"
        echo "  IRQ $irq_num → CPUs $CPU_SPEC"
    else
        echo "  [!] Cannot write $irq_file"
    fi
done <<< "$IRQ_LIST"

echo "[✓] IRQ steering configured"