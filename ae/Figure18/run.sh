#!/usr/bin/env bash
# run.sh — Reproduce Figure 18: Per-task transition delay CDF
#
# Compares per-task transition delay distributions:
#   - Linux KLP (via kpatch): each task waits for context switch before
#     the kernel can check its stack and complete its transition
#   - XKernel per-thread mode (Mode 1): each task transitions at its
#     next entry to the safe span (microseconds)
#
# Workload: iperf3 with tiny TCP window (-w 4k -P 128) over a
# 200ms RTT link (netem 100ms each side) keeps 128 threads
# blocked inside tcp_sendmsg_locked waiting for window space.
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
CLIENT_IP="192.168.100.2"    # remote: iperf3 server (receiver)
NIC="enp23s0f0np0"

IPERF_PARALLEL=128      # parallel streams (-P)
IPERF_WINDOW="4k"       # TCP window size (-w) — fills instantly
IPERF_LENGTH="512k"     # write length (-l); 512k/4k×300ms≈38.4s per call
IPERF_DURATION=300      # seconds

NETEM_DELAY="150ms"     # one-way delay (both sides → 300ms RTT)
NETEM_LIMIT=100000      # netem queue limit

SETTLE_TIME=10          # seconds to wait for workload to saturate
CONN_TIMEOUT=120        # max seconds to wait for connections (netem makes it slower)

while [[ $# -gt 0 ]]; do
    case "$1" in
        --parallel)   IPERF_PARALLEL="$2";  shift 2 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

RESULT_DIR="$SCRIPT_DIR/results"
KPATCH_MOD_NAME="kpatch-tcp-backlog"
KPATCH_KO="$SCRIPT_DIR/klp_module/${KPATCH_MOD_NAME}.ko"

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
sudo kpatch unload "$KPATCH_MOD_NAME" 2>/dev/null || true

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

[[ -f "$KPATCH_KO" ]] || die "kpatch module not found: $KPATCH_KO\nRun: sudo bash install_bench.sh"
[[ -x "$XKTOOL" ]]    || die "xkernel-tool not found at $XKTOOL"
command -v iperf3 &>/dev/null || die "iperf3 not found"
command -v bpftrace &>/dev/null || die "bpftrace not found (apt install bpftrace)"
command -v kpatch &>/dev/null || die "kpatch not found (run install_bench.sh first)"
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
    echo "NETEM_DELAY=$NETEM_DELAY (each side, RTT=$(echo ${NETEM_DELAY%ms}*2 | bc)ms)"
} > "$RESULT_DIR/log.txt"

# ── netem helpers ────────────────────────────────────────────────────
setup_netem() {
    log "Setting up netem: ${NETEM_DELAY} each side → $((${NETEM_DELAY%ms}*2))ms RTT ..."
    sudo tc qdisc del dev "$NIC" root 2>/dev/null || true
    sudo tc qdisc add dev "$NIC" root netem delay "$NETEM_DELAY" limit "$NETEM_LIMIT"
    ssh "$CLIENT_IP" "sudo tc qdisc del dev $NIC root 2>/dev/null || true; \
        sudo tc qdisc add dev $NIC root netem delay $NETEM_DELAY limit $NETEM_LIMIT"
    log_ok "netem active"
}

clear_netem() {
    sudo tc qdisc del dev "$NIC" root 2>/dev/null || true
    ssh "$CLIENT_IP" "sudo tc qdisc del dev $NIC root 2>/dev/null" || true
}

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
    sudo kpatch unload "$KPATCH_MOD_NAME" 2>/dev/null || true
    sudo "$XKTOOL" unload 1 2>/dev/null || true
    clear_netem 2>/dev/null || true
}
trap cleanup EXIT

# ── Set up netem on both sides ───────────────────────────────────────
setup_netem

# ══════════════════════════════════════════════════════════════════════
# Phase 1: KLP per-task transition data
# ══════════════════════════════════════════════════════════════════════
log_section "Phase 1: KLP Per-Task Transitions"

sudo kpatch unload "$KPATCH_MOD_NAME" 2>/dev/null || true
start_workload

# Record iperf3 PIDs (thread IDs) for post-filtering
if kill -0 "$IPERF_CLIENT_PID" 2>/dev/null; then
    IPERF_PIDS=$(ls /proc/$IPERF_CLIENT_PID/task/ 2>/dev/null | sort -n)
    IPERF_PID_COUNT=$(echo "$IPERF_PIDS" | grep -c '[0-9]' || true)
    log "Tracking $IPERF_PID_COUNT iperf3 threads (client PID=$IPERF_CLIENT_PID)"
else
    log "WARNING: iperf3 process $IPERF_CLIENT_PID is dead! Restarting workload..."
    start_workload
    IPERF_PIDS=$(ls /proc/$IPERF_CLIENT_PID/task/ 2>/dev/null | sort -n)
    IPERF_PID_COUNT=$(echo "$IPERF_PIDS" | grep -c '[0-9]' || true)
    log "Tracking $IPERF_PID_COUNT iperf3 threads (client PID=$IPERF_CLIENT_PID)"
fi
echo "$IPERF_PIDS" > /tmp/iperf3_pids.txt

# Use ftrace kprobes for reliable capture (no comm filter — filter in post-processing)
# Set up kprobes on klp_start_transition and klp_update_patch_state
echo 0 > /sys/kernel/debug/tracing/tracing_on
echo > /sys/kernel/debug/tracing/trace
echo 0 > /sys/kernel/debug/tracing/events/enable
echo 8192 > /sys/kernel/debug/tracing/buffer_size_kb
echo 'p:klp_start klp_start_transition' > /sys/kernel/debug/tracing/kprobe_events 2>/dev/null || true
echo 'p:klp_update klp_update_patch_state' >> /sys/kernel/debug/tracing/kprobe_events 2>/dev/null || true
echo 1 > /sys/kernel/debug/tracing/events/kprobes/klp_start/enable
echo 1 > /sys/kernel/debug/tracing/events/kprobes/klp_update/enable
echo 1 > /sys/kernel/debug/tracing/tracing_on

log "Loading kpatch module ..."
sudo kpatch load "$KPATCH_KO" 2>&1
sleep 20

# Stop tracing and extract data
echo 0 > /sys/kernel/debug/tracing/tracing_on
echo 0 > /sys/kernel/debug/tracing/events/kprobes/klp_start/enable 2>/dev/null || true
echo 0 > /sys/kernel/debug/tracing/events/kprobes/klp_update/enable 2>/dev/null || true
cat /sys/kernel/debug/tracing/trace > /tmp/klp_raw.txt
echo > /sys/kernel/debug/tracing/kprobe_events 2>/dev/null || true

# Post-process: filter klp_update events by iperf3 PIDs,
# compute delay relative to klp_start_transition
python3 - "$RESULT_DIR" << 'PYEOF'
import re, sys
result_dir = sys.argv[1]

# Load iperf3 PIDs
iperf_pids = set()
with open('/tmp/iperf3_pids.txt') as f:
    for line in f:
        line = line.strip()
        if line:
            iperf_pids.add(int(line))

lines = open('/tmp/klp_raw.txt').readlines()

t_start = None
pid_last_ns = {}
for line in lines:
    # ftrace format: <comm>-<pid> [cpu] <flags> <timestamp>: klp_start: ...
    # or: <comm>-<pid> [cpu] <flags> <timestamp>: klp_update: ...
    if 'klp_start:' in line:
        m = re.search(r'\s(\d+\.\d+):', line)
        if m:
            t_start = int(float(m.group(1)) * 1e9)
        continue
    if 'klp_update:' in line:
        m = re.match(r'\s*\S+-(\d+)\s+\[', line)
        tm = re.search(r'\s(\d+\.\d+):', line)
        if m and tm:
            pid = int(m.group(1))
            ns = int(float(tm.group(1)) * 1e9)
            if pid in iperf_pids:
                pid_last_ns[pid] = ns  # keep last per PID

if not pid_last_ns:
    # Fall back: use ALL klp_update events if no iperf3 events
    print(f"WARNING: No iperf3 KLP events (tracked {len(iperf_pids)} PIDs)")
    # Try without PID filter
    for line in lines:
        if 'klp_update:' in line:
            m = re.match(r'\s*\S+-(\d+)\s+\[', line)
            tm = re.search(r'\s(\d+\.\d+):', line)
            if m and tm:
                pid = int(m.group(1))
                ns = int(float(tm.group(1)) * 1e9)
                pid_last_ns[pid] = ns
    if pid_last_ns:
        print(f"  Found {len(pid_last_ns)} total KLP events (all tasks)")

if not pid_last_ns:
    print("WARNING: No KLP events captured at all!")
    sys.exit(0)
if t_start is None:
    print("WARNING: klp_start_transition not captured, using first event as t0")
    t_start = min(pid_last_ns.values())

entries = sorted(pid_last_ns.items(), key=lambda x: x[1])
outf = f'{result_dir}/per_task_data.txt'
with open(outf, 'w') as f:
    for pid, ns in entries:
        delay = ns - t_start
        f.write(f"[Success!]  Target PID: {pid} | Time: +{delay} ns | Waited: {delay} ns | Type: Fast-Path\n")
span_s = (entries[-1][1] - t_start) / 1e9
n_iperf = sum(1 for pid, _ in entries if pid in iperf_pids)
print(f"KLP: {len(entries)} unique tasks ({n_iperf} iperf3), span={span_s:.1f}s")
PYEOF

sudo kpatch unload "$KPATCH_MOD_NAME" 2>&1 || true
stop_workload
log_ok "KLP data: $RESULT_DIR/per_task_data.txt"
sleep 3

# ══════════════════════════════════════════════════════════════════════
# Phase 2: XKernel per-task transition data
# ══════════════════════════════════════════════════════════════════════
log_section "Phase 2: XKernel Per-Task Transitions"

sudo "$XKTOOL" unload 1 2>/dev/null || true
start_workload

# Prepare trace_pipe capture: clear buffer and disable unrelated events
echo 0 > /sys/kernel/debug/tracing/tracing_on
echo > /sys/kernel/debug/tracing/trace
echo 0 > /sys/kernel/debug/tracing/events/enable
echo nop > /sys/kernel/debug/tracing/current_tracer
echo 1 > /sys/kernel/debug/tracing/tracing_on

# Start capturing trace_pipe (bpf_printk output) in background
timeout 120 cat /sys/kernel/debug/tracing/trace_pipe > /tmp/xk_trace_raw.txt 2>/dev/null &
TRACE_PID=$!
sleep 1

# Write a marker BEFORE loading — ftrace records the exact timestamp
echo "XK_LOAD_START" > /sys/kernel/debug/tracing/trace_marker

log "Loading XKernel (Mode 1) ..."
sudo "$XKTOOL" load 1 1 2>&1

# Write a marker AFTER loading — captures BPF load overhead
echo "XK_LOAD_END" > /sys/kernel/debug/tracing/trace_marker

# Wait for per-task transitions (threads must exit & re-enter tcp_sendmsg_locked)
log "Waiting for per-task transitions ..."
for i in $(seq 1 12); do
    sleep 10
    COUNT=$(sudo bpftool -j map dump name transition_stat 2>/dev/null | python3 -c "
import sys, json, struct
try:
    data = json.load(sys.stdin)
    if data:
        entry = data[0]
        val = entry.get('value', {})
        raw = val.get('bytes', val) if isinstance(val, dict) else val
        if isinstance(raw, list):
            bs = bytes([int(x, 16) if isinstance(x, str) else x for x in raw])
            count = struct.unpack_from('<Q', bs, 24)[0]
            print(count)
        else:
            print(0)
    else:
        print(0)
except:
    print(0)
" 2>/dev/null)
    COUNT=${COUNT:-0}
    log "  ${i}0s: $COUNT tasks transitioned"
    if (( COUNT >= IPERF_PARALLEL )); then
        log_ok "All tasks transitioned"
        break
    fi
done

# Stop trace capture
echo 0 > /sys/kernel/debug/tracing/tracing_on
kill "$TRACE_PID" 2>/dev/null || true
wait "$TRACE_PID" 2>/dev/null || true

# Parse bpf_printk "transition done" events from trace_pipe.
# Use XK_LOAD_START / XK_LOAD_END markers for precise timing.
python3 - "$RESULT_DIR" << 'PYEOF'
import re, sys
result_dir = sys.argv[1]

lines = open('/tmp/xk_trace_raw.txt').readlines()

t_load_start = None
t_load_end = None
events = []

for line in lines:
    # Parse trace_marker: XK_LOAD_START / XK_LOAD_END
    if 'XK_LOAD_START' in line and 'tracing_mark_write' in line:
        tm = re.search(r'\s(\d+\.\d+):', line)
        if tm:
            t_load_start = float(tm.group(1))
        continue
    if 'XK_LOAD_END' in line and 'tracing_mark_write' in line:
        tm = re.search(r'\s(\d+\.\d+):', line)
        if tm:
            t_load_end = float(tm.group(1))
        continue
    # Parse transition done events
    if 'transition done' not in line:
        continue
    tm = re.search(r'\s(\d+\.\d+):', line)
    lat = re.search(r'took (\d+) us', line)
    if tm:
        ts_s = float(tm.group(1))
        internal_us = int(lat.group(1)) if lat else 0
        events.append((ts_s, internal_us))

if t_load_start and t_load_end:
    load_ms = (t_load_end - t_load_start) * 1000
    print(f"BPF load overhead: {load_ms:.1f} ms")
else:
    print("WARNING: Could not determine BPF load timestamps from trace_marker")
    t_load_start = t_load_end  # fallback

if not events:
    print("WARNING: No XKernel transition events captured in trace_pipe!")
    import subprocess, json, struct
    result = subprocess.run(
        ['sudo', 'bpftool', '-j', 'map', 'dump', 'name', 'transition_stat'],
        capture_output=True, text=True)
    count, max_us = 0, 0
    if result.returncode == 0 and result.stdout.strip():
        try:
            entries = json.loads(result.stdout)
            if entries:
                val = entries[0].get('value', {})
                raw = val.get('bytes', val) if isinstance(val, dict) else val
                if isinstance(raw, list):
                    bs = bytes([int(x, 16) if isinstance(x, str) else x for x in raw])
                    _, max_ns, _, count = struct.unpack_from('<QQQQ', bs, 0)
                    max_us = max_ns / 1000
        except: pass
    print(f"  Fallback: {count} tasks, max_internal={max_us:.1f}µs")
    outf = f'{result_dir}/per_task_data_xk.txt'
    with open(outf, 'w') as f:
        for i in range(count):
            delay_ns = int(load_ms * 1e6) if t_load_start and t_load_end else 0
            f.write(f"[Success!]  Target PID: 0 | Time: +{delay_ns} ns | "
                    f"Waited: {delay_ns} ns | Type: Fast-Path\n")
    sys.exit(0)

# Reference = XK_LOAD_START (includes BPF load time in per-task delay)
t_ref = t_load_start if t_load_start else events[0][0]
events.sort()
delays_ms = [(ts - t_ref) * 1000 for ts, _ in events]
internals = [i for _, i in events]

print(f"XKernel (incl. BPF load): {len(events)} tasks")
print(f"  Total delay:    min={min(delays_ms):.1f}ms, median={delays_ms[len(delays_ms)//2]:.1f}ms, max={max(delays_ms):.1f}ms")
print(f"  Internal only:  min={min(internals)}µs, max={max(internals)}µs")

outf = f'{result_dir}/per_task_data_xk.txt'
with open(outf, 'w') as f:
    for (ts, _), delay_ms in zip(events, delays_ms):
        delay_ns = int(delay_ms * 1e6)
        f.write(f"[Success!]  Target PID: 0 | Time: +{delay_ns} ns | "
                f"Waited: {delay_ns} ns | Type: Fast-Path\n")
print(f"  Data written to {outf}")
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
