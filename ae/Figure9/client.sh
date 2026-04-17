#!/bin/bash
# client.sh — Start iperf3 Net-APP traffic (run on client machines)
#
# Generates heavy softirq CPU usage on the server by sending
# 96 parallel UDP flows with small packets across 3 iperf3 instances.
# UDP + small packets (-l 128) maximizes packet rate → more softirq work.
#
# Usage:
#   bash client.sh                     # default server: 192.168.6.1
#   bash client.sh 10.0.0.1            # custom server IP

SERVER=${1:-192.168.6.1}
DURATION=6000

echo "[*] Starting iperf3 UDP clients → $SERVER (duration=${DURATION}s)"

iperf3 -u -c "$SERVER" -P 32 -l 128 -b 0 -p 5200 -t "$DURATION" &
iperf3 -u -c "$SERVER" -P 32 -l 128 -b 0 -p 5201 -t "$DURATION" &
iperf3 -u -c "$SERVER" -P 32 -l 128 -b 0 -p 5202 -t "$DURATION" &

echo "[✓] 3 iperf3 UDP instances running in background (ports 5200-5202)"
echo "    Kill with: kill %1 %2 %3"
wait
