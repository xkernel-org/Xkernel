#!/bin/bash
# setup_ssh.sh — Set up inter-node SSH for CloudLab experiments
#
# CloudLab nodes have local (non-shared) home directories. This script
# generates a user keypair, then uses root SSH (set up by Emulab) to
# install the public key on the remote node.
#
# Usage:
#   bash setup_ssh.sh [CLIENT_IP]
#   bash setup_ssh.sh                  # default: 192.168.6.2

set -euo pipefail

CLIENT_IP="${1:-192.168.6.2}"
USER="$(whoami)"

echo "[*] Configuring SSH to $CLIENT_IP ..."

# Generate SSH key if not present
if [[ ! -f "$HOME/.ssh/id_rsa" ]]; then
    echo "[*] Generating SSH key ..."
    ssh-keygen -t rsa -b 4096 -N "" -f "$HOME/.ssh/id_rsa" -q
fi

PUBKEY="$(cat "$HOME/.ssh/id_rsa.pub")"

# Use root SSH (Emulab-configured) to install the public key on the remote node
echo "[*] Installing public key on $CLIENT_IP via root SSH ..."
sudo ssh -o StrictHostKeyChecking=no "$CLIENT_IP" \
    "grep -qF '${PUBKEY}' /users/${USER}/.ssh/authorized_keys 2>/dev/null \
     || echo '${PUBKEY}' >> /users/${USER}/.ssh/authorized_keys"

# Add client to known_hosts
ssh-keyscan -H "$CLIENT_IP" >> "$HOME/.ssh/known_hosts" 2>/dev/null

# Verify
echo "[*] Verifying SSH connection ..."
if ssh -o BatchMode=yes -o ConnectTimeout=5 "$CLIENT_IP" "hostname"; then
    echo "[✓] SSH to $CLIENT_IP works."
else
    echo "[✗] Cannot SSH to $CLIENT_IP."
    exit 1
fi
