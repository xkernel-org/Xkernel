#!/bin/bash
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[*] Installing dependencies ..."
sudo apt-get update -qq
sudo apt-get install -y -qq build-essential liburing-dev bpftrace

echo "[*] Building benchmark ..."
make -C "$SCRIPT_DIR" clean
make -C "$SCRIPT_DIR" -j"$(nproc)"

if [[ -x "$SCRIPT_DIR/bin/bench" ]]; then
    echo "[✓] bench built: $SCRIPT_DIR/bin/bench"
else
    echo "[✗] Build failed" >&2
    exit 1
fi
