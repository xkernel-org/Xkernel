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

if ! command -v fio &>/dev/null; then
    echo "ERROR: 'fio' not found." >&2; exit 1
fi

FIO_JSON=$(mktemp /tmp/fio_bench.XXXXXX.json)
trap 'rm -f "$FIO_JSON"' EXIT

if [ $# -gt 0 ]; then
    FIO_ARGS=("$@")
else
    FIO_ARGS=("$SCRIPT_DIR/WRITE.fio")
fi

echo "[+] fio pinned to CPU $FIO_CPU, running ${FIO_ARGS[*]##*/} ..."

taskset -c "$FIO_CPU" fio "${FIO_ARGS[@]}" \
    --output-format=json+ \
    --output="$FIO_JSON" \
    2>/dev/null

python3 - "$FIO_JSON" <<'PYEOF'
import json, sys

with open(sys.argv[1]) as f:
    data = json.load(f)

print("=" * 60)
print("  fio Summary")
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

print("=" * 60)
PYEOF
