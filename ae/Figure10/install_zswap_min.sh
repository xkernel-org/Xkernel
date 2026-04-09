#!/bin/bash
# install_zswap_min.sh — Build zswap_min benchmark and install dependencies
#
# Usage:
#   bash ae/Figure10/install_zswap_min.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[*] Installing dependencies ..."
sudo apt-get update -qq
sudo apt-get install -y -qq build-essential numactl stress-ng

echo "[*] Building zswap_min ..."
make -C "$SCRIPT_DIR" clean
make -C "$SCRIPT_DIR" -j"$(nproc)"

if [[ -x "$SCRIPT_DIR/bin/zswap_min" ]]; then
    echo "[✓] zswap_min built: $SCRIPT_DIR/bin/zswap_min"
else
    echo "[✗] Build failed" >&2
    exit 1
fi
