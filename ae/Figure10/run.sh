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
#   sudo bash ae/Figure10/run.sh
#
# Prerequisites:
#   - Custom kernel (6.14.0-xkernel) running
#   - bash ae/Figure10/install_zswap_min.sh  (build benchmark)
#   - sudo bash build.sh                    (build KernelX)
#   - A swapfile must exist (swapon --show)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
XKTOOL="$PROJECT_ROOT/xkernel-tool"
TUNE_SCRIPT="$SCRIPT_DIR/tune_shrink_batch.sh"
ZSWAP_MIN="$SCRIPT_DIR/bin/zswap_min"

# Benchmark parameters (matching yltang's configuration)
TOTAL_MB=4096
BLOCK_PAGES=128
REUSE_DIST=16
WARMUP_PASSES=3
BURST=12
LOOPS=2000

# SHRINK_BATCH values to test (128 is baseline)
BASELINE_VALUE=128
TUNED_VALUES=(8 16 24 28 32 64)

TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
RESULT_DIR="$SCRIPT_DIR/results/$TIMESTAMP"
UNIT_NAME="zswap_min_fig10"

RED='\033[0;31m'; GREEN='\033[0;32m'; BOLD='\033[1m'; RST='\033[0m'
log()         { echo -e "${BOLD}[$(date '+%H:%M:%S')]${RST} $*"; }
log_ok()      { echo -e "${GREEN}[$(date '+%H:%M:%S')] ✓${RST} $*"; }
log_section() { echo -e "\n${BOLD}════════════════════════════════════════${RST}"; log "$*"; echo -e "${BOLD}════════════════════════════════════════${RST}"; }
die()         { echo -e "${RED}[$(date '+%H:%M:%S')] ✗${RST} $*" >&2; exit 1; }

# ── Preflight checks ────────────────────────────────────────────────
[[ -x "$ZSWAP_MIN" ]] || die "zswap_min not found. Run: bash install_zswap_min.sh"
[[ -x "$XKTOOL" ]]    || die "xkernel-tool not found at $XKTOOL"
[[ $(id -u) -eq 0 ]]  || die "Must run as root: sudo bash $0"

mkdir -p "$RESULT_DIR"

# ── Setup zswap environment ─────────────────────────────────────────
setup_zswap() {
    log_section "Setting up zswap environment"

    # Stop zram if running
    systemctl stop zramswap.service 2>/dev/null || true

    # Enable zswap and shrinker
    echo 1 > /sys/module/zswap/parameters/enabled
    echo Y > /sys/module/zswap/parameters/shrinker_enabled

    # Lower pool limit to make writeback more aggressive
    echo 5 > /sys/module/zswap/parameters/max_pool_percent

    # Mount debugfs
    mount -t debugfs none /sys/kernel/debug 2>/dev/null || true

    # Increase swappiness
    sysctl -w vm.swappiness=180

    # Disable THP
    echo never > /sys/kernel/mm/transparent_hugepage/enabled
    echo never > /sys/kernel/mm/transparent_hugepage/defrag

    # Default zswap parameters
    echo zbud > /sys/module/zswap/parameters/zpool
    echo lzo  > /sys/module/zswap/parameters/compressor

    log_ok "zswap environment configured"
    log "  enabled=$(cat /sys/module/zswap/parameters/enabled)"
    log "  shrinker=$(cat /sys/module/zswap/parameters/shrinker_enabled)"
    log "  max_pool_percent=$(cat /sys/module/zswap/parameters/max_pool_percent)"
    log "  swappiness=$(sysctl -n vm.swappiness)"
}

# ── Run benchmark for a given SHRINK_BATCH value ─────────────────────
run_benchmark() {
    local batch_value="$1"
    local outfile="$RESULT_DIR/${batch_value}.txt"

    log "Running zswap_min (SHRINK_BATCH=$batch_value) → $outfile"

    # Drop caches before each run
    sync
    echo 3 > /proc/sys/vm/drop_caches
    sleep 2

    systemd-run --unit="$UNIT_NAME" \
        -p MemoryHigh=1G \
        -p MemoryMax=1200M \
        -p MemorySwapMax=6G \
        --same-dir --collect --wait \
        numactl --cpunodebind=0 --membind=0 \
        "$ZSWAP_MIN" \
            --total-mb "$TOTAL_MB" \
            --block-pages "$BLOCK_PAGES" \
            --reuse-dist "$REUSE_DIST" \
            --warmup-passes "$WARMUP_PASSES" \
            --burst "$BURST" \
            --loops "$LOOPS" \
            --file "$outfile" \
        2>&1 | tee -a "$RESULT_DIR/log.txt"

    if [[ -f "$outfile" ]]; then
        local lines
        lines=$(wc -l < "$outfile")
        log_ok "  Collected $lines iterations → $outfile"
    else
        log "  WARNING: Output file not created"
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

save_log
setup_zswap

# ── Baseline: SHRINK_BATCH = 128 (kernel default, no tuning) ─────────
log_section "Baseline: SHRINK_BATCH = $BASELINE_VALUE (kernel default)"
run_benchmark "$BASELINE_VALUE"

# ── Tuned runs ───────────────────────────────────────────────────────
for val in "${TUNED_VALUES[@]}"; do
    log_section "Tuning SHRINK_BATCH = $val"

    # Unload previous tunable if loaded
    bash "$TUNE_SCRIPT" unload 2>/dev/null || true
    "$XKTOOL" table delete --all -y 2>/dev/null || true
    rm -rf "$PROJECT_ROOT/bpf/stubs/"* 2>/dev/null || true

    # Tune to new value
    bash "$TUNE_SCRIPT" "$val"

    # Run benchmark
    run_benchmark "$val"

    # Unload
    bash "$TUNE_SCRIPT" unload 2>/dev/null || true
done

# ── Cleanup ──────────────────────────────────────────────────────────
log_section "Cleanup"
"$XKTOOL" table delete --all -y 2>/dev/null || true
rm -rf "$PROJECT_ROOT/bpf/stubs/"* 2>/dev/null || true

log_ok "Figure 10 experiment complete."
log "Results in: $RESULT_DIR/"
ls -la "$RESULT_DIR/"
