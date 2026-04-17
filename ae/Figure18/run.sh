#!/usr/bin/env bash
# run.sh — Reproduce Figure 18: Per-task transition delay CDF
#
# Compares per-task transition delay distributions:
#   - Linux KLP (via kpatch): each task waits for context switch before
#     the kernel can check its stack and complete its transition
#   - XKernel per-thread mode (Mode 1): each task transitions at its
#     next entry to the safe span (microseconds)
#
# Workload: iperf3 with tiny TCP window (-w 4k -P 128) keeps 128
# threads inside tcp_sendmsg_locked.
#
# Output: results/per_task_data.txt (KLP) and per_task_data_xk.txt (XKernel)
# in the legacy format consumed by plot/plot.py
#
# Usage:
#   sudo bash run.sh [--parallel P]
#
# Prerequisites:
#   sudo bash install_bench.sh
#   bpftrace installed (apt install bpftrace)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
XKTOOL="$PROJECT_ROOT/xkernel-tool"

# ── Configuration ────────────────────────────────────────────────────
CLIENT_IP="192.168.6.2"    # remote: iperf3 server (receiver)
NIC="ens1f1np1"

IPERF_PARALLEL=128      # parallel streams (-P)
IPERF_WINDOW="4k"       # TCP window size (-w) — fills instantly
IPERF_LENGTH="1M"       # write length (-l)
IPERF_DURATION=120      # seconds

SETTLE_TIME=5           # seconds to wait for workload to saturate
CONN_TIMEOUT=30         # max seconds to wait for connections

while [[ $# -gt 0 ]]; do
    case "$1" in
        --parallel)   IPERF_PARALLEL="$2";  shift 2 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

RESULT_DIR="$SCRIPT_DIR/results"
KLP_MODULE="$SCRIPT_DIR/klp_module/kpatch-tcp-backlog.ko"

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

# ── Build XKernel tunable ────────────────────────────────────────────
log "Building XKernel tunable ..."
cd "$PROJECT_ROOT"
# Build will fail at compile step due to stack-relative operand, that's OK
sudo ./xkernel-tool build "$SCRIPT_DIR/process_backlog.toml" 2>&1 || true

sudo make -C "$PROJECT_ROOT/bpf" 2>&1 | tail -2

# Ensure kernel modules are built
if [[ ! -f "$PROJECT_ROOT/kernel/kfuncs/xk-kfuncs.ko" ]]; then
    sudo make -C "$PROJECT_ROOT/kernel/kfuncs" 2>&1 | tail -1
fi

# ── Preflight checks ────────────────────────────────────────────────
log_section "Preflight checks"

[[ -f "$KLP_MODULE" ]] || die "kpatch module not found: $KLP_MODULE\nRun: sudo bash install_bench.sh"
[[ -x "$XKTOOL" ]]    || die "xkernel-tool not found at $XKTOOL"
command -v iperf3 &>/dev/null || die "iperf3 not found"
command -v bpftrace &>/dev/null || die "bpftrace not found (apt install bpftrace)"
command -v kpatch &>/dev/null || die "kpatch not found"
ssh "$CLIENT_IP" "which iperf3 >/dev/null 2>&1" || die "iperf3 not found on client"

mkdir -p "$RESULT_DIR"
log_ok "All tools found"
log_ok "iperf3: -w $IPERF_WINDOW -l $IPERF_LENGTH -P $IPERF_PARALLEL"

# ── Save metadata ────────────────────────────────────────────────────
{
    echo "date:        $(date)"
    echo "kernel:      $(uname -r)"
    echo "IPERF_PARALLEL=$IPERF_PARALLEL"
    echo "IPERF_WINDOW=$IPERF_WINDOW"
    echo "IPERF_LENGTH=$IPERF_LENGTH"
} > "$RESULT_DIR/log.txt"

# ── Helper: start/stop iperf3 workload ──────────────────────────────
IPERF_CLIENT_PID=""

start_workload() {
    ssh "$CLIENT_IP" "iperf3 -s -D --pidfile /tmp/iperf3_fig18.pid" 2>/dev/null
    sleep 2

    iperf3 -c "$CLIENT_IP" -w "$IPERF_WINDOW" -l "$IPERF_LENGTH" \
        -t "$IPERF_DURATION" -P "$IPERF_PARALLEL" >/dev/null 2>&1 &
    IPERF_CLIENT_PID=$!
    log "iperf3 PID: $IPERF_CLIENT_PID"

    for i in $(seq 1 "$CONN_TIMEOUT"); do
        CONNS=$(ss -tn state established | grep -c "${CLIENT_IP}:5201" || true)
        CONNS=${CONNS:-0}
        if (( CONNS >= IPERF_PARALLEL - 8 )); then
            log_ok "$CONNS connections (${i}s)"
            break
        fi
        sleep 1
    done
    sleep "$SETTLE_TIME"
}

stop_workload() {
    if [[ -n "$IPERF_CLIENT_PID" ]]; then
        kill "$IPERF_CLIENT_PID" 2>/dev/null || true
        wait "$IPERF_CLIENT_PID" 2>/dev/null || true
        IPERF_CLIENT_PID=""
    fi
    ssh "$CLIENT_IP" "cat /tmp/iperf3_fig18.pid 2>/dev/null | xargs -r kill 2>/dev/null; rm -f /tmp/iperf3_fig18.pid" || true
    sleep 1
}

cleanup() {
    stop_workload 2>/dev/null || true
    sudo kpatch unload kpatch-tcp-backlog 2>/dev/null || true
    sudo "$XKTOOL" unload 1 2>/dev/null || true
}
trap cleanup EXIT

# ══════════════════════════════════════════════════════════════════════
# Phase 1: KLP per-task transition data
# ══════════════════════════════════════════════════════════════════════
log_section "Phase 1: KLP Per-Task Transitions"

sudo kpatch unload kpatch-tcp-backlog 2>/dev/null || true
start_workload

# Capture klp_update_patch_state per iperf3 task with bpftrace
sudo sh -c 'bpftrace -e '\''
kprobe:klp_update_patch_state /comm == "iperf3"/ {
    printf("PID:%d NS:%llu\n", tid, nsecs);
}
'\'' > /tmp/klp_raw.txt 2>/dev/null' &
BT_PID=$!
sleep 3

log "Loading kpatch ..."
sudo kpatch load "$KLP_MODULE" 2>&1
sleep 2

# Stop bpftrace (kill the sudo sh process and its child)
sudo sh -c 'kill $(pgrep -f "bpftrace.*klp_update_patch_state") 2>/dev/null' || true
wait "$BT_PID" 2>/dev/null || true

# Post-process: convert to legacy format with relative timestamps
python3 - "$RESULT_DIR" << 'PYEOF'
import re, sys
result_dir = sys.argv[1]
lines = open('/tmp/klp_raw.txt').readlines()
entries = []
for line in lines:
    m = re.match(r'PID:(\d+) NS:(\d+)', line.strip())
    if m:
        entries.append((int(m.group(1)), int(m.group(2))))
if not entries:
    print("WARNING: No KLP events captured!")
    sys.exit(0)
t0 = entries[0][1]
outf = f'{result_dir}/per_task_data.txt'
with open(outf, 'w') as f:
    for pid, ns in entries:
        delay = ns - t0
        f.write(f"[Success!]  Target PID: {pid} | Time: +{delay} ns | Waited: {delay} ns | Type: Fast-Path\n")
print(f"KLP: {len(entries)} tasks, span={((entries[-1][1]-t0)/1e6):.1f}ms")
PYEOF

sudo kpatch unload kpatch-tcp-backlog 2>&1 || true
stop_workload
log_ok "KLP data: $RESULT_DIR/per_task_data.txt"
sleep 3

# ══════════════════════════════════════════════════════════════════════
# Phase 2: XKernel per-task transition data
# ══════════════════════════════════════════════════════════════════════
log_section "Phase 2: XKernel Per-Task Transitions"

sudo "$XKTOOL" unload 1 2>/dev/null || true
start_workload

# Clear trace buffer
sudo sh -c 'echo > /sys/kernel/debug/tracing/trace'

# Start trace capture
sudo sh -c 'timeout 30 cat /sys/kernel/debug/tracing/trace_pipe > /tmp/xk_trace_raw.txt 2>/dev/null' &
XK_TRACE_PID=$!
sleep 1

log "Loading XKernel (Mode 1) ..."
sudo "$XKTOOL" load 1 1 2>&1 | grep -E "loaded|active" || true

# Wait for per-task transitions
sleep 10

# Convert to legacy format
python3 - "$RESULT_DIR" << 'PYEOF'
import re, sys
result_dir = sys.argv[1]
lines = open('/tmp/xk_trace_raw.txt').readlines()
events = []
for line in lines:
    if 'transition done' not in line or 'iperf3' not in line:
        continue
    m = re.search(r'took (\d+) us', line)
    tm = re.search(r'\[\d+\]\s+\S+\s+(\d+\.\d+):', line)
    if m and tm:
        events.append((float(tm.group(1)), int(m.group(1))))
if not events:
    print('WARNING: No XKernel events captured!')
    sys.exit(0)
outf = f'{result_dir}/per_task_data_xk.txt'
with open(outf, 'w') as f:
    for ts, took_us in events:
        f.write(f'cpu: 0, task: [iperf3], ktime_ns: {int(ts*1e9)}, check time: {took_us} us \u2192 \u5dee\u503c\uff1a{took_us} us\n')
print(f'XKernel: {len(events)} tasks, max={max(e[1] for e in events)} us')
PYEOF

sudo "$XKTOOL" unload 1 2>/dev/null || true
stop_workload
log_ok "XKernel data: $RESULT_DIR/per_task_data_xk.txt"

# ══════════════════════════════════════════════════════════════════════
# Summary
# ══════════════════════════════════════════════════════════════════════
log_section "Summary"

echo ""
echo "KLP per-task data:"
wc -l "$RESULT_DIR/per_task_data.txt"
head -3 "$RESULT_DIR/per_task_data.txt"
echo "..."
tail -1 "$RESULT_DIR/per_task_data.txt"

echo ""
echo "XKernel per-task data:"
wc -l "$RESULT_DIR/per_task_data_xk.txt"
head -3 "$RESULT_DIR/per_task_data_xk.txt"
echo "..."
tail -1 "$RESULT_DIR/per_task_data_xk.txt"

log_ok "Figure 18 data collected. Results in: $RESULT_DIR/"
log "Next: python3 plot/plot.py"
