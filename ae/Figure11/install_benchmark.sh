#!/bin/bash
# install_benchmark.sh — Build the NUMA migration benchmark and install dependencies
#
# Usage:
#   bash ae/Figure11/install_benchmark.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[*] Installing dependencies ..."
sudo apt-get update -qq
sudo apt-get install -y -qq build-essential numactl libnuma-dev

echo "[*] Building benchmark ..."
make -C "$SCRIPT_DIR" clean
make -C "$SCRIPT_DIR" -j"$(nproc)"

if [[ -x "$SCRIPT_DIR/bin/benchmark" ]]; then
    echo "[✓] benchmark built: $SCRIPT_DIR/bin/benchmark"
else
    echo "[✗] Build failed" >&2
    exit 1
fi
