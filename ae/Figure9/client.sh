#!/bin/bash
# client.sh — Start iperf3 Net-APP traffic (run on client machines)
#
# Generates 6 TCP connections (2 per port) with 1KB writes.
# With GRO ON and flow steering, this produces ~80% softirq CPU
# on the target core — enough for MAX_SOFTIRQ_RESTART to matter.
#
# Usage:
#   bash client.sh                     # default server: 192.168.6.1
#   bash client.sh 10.0.0.1            # custom server IP

SERVER=${1:-192.168.6.1}
DURATION=6000

echo "[*] Starting iperf3 TCP clients → $SERVER (duration=${DURATION}s)"

iperf3 -c "$SERVER" -P 2 -l 1k -p 5200 -t "$DURATION" &
iperf3 -c "$SERVER" -P 2 -l 1k -p 5201 -t "$DURATION" &
iperf3 -c "$SERVER" -P 2 -l 1k -p 5202 -t "$DURATION" &

echo "[✓] 3 iperf3 TCP instances (6 connections) running (ports 5200-5202)"
echo "    Kill with: kill %1 %2 %3"
wait
