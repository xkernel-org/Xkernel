#!/usr/bin/env bash
# run.sh — Reproduce Figure 16: kprobe trigger overhead on io_uring path
#
# Measures the per-trigger overhead of BPF kprobes attached to io_write()+0x6,
# comparing jump-optimized (JMP) vs INT3 kprobe mechanisms.
#
# Each io_uring write SQE triggers exactly one io_write() call.
# Writing 1 byte to /dev/null has near-zero I/O cost → kprobe overhead dominates.
#
# Three sweep modes:
#   base   — no kprobes attached (baseline)
#   xk     — jump-optimized kprobe at io_write+0x6 [OPTIMIZED] (~25 ns)
#
# Usage:
#   sudo bash ae/Figure16/run.sh [--delays 0,1,5,10] [--threads N]
#
# Prerequisites:
#   bash ae/Figure16/install_bench.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BENCH="$SCRIPT_DIR/bin/bench"

# ── Parameters ───────────────────────────────────────────────────────
DELAYS=(0 1 5 10)            # app-delay values to sweep (us)
THREADS=10                   # number of io_uring threads

while [[ $# -gt 0 ]]; do
    case "$1" in
        --delays)    IFS=',' read -ra DELAYS <<< "$2"; shift 2 ;;
        --threads)   THREADS="$2";   shift 2 ;;
        *)           echo "Unknown option: $1"; exit 1 ;;
    esac
done

# IOPS sweep: 100K–3M in 200K steps
IOPS_TARGETS=()
for (( r=100000; r<=3000000; r+=200000 )); do
    IOPS_TARGETS+=($r)
done

DATA_DIR="$SCRIPT_DIR/data"
KPROBE_TARGET="io_write+0x6"   # 5-byte MOV in prologue

RED='\033[0;31m'; GREEN='\033[0;32m'; BOLD='\033[1m'; RST='\033[0m'
log()         { echo -e "${BOLD}[$(date '+%H:%M:%S')]${RST} $*"; }
log_ok()      { echo -e "${GREEN}[$(date '+%H:%M:%S')] ✓${RST} $*"; }
log_section() { echo -e "\n${BOLD}════════════════════════════════════════${RST}"; log "$*"; echo -e "${BOLD}════════════════════════════════════════${RST}"; }
die()         { echo -e "${RED}[$(date '+%H:%M:%S')] ✗${RST} $*" >&2; exit 1; }

# ── Preflight ────────────────────────────────────────────────────────
log_section "Preflight checks"

# Clean previous results for idempotency
rm -f "$DATA_DIR"/*.txt 2>/dev/null || true

if [[ ! -x "$BENCH" ]]; then
    log "Building benchmark..."
    make -C "$SCRIPT_DIR" -j"$(nproc)"
fi
[[ -x "$BENCH" ]] || die "bench not found. Run: bash install_bench.sh"

grep -qw "io_write" /proc/kallsyms 2>/dev/null || \
    die "io_write not found in /proc/kallsyms"

TRACE_DIR=""
[[ -d /sys/kernel/tracing ]] && TRACE_DIR=/sys/kernel/tracing
[[ -d /sys/kernel/debug/tracing ]] && TRACE_DIR=/sys/kernel/debug/tracing
[[ -n "$TRACE_DIR" ]] || die "tracefs not found"

mkdir -p "$DATA_DIR"

log_ok "bench binary:  $BENCH"
log_ok "kprobe target: $KPROBE_TARGET"
log_ok "delays:        ${DELAYS[*]} us"
log_ok "threads:       ${THREADS}"
log_ok "IOPS targets:  ${#IOPS_TARGETS[@]} levels (${IOPS_TARGETS[0]}..${IOPS_TARGETS[-1]})"

# ── Save metadata ────────────────────────────────────────────────────
{
    echo "date:       $(date)"
    echo "kernel:     $(uname -r)"
    echo "delays:     ${DELAYS[*]} us"
    echo "threads:    $THREADS"
    echo "kprobe:     $KPROBE_TARGET"
    echo "iops_range: ${IOPS_TARGETS[0]}..${IOPS_TARGETS[-1]}"
} > "$DATA_DIR/log.txt"

# ── Helper: run one IOPS sweep ──────────────────────────────────────
run_sweep() {
    local label="$1"       # "base", "xk", or "xkint3"
    local delay="$2"       # app delay in us
    local prefix="${label}_${delay}"

    log_section "Sweep: $label (app_delay=${delay}us, threads=${THREADS})"

    for r in "${IOPS_TARGETS[@]}"; do
        local n=$((r * 2))
        local outfile="$DATA_DIR/${prefix}_${r}.txt"

        log "  IOPS=$r  n=$n → $(basename "$outfile")"
        "$BENCH" -d "$delay" -j "$THREADS" -r "$r" -n "$n" > "$outfile" 2>&1
    done

    log_ok "$label sweep done (${#IOPS_TARGETS[@]} data points)"
}

# ── Helper: attach / detach kprobe via debugfs ──────────────────────
KPROBE_NAME="xk_probe"

cleanup() {
    if [[ -d "$TRACE_DIR/events/kprobes/${KPROBE_NAME}" ]]; then
        echo 0 > "$TRACE_DIR/events/kprobes/${KPROBE_NAME}/enable" 2>/dev/null || true
        echo "-:${KPROBE_NAME}" >> "$TRACE_DIR/kprobe_events" 2>/dev/null || true
    fi
    echo 1 | tee /proc/sys/debug/kprobes-optimization > /dev/null 2>&1 || true
}
trap cleanup EXIT

attach_kprobe() {
    # Register kprobe at offset via tracefs
    echo "p:${KPROBE_NAME} ${KPROBE_TARGET}" > "$TRACE_DIR/kprobe_events"
    echo 1 > "$TRACE_DIR/events/kprobes/${KPROBE_NAME}/enable"
    sleep 2   # allow optimization to complete

    local status
    status=$(cat /sys/kernel/debug/kprobes/list 2>/dev/null | grep io_write || true)
    log_ok "kprobe attached: $status"
}

detach_kprobe() {
    echo 0 > "$TRACE_DIR/events/kprobes/${KPROBE_NAME}/enable" 2>/dev/null || true
    echo "-:${KPROBE_NAME}" >> "$TRACE_DIR/kprobe_events" 2>/dev/null || true
    log_ok "kprobe detached"
}

# ── Main experiment: for each delay, run base → xk ──────────────────
for d in "${DELAYS[@]}"; do
    log_section "===== APP_DELAY = ${d} us ====="

    # Phase 1: Baseline
    run_sweep "base" "$d"

    # Phase 2: Jump-optimized kprobe (xk)
    log_section "Attaching jump-optimized kprobe [OPTIMIZED]"
    echo 1 | tee /proc/sys/debug/kprobes-optimization > /dev/null
    attach_kprobe
    run_sweep "xk" "$d"
    detach_kprobe
done

# ── Summary ──────────────────────────────────────────────────────────
log_section "Experiment complete"
log "Data directory: $DATA_DIR/"
log "  delays:       ${DELAYS[*]} us"
log "  base files:   $(ls "$DATA_DIR"/base_*.txt 2>/dev/null | wc -l)"
log "  xk files:     $(ls "$DATA_DIR"/xk_*.txt 2>/dev/null | wc -l)"
log ""
log "Next steps:"
log "  python3 plot/plot.py       # → plot/figure16.pdf"
