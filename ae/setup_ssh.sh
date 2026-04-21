#!/bin/bash
# setup_ssh.sh — Set up passwordless SSH between server and client
#
# Run this on the server (192.168.6.1) once before running any experiment
# that requires two machines (Figure 9, Figure 12, etc.).
#
# Usage:
#   bash setup_ssh.sh [CLIENT_IP]
#   bash setup_ssh.sh                  # default: 192.168.6.2

set -euo pipefail

CLIENT_IP="${1:-192.168.6.2}"

echo "[*] Setting up passwordless SSH to $CLIENT_IP ..."

# Generate SSH key if not present
if [[ ! -f "$HOME/.ssh/id_rsa" ]]; then
    echo "[*] Generating SSH key ..."
    ssh-keygen -t rsa -b 4096 -N "" -f "$HOME/.ssh/id_rsa"
fi

# Copy public key to client (will prompt for password once)
echo "[*] Copying SSH key to $CLIENT_IP (you may be prompted for a password) ..."
ssh-copy-id -o StrictHostKeyChecking=no "$CLIENT_IP"

# Verify
echo "[*] Verifying SSH connection ..."
ssh -o BatchMode=yes "$CLIENT_IP" "echo '[✓] SSH to $CLIENT_IP works ($(whoami)@$(hostname))'"

echo "[✓] Passwordless SSH configured. You can now run the experiment scripts."
