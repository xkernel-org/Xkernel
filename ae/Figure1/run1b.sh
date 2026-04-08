#!/usr/bin/env bash
# run1b.sh — Figure 1(b): RocksDB multiread-random benchmark
#
# Reproduces Figure 1(b) from the paper:
#   "Reducing BLK_MAX_REQUEST_COUNT from 32 to 1 reduces CPU time spent on
#    I/O wait by 12%, yielding an end-to-end 1.2× throughput improvement,
#    while reducing P50 and P75 latency by 1.37× and 1.41×, respectively."
#
# Workload: db_bench multireadrandom, dataset (16B keys, 2048B values),
#           io_uring backed MultiGet API, Direct I/O, pinned to CPU 5.
#
# Output:
#   results/nvme_32.txt      — db_bench output (baseline, V=32)
#   results/nvme_32_cpu.txt  — sar CPU usage  (baseline)
#   results/nvme_1.txt       — db_bench output (tuned,    V=1)
#   results/nvme_1_cpu.txt   — sar CPU usage  (tuned)
#
# Usage:
#   bash run1b.sh                  # uses /dev/nvme1n1
#   bash run1b.sh /dev/sdb         # specify device
#
# Prerequisites:
#   - RocksDB installed (rocksdb/db_bench must exist)
#   - xkernel kernel booted + tunables built
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
XKTOOL="$PROJECT_ROOT/xkernel-tool"

# ── Logging helpers ──────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'
BOLD='\033[1m'; CYAN='\033[36m'; RST='\033[0m'
log()         { echo -e "${BOLD}[$(date '+%H:%M:%S')]${RST} $*"; }
log_ok()      { echo -e "${GREEN}[$(date '+%H:%M:%S')] ✓${RST} $*"; }
log_err()     { echo -e "${RED}[$(date '+%H:%M:%S')] ✗${RST} $*"; }
log_section() {
    echo ""
    echo -e "${BOLD}${CYAN}════════════════════════════════════════════════════${RST}"
    echo -e "${BOLD}${CYAN}  $*${RST}"
    echo -e "${BOLD}${CYAN}════════════════════════════════════════════════════${RST}"
    echo ""
}

# ── Configuration ────────────────────────────────────────────────────
DEVICE="${1:-/dev/nvme1n1}"
MOUNT_POINT="/mnt/rocksdb_bench"
DB_BENCH="$SCRIPT_DIR/rocksdb/db_bench"
DB_PATH="$MOUNT_POINT/rocksdb_data"
TUNE_SCRIPT="$SCRIPT_DIR/tune_blk_max_req.sh"
RESULT_DIR="$SCRIPT_DIR/results"
BENCH_CPU=5

KEY_SIZE=16
VALUE_SIZE=2048
NUM_KEYS=150000

# Benchmark parameters
DURATION=15          # seconds per run
BATCH_SIZE=256         # MultiGet batch size
NUM_THREADS=1         # single-threaded, pinned to one CPU

# ── Preflight checks ────────────────────────────────────────────────
if ! sudo -n true 2>/dev/null; then
    log "This script needs sudo privileges. You may be prompted for your password."
    sudo true || { log_err "Failed to obtain sudo. Aborting."; exit 1; }
fi

if [[ ! -x "$DB_BENCH" ]]; then
    log_err "db_bench not found at $DB_BENCH"
    log_err "Run: bash install_rocksdb.sh"
    exit 1
fi

if [[ ! -b "$DEVICE" ]]; then
    log_err "Block device $DEVICE not found"
    exit 1
fi

if [[ ! -f "$TUNE_SCRIPT" ]]; then
    log_err "tune_blk_max_req.sh not found at $TUNE_SCRIPT"
    exit 1
fi

for cmd in sar taskset; do
    if ! command -v "$cmd" &>/dev/null; then
        log_err "'$cmd' not found. Install sysstat / util-linux."
        exit 1
    fi
done

mkdir -p "$RESULT_DIR"

log_section "Figure 1(b): RocksDB multiread-random"
log "Device      : $DEVICE"
log "Mount point : $MOUNT_POINT"
log "Dataset     : ($NUM_KEYS keys × ${KEY_SIZE}B key + ${VALUE_SIZE}B value)"
log "Duration    : ${DURATION}s per run"
log "CPU pin     : CPU $BENCH_CPU"
log "Results     : $RESULT_DIR/nvme_{1,32}{,_cpu}.txt"

# ── Helper functions ─────────────────────────────────────────────────
setup_device() {
    log "Formatting $DEVICE as ext4 and mounting at $MOUNT_POINT ..."
    sudo umount "$MOUNT_POINT" 2>/dev/null || true
    sudo mkfs.ext4 -F "$DEVICE" 2>&1 | tail -1
    sudo mkdir -p "$MOUNT_POINT"
    sudo mount -o noatime,nodiratime "$DEVICE" "$MOUNT_POINT"
    sudo chmod 777 "$MOUNT_POINT"
    log_ok "Mounted $DEVICE at $MOUNT_POINT"
}

cleanup_device() {
    log "Cleaning up mount ..."
    sudo umount "$MOUNT_POINT" 2>/dev/null || true
}
trap cleanup_device EXIT

run_fill() {
    log "Filling database with $NUM_KEYS keys ..."
    log "  This may take a while ..."

    taskset -c "$BENCH_CPU" "$DB_BENCH" \
        --benchmarks=fillrandom \
        --db="$DB_PATH" \
        --key_size="$KEY_SIZE" \
        --value_size="$VALUE_SIZE" \
        --num="$NUM_KEYS" \
        --use_direct_io_for_flush_and_compaction=true \
        --compression_type=none \
        --disable_wal=true \
        2>&1 | tail -3

    # Compact to ensure stable read performance
    log "Compacting database ..."
    taskset -c "$BENCH_CPU" "$DB_BENCH" \
        --benchmarks=compact \
        --db="$DB_PATH" \
        --use_existing_db=true \
        --use_direct_io_for_flush_and_compaction=true \
        2>&1 | tail -3

    # Drop page cache
    sync
    sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'
    log_ok "Database fill complete"
}

# run_multiread <blk_value>
#   Writes:  $RESULT_DIR/nvme_<blk_value>.txt      (db_bench output)
#            $RESULT_DIR/nvme_<blk_value>_cpu.txt   (sar CPU output)
run_multiread() {
    local blk_value="$1"
    local bench_out="$RESULT_DIR/nvme_${blk_value}.txt"
    local cpu_out="$RESULT_DIR/nvme_${blk_value}_cpu.txt"
    local raw_out
    raw_out=$(mktemp /tmp/fig1b_raw.XXXXXX.txt)

    log "Running multireadrandom (BLK_MAX_REQUEST_COUNT=$blk_value) for ${DURATION}s ..."
    log "  db_bench output → $bench_out"
    log "  sar CPU output  → $cpu_out"

    # Drop page cache between runs
    sync
    sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'

    # Start sar on the pinned CPU (1-second intervals, raw per-second output)
    sar -u -P "$BENCH_CPU" 1 > "$cpu_out" 2>&1 &
    local sar_pid=$!

    # Run db_bench: multireadrandom with io_uring + Direct I/O, pinned to CPU 5
    taskset -c "$BENCH_CPU" "$DB_BENCH" \
        --benchmarks=multireadrandom \
        --db="$DB_PATH" \
        --use_existing_db=true \
        --key_size="$KEY_SIZE" \
        --value_size="$VALUE_SIZE" \
        --num="$NUM_KEYS" \
        --duration="$DURATION" \
        --threads="$NUM_THREADS" \
        --multiread_batched=true \
        --batch_size="$BATCH_SIZE" \
        --use_direct_reads=true \
        --async_io=true \
        --statistics=true \
        --histogram=true \
        > "$raw_out" 2>&1

    # Stop sar (SIGINT so it writes the Average line)
    kill -INT "$sar_pid" 2>/dev/null || true
    wait "$sar_pid" 2>/dev/null || true

    # Extract the multireadrandom summary + histogram block from raw db_bench
    # output, matching the format of existing nvme_*.txt files.
    python3 - "$raw_out" "$bench_out" <<'PYEOF'
import sys, re

raw_path, out_path = sys.argv[1], sys.argv[2]
with open(raw_path) as f:
    lines = f.readlines()

# Find the multireadrandom summary line and the histogram that follows
output_lines = []
capture = False
for line in lines:
    if line.startswith("multireadrandom"):
        capture = True
    if capture:
        output_lines.append(line)

with open(out_path, 'w') as f:
    f.writelines(output_lines)
PYEOF

    rm -f "$raw_out"

    # Print quick summary to console
    echo ""
    log "  ── nvme_${blk_value}.txt ──"
    head -6 "$bench_out" | while IFS= read -r line; do log "  $line"; done
    echo ""
    log "  ── nvme_${blk_value}_cpu.txt (last 3 samples) ──"
    grep "^ *[0-9]" "$cpu_out" | tail -3 | while IFS= read -r line; do log "  $line"; done
    echo ""

    log_ok "Results saved: $bench_out , $cpu_out"
}

compare_results() {
    local base="$RESULT_DIR/nvme_32.txt"
    local tuned="$RESULT_DIR/nvme_1.txt"
    local base_cpu="$RESULT_DIR/nvme_32_cpu.txt"
    local tuned_cpu="$RESULT_DIR/nvme_1_cpu.txt"

    [[ -f "$base" && -f "$tuned" ]] || return 0

    python3 - "$base" "$tuned" "$base_cpu" "$tuned_cpu" <<'PYEOF'
import sys, re

def extract_bench(path):
    with open(path) as f:
        content = f.read()
    result = {}
    m = re.search(r'multireadrandom\s*:\s*([\d.]+)\s*micros/op\s+([\d]+)\s*ops/sec', content)
    if m:
        result['ops_sec'] = int(m.group(2))
        result['usec_per_op'] = float(m.group(1))
    for line in content.split('\n'):
        if 'P50' in line and 'P75' in line:
            parts = re.findall(r'P(\d+(?:\.\d+)?)\s*:\s*([\d.]+)', line)
            for k, v in parts:
                result[f'p{k}'] = float(v)
            break
    return result

def extract_iowait(path):
    try:
        with open(path) as f:
            for line in f:
                if line.startswith("Average:"):
                    parts = line.split()
                    return float(parts[5]) if len(parts) > 5 else None
    except Exception:
        pass
    return None

base = extract_bench(sys.argv[1])
tuned = extract_bench(sys.argv[2])
base_iowait = extract_iowait(sys.argv[3])
tuned_iowait = extract_iowait(sys.argv[4])

print(f"\n{'='*60}")
print(f"  Comparison: Baseline (V=32) vs Tuned (V=1)")
print(f"{'='*60}")

if 'ops_sec' in base and 'ops_sec' in tuned:
    ratio = tuned['ops_sec'] / base['ops_sec'] if base['ops_sec'] else 0
    print(f"  Throughput : {base['ops_sec']:>10,} → {tuned['ops_sec']:>10,}  ({ratio:.2f}×)")

for p in ['p50', 'p75']:
    if p in base and p in tuned:
        ratio = base[p] / tuned[p] if tuned[p] else 0
        label = p.upper()
        print(f"  {label} latency: {base[p]:>10.1f} → {tuned[p]:>10.1f} µs ({ratio:.2f}× reduction)")

if base_iowait is not None and tuned_iowait is not None:
    diff = base_iowait - tuned_iowait
    print(f"  %iowait   : {base_iowait:>10.1f} → {tuned_iowait:>10.1f}%  (Δ {diff:+.1f}%)")

print(f"{'='*60}")
print(f"\n  Expected (from paper):")
print(f"    Throughput improvement : 1.2×")
print(f"    P50 latency reduction  : 1.37×")
print(f"    P75 latency reduction  : 1.41×")
print(f"    I/O wait reduction     : 12%")
print(f"{'='*60}\n")
PYEOF
}

# ── Main ─────────────────────────────────────────────────────────────
setup_device
run_fill

# ── Run 1: Baseline (BLK_MAX_REQUEST_COUNT = 32, kernel default) ─────
log_section "Run 1: Baseline (BLK_MAX_REQUEST_COUNT = 32)"
run_multiread 32

# ── Tune: Set BLK_MAX_REQUEST_COUNT = 1 via KernelX ─────────────────
log_section "Tuning BLK_MAX_REQUEST_COUNT = 1"
sudo bash "$TUNE_SCRIPT" 1

# ── Run 2: Tuned (BLK_MAX_REQUEST_COUNT = 1) ────────────────────────
log_section "Run 2: Tuned (BLK_MAX_REQUEST_COUNT = 1)"
run_multiread 1

# ── Unload tunable ───────────────────────────────────────────────────
log "Unloading BLK_MAX_REQUEST_COUNT tunable ..."
sudo bash "$TUNE_SCRIPT" unload || true
sudo "$XKTOOL" table delete --all -y
sudo rm -rf "$PROJECT_ROOT/bpf/stubs/"*

# ── Compare ──────────────────────────────────────────────────────────
log_section "Comparison"
compare_results

log_ok "Figure 1(b) experiment complete."
log "Results in: $RESULT_DIR/"
log "  nvme_32.txt / nvme_32_cpu.txt  (baseline)"
log "  nvme_1.txt  / nvme_1_cpu.txt   (tuned)"
