#!/usr/bin/env bash
#
# fio_bench.sh — Run fio (WRITE.fio) pinned to CPU 5, print summary to stdout.
#
# Usage:
#   sudo bash ae/Figure1/fio_bench.sh
#   sudo bash ae/Figure1/fio_bench.sh READ.fio
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FIO_CPU=5

for cmd in fio sar; do
    if ! command -v "$cmd" &>/dev/null; then
        echo "ERROR: '$cmd' not found." >&2; exit 1
    fi
done

# Temp files (cleaned up on exit)
FIO_JSON=$(mktemp /tmp/fio_bench.XXXXXX.json)
SAR_LOG=$(mktemp /tmp/fio_bench_sar.XXXXXX.log)
trap 'rm -f "$FIO_JSON" "$SAR_LOG"' EXIT

if [ $# -gt 0 ]; then
    FIO_ARGS=("$@")
else
    FIO_ARGS=("$SCRIPT_DIR/WRITE.fio")
fi

echo "[+] fio pinned to CPU $FIO_CPU, running ${FIO_ARGS[*]##*/} ..."

# Start sar on the pinned CPU
sar -u -P "$FIO_CPU" 1 > "$SAR_LOG" 2>&1 &
SAR_PID=$!

# Run fio
taskset -c "$FIO_CPU" fio "${FIO_ARGS[@]}" \
    --output-format=json+ \
    --output="$FIO_JSON" \
    2>/dev/null

# Stop sar (SIGINT for Average line)
kill -INT "$SAR_PID" 2>/dev/null || true
wait "$SAR_PID" 2>/dev/null || true

# Print summary
python3 - "$FIO_JSON" "$SAR_LOG" "$FIO_CPU" <<'PYEOF'
import json, sys

fio_json_path, sar_log_path, cpu_id = sys.argv[1], sys.argv[2], sys.argv[3]

with open(fio_json_path) as f:
    data = json.load(f)

print("=" * 60)
print("  fio + sar Summary  (CPU %s)" % cpu_id)
print("=" * 60)

for job in data.get("jobs", []):
    name = job.get("jobname", "unknown")
    for direction in ("read", "write", "trim"):
        d = job.get(direction, {})
        if d.get("total_ios", 0) == 0:
            continue

        clat = d.get("clat_ns", d.get("clat", {}))
        percentile = clat.get("percentile", {})

        p50 = p90 = None
        for key, val in percentile.items():
            kf = float(key)
            if abs(kf - 50.0) < 0.01: p50 = val
            if abs(kf - 90.0) < 0.01: p90 = val

        unit, div = ("μs", 1000) if p50 and p50 > 10000 else ("ns", 1)
        p50_s = f"{p50/div:.2f} {unit}" if p50 is not None else "N/A"
        p90_s = f"{p90/div:.2f} {unit}" if p90 is not None else "N/A"
        bw = d.get("bw", 0)
        iops = d.get("iops", 0)

        print(f"\n  [{name}] {direction}")
        print(f"    IOPS       : {iops:,.0f}")
        print(f"    BW         : {bw/1024:.2f} MiB/s")
        print(f"    p50 clat   : {p50_s}")
        print(f"    p90 clat   : {p90_s}")

# Parse sar Average line
with open(sar_log_path) as f:
    for line in f:
        if line.startswith("Average:"):
            parts = line.split()
            # cols: Average: CPU %user %nice %system %iowait %steal %idle
            user, system, iowait = parts[2], parts[4], parts[5]
            print(f"\n  CPU {cpu_id} usage (sar avg)")
            print(f"    %user      : {user}")
            print(f"    %system    : {system}")
            print(f"    %iowait    : {iowait}")
            break
    else:
        print("\n  (sar average not available)")

print("=" * 60)
PYEOF
