#!/usr/bin/env bash
# Trigger workload for MAX_SOFTIRQ_RESTART (handle_softirqs).
#
# Generates high network/timer interrupt pressure to trigger softirq
# processing, which calls handle_softirqs() and hits the kprobe.
#
# Usage:
#   bash tests/workloads/trigger_softirq.sh [duration_sec]

set -euo pipefail

DURATION=${1:-30}

echo "[trigger_softirq] duration=${DURATION}s"

cleanup() {
    jobs -p 2>/dev/null | xargs -r kill 2>/dev/null || true
    wait 2>/dev/null || true
}
trap cleanup EXIT

DEADLINE=$((SECONDS + DURATION))

# Strategy: generate heavy network traffic to trigger NET_RX/TX softirqs
# plus timer-heavy workloads for TIMER_SOFTIRQ

# 1. Network pressure via loopback ping flood
ping -f -c $((DURATION * 10000)) 127.0.0.1 > /dev/null 2>&1 &

# 2. Many short-lived processes to trigger scheduler softirqs
while [ $SECONDS -lt $DEADLINE ]; do
    for _ in $(seq 1 50); do
        true &
    done
    wait 2>/dev/null || true
    # Drop caches to trigger RCU/timer softirqs
    echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null 2>&1 || true
done &

# 3. Heavy timer workload
if command -v stress-ng >/dev/null 2>&1; then
    timeout "${DURATION}" stress-ng --timer 4 --timeout "${DURATION}s" \
        2>/dev/null || true
else
    # Fallback: dd with sync to trigger IO completion softirqs
    while [ $SECONDS -lt $DEADLINE ]; do
        dd if=/dev/zero of=/dev/null bs=4k count=10000 status=none 2>/dev/null || true
    done
fi

wait 2>/dev/null || true
echo "[trigger_softirq] Done"
