#!/bin/bash
# setup_ssh.sh — Set up inter-node SSH for CloudLab experiments
#
# CloudLab nodes share /users/ via NFS, so ~/.ssh/ is the same on all nodes.
# We generate a key pair and add it to our own authorized_keys — this
# enables SSH between all nodes in the experiment.
#
# Usage:
#   bash setup_ssh.sh [CLIENT_IP]
#   bash setup_ssh.sh                  # default: 192.168.6.2

set -euo pipefail

CLIENT_IP="${1:-192.168.6.2}"

echo "[*] Configuring SSH for $CLIENT_IP ..."

# Generate SSH key if not present
if [[ ! -f "$HOME/.ssh/id_rsa" ]]; then
    echo "[*] Generating SSH key ..."
    ssh-keygen -t rsa -b 4096 -N "" -f "$HOME/.ssh/id_rsa" -q
fi

# Authorize our own key (NFS-shared home → works on all nodes)
if ! grep -qF "$(cat "$HOME/.ssh/id_rsa.pub")" "$HOME/.ssh/authorized_keys" 2>/dev/null; then
    cat "$HOME/.ssh/id_rsa.pub" >> "$HOME/.ssh/authorized_keys"
    chmod 600 "$HOME/.ssh/authorized_keys"
    echo "[✓] Public key added to authorized_keys"
else
    echo "[✓] Public key already in authorized_keys"
fi

# Add client to known_hosts (skip host key prompt)
ssh-keyscan -H "$CLIENT_IP" >> "$HOME/.ssh/known_hosts" 2>/dev/null

# Verify connectivity
echo "[*] Verifying SSH connection ..."
if ssh -o BatchMode=yes -o ConnectTimeout=5 "$CLIENT_IP" "hostname"; then
    echo "[✓] SSH to $CLIENT_IP works."
else
    echo "[✗] Cannot SSH to $CLIENT_IP."
    exit 1
fi
