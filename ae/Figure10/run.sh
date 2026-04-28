#!/usr/bin/env bash
# run.sh — Reproduce Figure 10: zswap shrinker latency under different SHRINK_BATCH values
#
# This script:
#   1. Sets up zswap environment (enable zswap, shrinker, configure parameters)
#   2. Runs baseline (SHRINK_BATCH=128, kernel default)
#   3. For each tuned value: tune via KernelX, run benchmark, unload
#   4. Results saved to results/<timestamp>/
#
# Usage:
#   bash ae/Figure10/run.sh
#
# Prerequisites:
#   - Linux 6.14.8-061408-generic running
#   - KERNEL_DIR=~/linux-6.14.8-061408-generic
#   - gcc-14 and g++-14 installed for Linux 6.14.8 kernel module builds
#   - bash ae/Figure10/install_zswap_min.sh  (build benchmark)
#   - A swapfile must exist (swapon --show)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
XKTOOL="$PROJECT_ROOT/xkernel-tool"
TUNE_SCRIPT="$SCRIPT_DIR/tune_shrink_batch.sh"
ZSWAP_MIN="$SCRIPT_DIR/bin/zswap_min"

# Benchmark parameters
TOTAL_MB=4096
BLOCK_PAGES=128
REUSE_DIST=16
WARMUP_PASSES=2
BURST=12
LOOPS=500
EXPECTED_RESULT_LINES=$((LOOPS + 2))

# SHRINK_BATCH values to test (128 is baseline)
BASELINE_VALUE=128
TUNED_VALUES=(8 16 24 28 32 64)

RESULT_DIR="$SCRIPT_DIR/results"
UNIT_NAME="zswap_min_fig10"

RED='\033[0;31m'; GREEN='\033[0;32m'; BOLD='\033[1m'; RST='\033[0m'
log()         { echo -e "${BOLD}[$(date '+%H:%M:%S')]${RST} $*"; }
log_ok()      { echo -e "${GREEN}[$(date '+%H:%M:%S')] ✓${RST} $*"; }
log_section() { echo -e "\n${BOLD}════════════════════════════════════════${RST}"; log "$*"; echo -e "${BOLD}════════════════════════════════════════${RST}"; }
die()         { echo -e "${RED}[$(date '+%H:%M:%S')] ✗${RST} $*" >&2; exit 1; }

# ── Preflight checks ────────────────────────────────────────────────
[[ -x "$ZSWAP_MIN" ]] || die "zswap_min not found. Run: bash install_zswap_min.sh"
[[ -x "$XKTOOL" ]]    || die "xkernel-tool not found at $XKTOOL"
command -v gcc-14 >/dev/null 2>&1 || die "gcc-14 not found. Install it with: sudo apt-get install -y gcc-14 g++-14"
command -v g++-14 >/dev/null 2>&1 || die "g++-14 not found. Install it with: sudo apt-get install -y gcc-14 g++-14"

# Linux 6.14.8-061408-generic headers were built with GCC 14. Use the same
# compiler for Xkernel's kernel modules; otherwise module builds can fail on
# GCC-14-only flags such as -fmin-function-alignment=16.
export CC="${CC:-gcc-14}"
export CXX="${CXX:-g++-14}"

mkdir -p "$RESULT_DIR"

# ── Resume/idempotency helpers ───────────────────────────────────────
result_file() {
    local batch_value="$1"
    echo "$RESULT_DIR/${batch_value}.txt"
}

result_complete() {
    local outfile="$1"
    [[ -f "$outfile" ]] || return 1

    local lines
    lines=$(wc -l < "$outfile")
    [[ "$lines" -ge "$EXPECTED_RESULT_LINES" ]]
}

all_results_complete() {
    local val
    result_complete "$(result_file "$BASELINE_VALUE")" || return 1
    for val in "${TUNED_VALUES[@]}"; do
        result_complete "$(result_file "$val")" || return 1
    done
    return 0
}

prepare_output_file() {
    local outfile="$1"
    [[ -f "$outfile" ]] || return 0

    if result_complete "$outfile"; then
        return 0
    fi

    local backup="${outfile}.partial.$(date '+%Y%m%d-%H%M%S')"
    log "Preserving incomplete result: $outfile → $backup"
    sudo mv "$outfile" "$backup"
}

cleanup_stale_xkernel_state() {
    log_section "Clearing stale Xkernel runtime state"
    sudo "$XKTOOL" unload --all 2>/dev/null || true
    sudo rmmod xk_kfuncs 2>/dev/null || true
    log_ok "stale Xkernel runtime state cleared"
}

xkernel_build_ready() {
    [[ -s /dev/shm/xkernel/scope_table ]] || return 1
    awk -F'\t' 'NR>1 && $6 ~ /xtune_stub_.*\.bpf\.o/ {found=1} END {exit !found}' /dev/shm/xkernel/scope_table || return 1
    compgen -G "$PROJECT_ROOT/bpf/stubs/xtune_stub_*.bpf.c" > /dev/null || return 1
    compgen -G "$PROJECT_ROOT/bpf/stubs/xtune_stub_*.bpf.h" > /dev/null || return 1
    compgen -G "$PROJECT_ROOT/bpf/stubs/xtune_stub_*.bpf.o" > /dev/null || return 1
}

# ── Setup zswap environment ─────────────────────────────────────────
setup_zswap() {
    log_section "Setting up zswap environment"

    # Stop zram if running
    sudo systemctl stop zramswap.service 2>/dev/null || true

    # Enable zswap and shrinker
    echo 1 | sudo tee /sys/module/zswap/parameters/enabled > /dev/null
    echo Y | sudo tee /sys/module/zswap/parameters/shrinker_enabled > /dev/null

    # Lower pool limit to make writeback more aggressive
    echo 5 | sudo tee /sys/module/zswap/parameters/max_pool_percent > /dev/null

    # Mount debugfs
    sudo mount -t debugfs none /sys/kernel/debug 2>/dev/null || true

    # Increase swappiness
    sudo sysctl -w vm.swappiness=180

    # Disable THP
    echo never | sudo tee /sys/kernel/mm/transparent_hugepage/enabled > /dev/null
    echo never | sudo tee /sys/kernel/mm/transparent_hugepage/defrag > /dev/null

    # Default zswap parameters
    echo zbud | sudo tee /sys/module/zswap/parameters/zpool > /dev/null
    echo lzo  | sudo tee /sys/module/zswap/parameters/compressor > /dev/null

    log_ok "zswap environment configured"
    log "  enabled=$(cat /sys/module/zswap/parameters/enabled)"
    log "  shrinker=$(cat /sys/module/zswap/parameters/shrinker_enabled)"
    log "  max_pool_percent=$(cat /sys/module/zswap/parameters/max_pool_percent)"
    log "  swappiness=$(sysctl -n vm.swappiness)"
}

# ── Run benchmark for a given SHRINK_BATCH value ─────────────────────
run_benchmark() {
    local batch_value="$1"
    local outfile
    outfile=$(result_file "$batch_value")

    if result_complete "$outfile"; then
        local lines
        lines=$(wc -l < "$outfile")
        log_ok "  Reusing existing $lines-iteration result → $outfile"
        return 0
    fi

    prepare_output_file "$outfile"

    log "Running zswap_min (SHRINK_BATCH=$batch_value) → $outfile"

    # Drop caches before each run
    sync
    echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null
    sleep 2

    sudo systemd-run --unit="$UNIT_NAME" \
        -p MemoryHigh=1G \
        -p MemoryMax=1200M \
        -p MemorySwapMax=6G \
        --same-dir --collect --pipe \
        numactl --cpunodebind=0 --membind=0 \
        /usr/bin/time -o "$outfile" --append \
        "$ZSWAP_MIN" \
            --total-mb "$TOTAL_MB" \
            --block-pages "$BLOCK_PAGES" \
            --reuse-dist "$REUSE_DIST" \
            --warmup-passes "$WARMUP_PASSES" \
            --burst "$BURST" \
            --loops "$LOOPS" \
            --file "$outfile" \
        2>&1 | tee -a "$RESULT_DIR/log.txt"

    if result_complete "$outfile"; then
        local lines
        lines=$(wc -l < "$outfile")
        log_ok "  Collected $lines iterations → $outfile"
    elif [[ -f "$outfile" ]]; then
        local lines
        lines=$(wc -l < "$outfile")
        die "Incomplete output: collected $lines lines, expected at least $EXPECTED_RESULT_LINES → $outfile"
    else
        die "Output file not created: $outfile"
    fi
}

# ── Save experiment metadata ─────────────────────────────────────────
save_log() {
    {
        echo "date:       $(date)"
        echo "git branch: $(cd "$PROJECT_ROOT" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')"
        echo "git commit: $(cd "$PROJECT_ROOT" && git rev-parse HEAD 2>/dev/null || echo 'unknown')"
        echo ""
        echo "=== parameters ==="
        echo "TOTAL_MB=$TOTAL_MB"
        echo "BLOCK_PAGES=$BLOCK_PAGES"
        echo "REUSE_DIST=$REUSE_DIST"
        echo "WARMUP_PASSES=$WARMUP_PASSES"
        echo "BURST=$BURST"
        echo "LOOPS=$LOOPS"
        echo "BASELINE_VALUE=$BASELINE_VALUE"
        echo "TUNED_VALUES=${TUNED_VALUES[*]}"
    } >> "$RESULT_DIR/log.txt"
}

# ── Main ─────────────────────────────────────────────────────────────

if all_results_complete; then
    log_section "All Figure 10 results already complete"
    log_ok "Skipping build and benchmark sweep. Results in: $RESULT_DIR/"
    ls -la "$RESULT_DIR/"
    exit 0
fi

save_log
cleanup_stale_xkernel_state
setup_zswap

# ── One-time build (kernel diff + codegen + BPF compile) ─────────────

if xkernel_build_ready; then
    log_section "Reusing existing SHRINK_BATCH tunable build"
    log_ok "Existing BPF stubs and scope table found"
else
    log_section "Building SHRINK_BATCH tunable (one-time)"
    sudo "$XKTOOL" table delete --all -y 2>/dev/null || true
    sudo rm -rf "$PROJECT_ROOT/bpf/stubs/"* 2>/dev/null || true
    sudo bash "$TUNE_SCRIPT" build
fi

# ── Baseline: SHRINK_BATCH = 128 (kernel default, no tuning) ─────────
log_section "Baseline: SHRINK_BATCH = $BASELINE_VALUE (kernel default)"
run_benchmark "$BASELINE_VALUE"

# ── Tuned runs (patch BPF stub only — no kernel rebuild) ─────────────
for val in "${TUNED_VALUES[@]}"; do
    if result_complete "$(result_file "$val")"; then
        log_section "Skipping SHRINK_BATCH = $val (complete result exists)"
        run_benchmark "$val"
        continue
    fi

    log_section "Tuning SHRINK_BATCH = $val"

    # Unload previous if loaded
    sudo bash "$TUNE_SCRIPT" unload 2>/dev/null || true

    # Patch BPF stub + recompile BPF + reload
    sudo bash "$TUNE_SCRIPT" "$val"

    # Run benchmark
    run_benchmark "$val"

    # Unload after this round
    sudo bash "$TUNE_SCRIPT" unload 2>/dev/null || true
done

# ── Cleanup ──────────────────────────────────────────────────────────
log_section "Cleanup"
sudo bash "$TUNE_SCRIPT" unload 2>/dev/null || true
sudo "$XKTOOL" table delete --all -y 2>/dev/null || true
sudo rm -rf "$PROJECT_ROOT/bpf/stubs/"* 2>/dev/null || true

log_ok "Figure 10 experiment complete."
log "Results in: $RESULT_DIR/"
ls -la "$RESULT_DIR/"
