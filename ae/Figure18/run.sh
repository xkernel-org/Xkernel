#!/usr/bin/env bash
# run.sh — Reproduce Figure 18: Transition time comparison (KLP vs XKernel)
#
# Compares:
#   - Linux KLP via kpatch: must wait for ALL threads to exit
#     tcp_sendmsg_locked before the transition completes (~17s)
#   - XKernel per-thread mode (Mode 1): loads BPF kprobes instantly,
#     each thread transitions independently (~1s)
#
# Workload: iperf3 with tiny TCP window (-w 4k) + netem 100ms each side
# keeps 128 threads stuck inside tcp_sendmsg_locked (in sk_stream_wait_memory),
# making KLP transition extremely slow.
#
# IMPORTANT: iperf3 CLIENT (sender) runs LOCALLY — the sender enters
# tcp_sendmsg_locked, NOT the receiver.
#
# Usage:
#   sudo bash run.sh [--runs N] [--parallel P]
#
# Prerequisites:
#   sudo bash install_bench.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
XKTOOL="$PROJECT_ROOT/xkernel-tool"

# ── Configuration ────────────────────────────────────────────────────
CLIENT_IP="192.168.6.2"    # remote: iperf3 server (receiver)
NIC="ens1f1np1"

IPERF_DURATION=180      # iperf3 duration (long enough for measurement)
IPERF_PARALLEL=128      # parallel streams (-P)
IPERF_WINDOW="4k"       # TCP window size (-w) — key: fills instantly
IPERF_LENGTH="1M"       # write length (-l)
NETEM_DELAY="100ms"     # netem delay each side (200ms RTT total)
NETEM_RATE="100mbit"    # rate limit to slow ACKs

RUNS=5                  # number of measurement runs per method
SETTLE_TIME=10          # seconds to wait for workload to saturate
CONN_TIMEOUT=60         # max seconds to wait for connections

# Parse command line
while [[ $# -gt 0 ]]; do
    case "$1" in
        --runs)       RUNS="$2";            shift 2 ;;
        --parallel)   IPERF_PARALLEL="$2";  shift 2 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

RESULT_DIR="$SCRIPT_DIR/results"
KLP_MODULE="$SCRIPT_DIR/klp_module/kpatch-tcp-backlog.ko"
KLP_SYSFS_NAME="kpatch_tcp_backlog"  # underscores in sysfs
KLP_MOD_NAME="kpatch_tcp_backlog"

RED='\033[0;31m'; GREEN='\033[0;32m'; BOLD='\033[1m'; RST='\033[0m'
log()         { echo -e "${BOLD}[$(date '+%H:%M:%S')]${RST} $*"; }
log_ok()      { echo -e "${GREEN}[$(date '+%H:%M:%S')] ✓${RST} $*"; }
log_section() { echo -e "\n${BOLD}════════════════════════════════════════${RST}"; log "$*"; echo -e "${BOLD}════════════════════════════════════════${RST}"; }
die()         { echo -e "${RED}[$(date '+%H:%M:%S')] ✗${RST} $*" >&2; exit 1; }

# ── Idempotent cleanup of prior state ────────────────────────────────
log "Cleaning prior state ..."
sudo "$XKTOOL" table delete --all -y 2>/dev/null || true
sudo rm -f "$PROJECT_ROOT"/bpf/stubs/xtune_stub_*.bpf.c \
           "$PROJECT_ROOT"/bpf/stubs/xtune_stub_*.bpf.h \
           "$PROJECT_ROOT"/bpf/stubs/xtune_stub_*.bpf.o 2>/dev/null || true
sudo kpatch unload kpatch-tcp-backlog 2>/dev/null || true
sudo tc qdisc del dev "$NIC" root 2>/dev/null || true
ssh "$CLIENT_IP" "sudo tc qdisc del dev $NIC root 2>/dev/null" || true

# ── Build XKernel tunable ────────────────────────────────────────────
log "Building XKernel tunable ..."
cd "$PROJECT_ROOT"
# Build will fail at compile step due to stack-relative operand, that's OK
./xkernel-tool build "$SCRIPT_DIR/process_backlog.toml" 2>&1 || true

# Fix the known stack-relative operand in BPF stub
STUB_H="$PROJECT_ROOT/bpf/stubs/xtune_stub_1.bpf.h"
if grep -q 'regs->-0x68(%rbp)' "$STUB_H" 2>/dev/null; then
    log "Fixing stack-relative operand in BPF stub ..."
    sudo chmod 666 "$STUB_H"
    python3 -c "
import re
with open('$STUB_H') as f: s = f.read()
old = '''    u32 reg_val = (u32)(regs->-0x68(%rbp));
    u32 new_imm = (u32)(val + -1);
    xk_cmp_set_flags32(regs, reg_val, new_imm);'''
new = '''    u32 reg_val = 0;
    u64 stack_addr = regs->bp - 0x68;
    bpf_probe_read_kernel(&reg_val, sizeof(reg_val), (void *)stack_addr);
    u32 new_imm = (u32)(val + -1);
    xk_cmp_set_flags32(regs, reg_val, new_imm);'''
s = s.replace(old, new)
s = s.replace('cmp new_IV, %-0x68(%rbp)', 'cmp new_IV, [rbp-0x68]')
with open('$STUB_H', 'w') as f: f.write(s)
"
fi
sudo make -C "$PROJECT_ROOT/bpf" 2>&1 | tail -2

# Ensure kernel modules are built (but don't clean - install_bench.sh handles that)
if [[ ! -f "$PROJECT_ROOT/kernel/kfuncs/xk-kfuncs.ko" ]]; then
    sudo make -C "$PROJECT_ROOT/kernel/kfuncs" 2>&1 | tail -1
fi

# ── Preflight checks ────────────────────────────────────────────────
log_section "Preflight checks"

[[ -f "$KLP_MODULE" ]] || die "kpatch module not found: $KLP_MODULE\nRun: sudo bash install_bench.sh"
[[ -x "$XKTOOL" ]]    || die "xkernel-tool not found at $XKTOOL"
command -v iperf3 &>/dev/null || die "iperf3 not found"
command -v kpatch &>/dev/null || die "kpatch not found. Run: sudo bash install_bench.sh"
ssh "$CLIENT_IP" "which iperf3 >/dev/null 2>&1" || die "iperf3 not found on client"
[[ -d /sys/kernel/livepatch ]] || die "KLP not supported (CONFIG_LIVEPATCH=n)"

mkdir -p "$RESULT_DIR"

log_ok "kpatch module: $KLP_MODULE"
log_ok "iperf3: -w $IPERF_WINDOW -l $IPERF_LENGTH -P $IPERF_PARALLEL"
log_ok "netem: $NETEM_DELAY each side, rate $NETEM_RATE"
log_ok "Runs: $RUNS per method"

# ── Save experiment metadata ─────────────────────────────────────────
{
    echo "date:        $(date)"
    echo "kernel:      $(uname -r)"
    echo "git_branch:  $(cd "$PROJECT_ROOT" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')"
    echo "git_commit:  $(cd "$PROJECT_ROOT" && git rev-parse --short HEAD 2>/dev/null || echo 'unknown')"
    echo ""
    echo "=== parameters ==="
    echo "IPERF_PARALLEL=$IPERF_PARALLEL"
    echo "IPERF_WINDOW=$IPERF_WINDOW"
    echo "IPERF_LENGTH=$IPERF_LENGTH"
    echo "NETEM_DELAY=$NETEM_DELAY"
    echo "NETEM_RATE=$NETEM_RATE"
    echo "RUNS=$RUNS"
} > "$RESULT_DIR/log.txt"

# ── Helper: setup netem ─────────────────────────────────────────────
setup_netem() {
    sudo tc qdisc replace dev "$NIC" root netem delay "$NETEM_DELAY" rate "$NETEM_RATE" limit 100000
    ssh "$CLIENT_IP" "sudo tc qdisc replace dev $NIC root netem delay $NETEM_DELAY limit 1000000"
    sleep 2
    log_ok "netem: $NETEM_DELAY delay each side"
}

teardown_netem() {
    sudo tc qdisc del dev "$NIC" root 2>/dev/null || true
    ssh "$CLIENT_IP" "sudo tc qdisc del dev $NIC root 2>/dev/null" || true
}

# ── Helper: start/stop iperf3 workload ──────────────────────────────
# CLIENT (sender) runs LOCALLY — sender threads enter tcp_sendmsg_locked
IPERF_CLIENT_PID=""

start_iperf_workload() {
    # Start iperf3 server on remote (receiver)
    ssh "$CLIENT_IP" "iperf3 -s -D --pidfile /tmp/iperf3_fig18.pid" 2>/dev/null
    sleep 2

    # Start iperf3 client locally (sender — enters tcp_sendmsg_locked)
    iperf3 -c "$CLIENT_IP" -w "$IPERF_WINDOW" -l "$IPERF_LENGTH" \
        -t "$IPERF_DURATION" -P "$IPERF_PARALLEL" >/dev/null 2>&1 &
    IPERF_CLIENT_PID=$!
    log "iperf3 client PID: $IPERF_CLIENT_PID"

    # Wait for connections to establish (takes ~26s with 200ms RTT)
    log "Waiting for $IPERF_PARALLEL connections ..."
    for i in $(seq 1 "$CONN_TIMEOUT"); do
        CONNS=$(ss -tn state established | grep -c "${CLIENT_IP}:5201" || true)
        CONNS=${CONNS:-0}
        if (( CONNS >= IPERF_PARALLEL - 8 )); then
            log_ok "$CONNS connections established (${i}s)"
            break
        fi
        sleep 1
    done

    # Let workload saturate
    log "Settling ${SETTLE_TIME}s ..."
    sleep "$SETTLE_TIME"

    # Verify threads are stuck in tcp_sendmsg_locked
    local STUCK
    STUCK=$(cat /proc/$IPERF_CLIENT_PID/task/*/wchan 2>/dev/null | grep -c wait_woken || true)
    log_ok "${STUCK:-0} threads in wait_woken (tcp_sendmsg_locked)"
}

stop_iperf_workload() {
    if [[ -n "$IPERF_CLIENT_PID" ]]; then
        kill "$IPERF_CLIENT_PID" 2>/dev/null || true
        wait "$IPERF_CLIENT_PID" 2>/dev/null || true
        IPERF_CLIENT_PID=""
    fi
    ssh "$CLIENT_IP" "kill \$(cat /tmp/iperf3_fig18.pid 2>/dev/null) 2>/dev/null; rm -f /tmp/iperf3_fig18.pid" || true
    sleep 1
    log "iperf3 workload stopped"
}

# ── Cleanup trap ─────────────────────────────────────────────────────
cleanup() {
    stop_iperf_workload 2>/dev/null || true
    teardown_netem 2>/dev/null || true
    sudo kpatch unload kpatch-tcp-backlog 2>/dev/null || true
    sudo "$XKTOOL" unload 1 2>/dev/null || true
}
trap cleanup EXIT

# ══════════════════════════════════════════════════════════════════════
# Phase 1: Measure KLP transition time (via kpatch)
# ══════════════════════════════════════════════════════════════════════
log_section "Phase 1: KLP Transition Time (kpatch)"

KLP_RESULTS_FILE="$RESULT_DIR/klp_times.txt"
echo "# KLP transition time (nanoseconds)" > "$KLP_RESULTS_FILE"

for run in $(seq 1 "$RUNS"); do
    log "KLP Run $run/$RUNS"

    # Ensure clean KLP state
    sudo kpatch unload kpatch-tcp-backlog 2>/dev/null || true
    sleep 1

    setup_netem
    start_iperf_workload

    # Measure KLP transition via kpatch load (blocks until complete or timeout)
    START_NS=$(date +%s%N)
    sudo kpatch load "$KLP_MODULE" 2>&1
    END_NS=$(date +%s%N)

    KLP_TIME_NS=$((END_NS - START_NS))
    KLP_TIME_MS=$(echo "scale=1; $KLP_TIME_NS / 1000000" | bc)
    echo "$KLP_TIME_NS" >> "$KLP_RESULTS_FILE"
    log_ok "KLP transition: ${KLP_TIME_MS} ms"

    # Unload kpatch
    sudo kpatch unload kpatch-tcp-backlog 2>&1 || true
    sleep 2

    stop_iperf_workload
    teardown_netem
    sleep 3
done

# ══════════════════════════════════════════════════════════════════════
# Phase 2: Measure XKernel transition time (per-thread, Mode 1)
# ══════════════════════════════════════════════════════════════════════
log_section "Phase 2: XKernel Transition Time (Mode 1)"

XK_RESULTS_FILE="$RESULT_DIR/xkernel_times.txt"
echo "# XKernel transition time (nanoseconds)" > "$XK_RESULTS_FILE"

for run in $(seq 1 "$RUNS"); do
    log "XKernel Run $run/$RUNS"

    # Ensure clean state
    sudo "$XKTOOL" unload 1 2>/dev/null || true

    setup_netem
    start_iperf_workload

    # Measure XKernel load time (Mode 1 = per-task)
    START_NS=$(date +%s%N)
    sudo "$XKTOOL" load 1 1 2>&1
    END_NS=$(date +%s%N)

    XK_TIME_NS=$((END_NS - START_NS))
    XK_TIME_MS=$(echo "scale=1; $XK_TIME_NS / 1000000" | bc)
    echo "$XK_TIME_NS" >> "$XK_RESULTS_FILE"
    log_ok "XKernel transition: ${XK_TIME_MS} ms"

    # Unload
    sudo "$XKTOOL" unload 1 2>/dev/null || true

    stop_iperf_workload
    teardown_netem
    sleep 3
done

# ══════════════════════════════════════════════════════════════════════
# Summary
# ══════════════════════════════════════════════════════════════════════
log_section "Summary"

echo ""
echo "KLP transition times (ms):"
tail -n +2 "$KLP_RESULTS_FILE" | while read ns; do
    echo "  $(echo "scale=1; $ns / 1000000" | bc) ms"
done

echo ""
echo "XKernel transition times (ms):"
tail -n +2 "$XK_RESULTS_FILE" | while read ns; do
    echo "  $(echo "scale=1; $ns / 1000000" | bc) ms"
done

KLP_MEDIAN=$(tail -n +2 "$KLP_RESULTS_FILE" | sort -n | awk 'NR==int((NR+1)/2)')
XK_MEDIAN=$(tail -n +2 "$XK_RESULTS_FILE" | sort -n | awk 'NR==int((NR+1)/2)')
echo ""
echo "Median KLP:     $(echo "scale=1; $KLP_MEDIAN / 1000000" | bc) ms"
echo "Median XKernel: $(echo "scale=1; $XK_MEDIAN / 1000000" | bc) ms"
echo "Speedup:        $(echo "scale=1; $KLP_MEDIAN / $XK_MEDIAN" | bc)x"

log_ok "Figure 18 experiment complete. Results in: $RESULT_DIR/"
log "Next: python3 plot/plot.py"
