#!/usr/bin/env bash
# ae/common.sh — Shared helpers for artifact evaluation scripts
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
RESULTS_DIR="$SCRIPT_DIR/results"
XKTOOL="$PROJECT_ROOT/xkernel-tool"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BOLD='\033[1m'
CYAN='\033[36m'
RST='\033[0m'

mkdir -p "$RESULTS_DIR"

# Log with timestamp
log() {
    echo -e "${BOLD}[$(date '+%H:%M:%S')]${RST} $*"
}

log_ok() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')] ✓${RST} $*"
}

log_err() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ✗${RST} $*"
}

log_section() {
    echo ""
    echo -e "${BOLD}${CYAN}════════════════════════════════════════════════════${RST}"
    echo -e "${BOLD}${CYAN}  $*${RST}"
    echo -e "${BOLD}${CYAN}════════════════════════════════════════════════════${RST}"
    echo ""
}

# Time a command and print duration
timed() {
    local start end duration
    start=$(date +%s)
    "$@"
    local rc=$?
    end=$(date +%s)
    duration=$((end - start))
    log "  Duration: ${duration}s"
    return $rc
}

# Check we're running as root
require_root() {
    if [[ $EUID -ne 0 ]]; then
        log_err "This experiment requires root. Run with: sudo bash $0"
        exit 1
    fi
}

# Check xkernel kernel is running
require_xkernel() {
    local kver
    kver=$(uname -r)
    if [[ "$kver" != *xkernel* ]]; then
        log_err "Not running xkernel kernel (current: $kver)"
        log_err "Boot into the xkernel kernel first."
        exit 1
    fi
}

# Build a tunable if not already built
ensure_built() {
    local toml_file="$1"
    log "Building from $toml_file..."
    "$XKTOOL" build "$toml_file" --skip-gen 2>&1 || "$XKTOOL" build "$toml_file" 2>&1
}

# Load a ConstID, run workload, collect result, unload
run_with_value() {
    local mode="$1"
    local const_id="$2"
    local value="$3"
    local workload_cmd="$4"
    local result_file="$5"

    log "  Loading ConstID=$const_id mode=$mode value=$value"
    sudo "$XKTOOL" load "$mode" "$const_id" 2>&1 || true

    log "  Running workload..."
    eval "$workload_cmd" >> "$result_file" 2>&1

    log "  Unloading ConstID=$const_id"
    sudo "$XKTOOL" unload "$const_id" 2>&1 || true
}

# Save experiment metadata
save_metadata() {
    local exp_name="$1"
    local output="$RESULTS_DIR/${exp_name}_meta.txt"
    {
        echo "Experiment: $exp_name"
        echo "Date: $(date -Iseconds)"
        echo "Kernel: $(uname -r)"
        echo "Machine: $(hostname)"
        echo "CPU: $(lscpu | grep 'Model name' | sed 's/.*: *//')"
        echo "Cores: $(nproc)"
        echo "Memory: $(free -h | awk '/^Mem:/ {print $2}')"
    } > "$output"
    log "Saved metadata: $output"
}
