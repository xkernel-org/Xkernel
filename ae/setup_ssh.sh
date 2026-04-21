#!/bin/bash
# setup_ssh.sh — Verify and configure SSH connectivity to the client machine
#
# On CloudLab, nodes in the same experiment already share SSH keys.
# This script verifies connectivity and adds the client to known_hosts.
#
# Usage:
#   bash setup_ssh.sh [CLIENT_IP]
#   bash setup_ssh.sh                  # default: 192.168.6.2

set -euo pipefail

CLIENT_IP="${1:-192.168.6.2}"

echo "[*] Configuring SSH for $CLIENT_IP ..."

# Add client to known_hosts (skip host key prompt)
ssh-keyscan -H "$CLIENT_IP" >> "$HOME/.ssh/known_hosts" 2>/dev/null
echo "[✓] Added $CLIENT_IP to known_hosts"

# Verify connectivity
echo "[*] Verifying SSH connection ..."
if ssh -o BatchMode=yes -o ConnectTimeout=5 "$CLIENT_IP" "hostname"; then
    echo "[✓] SSH to $CLIENT_IP works."
else
    echo "[✗] Cannot SSH to $CLIENT_IP. Check that both machines are in the same CloudLab experiment."
    exit 1
fi
