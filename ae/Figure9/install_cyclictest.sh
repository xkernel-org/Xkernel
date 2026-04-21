#!/bin/bash
# install_cyclictest.sh — Install dependencies for Figure 9 (server + client)
#
# Run on the server (192.168.6.1). Installs:
#   Server: rt-tests (cyclictest), iperf3
#   Client: iperf3 (via SSH)
#
# Usage:
#   bash install_cyclictest.sh [CLIENT_IP]

set -euo pipefail

CLIENT_IP="${1:-192.168.6.2}"

echo "[*] Installing server dependencies (rt-tests, iperf3) ..."
sudo apt-get update -qq
sudo apt-get install -y -qq rt-tests iperf3

echo "[*] Installing client dependencies on $CLIENT_IP (iperf3) ..."
ssh "$CLIENT_IP" "sudo apt-get update -qq && sudo apt-get install -y -qq iperf3"

echo "[✓] Installation complete (server + client)"
