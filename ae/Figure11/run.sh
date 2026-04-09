#!/usr/bin/env bash
# run.sh — Reproduce Figure 11: NUMA page migration latency under different
#           NR_MAX_BATCHED_MIGRATION values
#
# This script:
#   1. Disables numa_balancing
#   2. Runs baseline (NR_MAX_BATCHED_MIGRATION=512, kernel default)
#   3. For each tuned value: tune via KernelX, run benchmark, unload
#   4. Results saved to results/<timestamp>/
#
# The experiment uses the "high migration pressure" configuration:
#   - 24 query workers, 2 migration threads
#   - Rolling hot set (rotate every 1s, full-width step)
#   - 8 GiB total memory, pages migrated from NUMA node 1 → node 0
#
# Usage:
#   bash ae/Figure11/run.sh
#
# Prerequisites:
#   - Custom kernel (6.14.0-xkernel) running
#   - bash ae/Figure11/install_benchmark.sh  (build benchmark)
#   - sudo bash build.sh                     (build KernelX)
#   - 2+ NUMA nodes required

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
XKTOOL="$PROJECT_ROOT/xkernel-tool"
TUNE_SCRIPT="$SCRIPT_DIR/tune_nr_max_batched_migration.sh"
BENCHMARK="$SCRIPT_DIR/bin/benchmark"

# Benchmark parameters (matching yltang's high-pressure config)
PAGES=2097152          # 8 GiB
WORKERS=24
MIGRATES=2
SRC_NODE=1
DST_NODE=0
BATCH=8192             # user-space collection cap (larger than kernel batch)
MIGRATE_INTERVAL=0
HOT_FRAC=0.20
HOT_PROB=0.80
HOT_ROTATE=1
ROTATE_STEP="full"
DRAIN_PER_WINDOW=0
QPS_SAMPLE_MS=10
PROBE_OPS=2000
PROBE_PERIOD_MS=50
DURATION=30
REPEATS=1

# NR_MAX_BATCHED_MIGRATION values to test (512 is baseline/kernel default)
BASELINE_VALUE=512
TUNED_VALUES=(32 64 128 256 1024)

RESULT_DIR="$SCRIPT_DIR/results"

RED='\033[0;31m'; GREEN='\033[0;32m'; BOLD='\033[1m'; RST='\033[0m'
log()         { echo -e "${BOLD}[$(date '+%H:%M:%S')]${RST} $*"; }
log_ok()      { echo -e "${GREEN}[$(date '+%H:%M:%S')] ✓${RST} $*"; }
log_section() { echo -e "\n${BOLD}════════════════════════════════════════${RST}"; log "$*"; echo -e "${BOLD}════════════════════════════════════════${RST}"; }
die()         { echo -e "${RED}[$(date '+%H:%M:%S')] ✗${RST} $*" >&2; exit 1; }

# ── Preflight checks ────────────────────────────────────────────────
[[ -x "$BENCHMARK" ]] || die "benchmark not found. Run: bash install_benchmark.sh"
[[ -x "$XKTOOL" ]]    || die "xkernel-tool not found at $XKTOOL"

# Check NUMA availability
if ! command -v numactl &>/dev/null; then
    die "numactl not found. Run: bash install_benchmark.sh"
fi
NUMA_NODES=$(numactl --hardware 2>/dev/null | grep "available:" | awk '{print $2}')
[[ "$NUMA_NODES" -ge 2 ]] || die "Need at least 2 NUMA nodes (found: $NUMA_NODES)"

mkdir -p "$RESULT_DIR"

# ── Setup environment ────────────────────────────────────────────────
setup_env() {
    log_section "Setting up environment"

    # Disable automatic NUMA balancing
    echo 0 | sudo tee /proc/sys/kernel/numa_balancing > /dev/null
    log "numa_balancing = $(cat /proc/sys/kernel/numa_balancing)"

    log_ok "Environment configured"
}

# ── Run benchmark for a given NR_MAX_BATCHED_MIGRATION value ─────────
run_benchmark() {
    local batch_value="$1"
    local outfile="$RESULT_DIR/${batch_value}.txt"

    log "Running benchmark (NR_MAX_BATCHED_MIGRATION=$batch_value, $REPEATS repeats) → $outfile"

    for i in $(seq 1 "$REPEATS"); do
        log "  Repeat $i/$REPEATS ..."

        # Drop caches between runs
        sync
        echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null
        sleep 1

        sudo "$BENCHMARK" \
            --pages "$PAGES" \
            --workers "$WORKERS" \
            --migrates "$MIGRATES" \
            --src "$SRC_NODE" \
            --dst "$DST_NODE" \
            --batch "$BATCH" \
            --migrate-interval "$MIGRATE_INTERVAL" \
            --hot-frac "$HOT_FRAC" \
            --hot-prob "$HOT_PROB" \
            --hot-rotate "$HOT_ROTATE" \
            --rotate-step "$ROTATE_STEP" \
            --drain-per-window "$DRAIN_PER_WINDOW" \
            --only-src --restat \
            --qps-sample-ms "$QPS_SAMPLE_MS" \
            --probe "$PROBE_OPS" "$PROBE_PERIOD_MS" \
            --duration "$DURATION" \
            >> "$outfile" 2>&1
    done

    if [[ -f "$outfile" ]]; then
        log_ok "  Results saved → $outfile"
    else
        log "  WARNING: Output file not created"
    fi
}

# ── Summarize results ────────────────────────────────────────────────
summarize_results() {
    local batch_value="$1"
    local outfile="$RESULT_DIR/${batch_value}.txt"

    if [[ -f "$outfile" ]]; then
        log "Summarizing $outfile ..."
        python3 "$SCRIPT_DIR/plot/summarize.py" "$outfile"
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
        echo "PAGES=$PAGES"
        echo "WORKERS=$WORKERS"
        echo "MIGRATES=$MIGRATES"
        echo "SRC_NODE=$SRC_NODE DST_NODE=$DST_NODE"
        echo "BATCH=$BATCH"
        echo "HOT_FRAC=$HOT_FRAC HOT_PROB=$HOT_PROB"
        echo "HOT_ROTATE=$HOT_ROTATE ROTATE_STEP=$ROTATE_STEP"
        echo "DRAIN_PER_WINDOW=$DRAIN_PER_WINDOW"
        echo "DURATION=$DURATION"
        echo "REPEATS=$REPEATS"
        echo "BASELINE_VALUE=$BASELINE_VALUE"
        echo "TUNED_VALUES=${TUNED_VALUES[*]}"
    } > "$RESULT_DIR/log.txt"
}

# ── Main ─────────────────────────────────────────────────────────────

save_log
setup_env

# ── Baseline: NR_MAX_BATCHED_MIGRATION = 512 (kernel default) ────────
log_section "Baseline: NR_MAX_BATCHED_MIGRATION = $BASELINE_VALUE (kernel default)"
run_benchmark "$BASELINE_VALUE"
summarize_results "$BASELINE_VALUE"

# ── Tuned runs ───────────────────────────────────────────────────────
for val in "${TUNED_VALUES[@]}"; do
    log_section "Tuning NR_MAX_BATCHED_MIGRATION = $val"

    # Unload previous tunable if loaded
    sudo bash "$TUNE_SCRIPT" unload 2>/dev/null || true
    sudo "$XKTOOL" table delete --all -y 2>/dev/null || true
    rm -rf "$PROJECT_ROOT/bpf/stubs/"* 2>/dev/null || true

    # Tune to new value
    sudo bash "$TUNE_SCRIPT" "$val"

    # Run benchmark
    run_benchmark "$val"
    summarize_results "$val"

    # Unload and clean up
    sudo bash "$TUNE_SCRIPT" unload 2>/dev/null || true
    sudo "$XKTOOL" table delete --all -y 2>/dev/null || true
    rm -rf "$PROJECT_ROOT/bpf/stubs/"* 2>/dev/null || true
done

# ── Cleanup ──────────────────────────────────────────────────────────
log_section "Cleanup"
sudo "$XKTOOL" table delete --all -y 2>/dev/null || true
rm -rf "$PROJECT_ROOT/bpf/stubs/"* 2>/dev/null || true

# Re-enable numa_balancing
echo 1 | sudo tee /proc/sys/kernel/numa_balancing > /dev/null 2>&1 || true

log_ok "Figure 11 experiment complete."
log "Results in: $RESULT_DIR/"
ls -la "$RESULT_DIR/"
log ""
log "Next steps:"
log "  python plot/plot.py       # → plot/figure11.pdf"
