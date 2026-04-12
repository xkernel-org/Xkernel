#!/usr/bin/env bash
# Heavy-SS workload for BLK_MAX_REQUEST_COUNT (blk_add_rq_to_plug).
#
# Keeps many threads inside blk_add_rq_to_plug's Safe Span concurrently
# using parallel fio (or dd) with high queue depths.
#
# Usage:
#   bash tests/workloads/trigger_heavy_blk.sh [duration_sec] [n_jobs]

set -euo pipefail

DURATION=${1:-30}
JOBS=${2:-8}
TMPDIR="/tmp/xk_heavy_blk_$$"
BS="4k"

echo "[heavy_blk] duration=${DURATION}s, jobs=${JOBS}"

cleanup() {
    jobs -p 2>/dev/null | xargs -r kill 2>/dev/null || true
    wait 2>/dev/null || true
    rm -rf "${TMPDIR}" 2>/dev/null || true
}
trap cleanup EXIT

mkdir -p "${TMPDIR}"

if command -v fio >/dev/null 2>&1; then
    echo "[heavy_blk] Using fio with ${JOBS} parallel jobs"
    fio --name=heavy_blk \
        --directory="${TMPDIR}" \
        --ioengine=psync \
        --rw=randrw \
        --bs="${BS}" \
        --size=64M \
        --numjobs="${JOBS}" \
        --runtime="${DURATION}" \
        --time_based \
        --group_reporting \
        --minimal \
        2>/dev/null || true
else
    echo "[heavy_blk] Using dd with ${JOBS} parallel writers"
    # Fallback: parallel dd
    writer() {
        local id=$1
        local f="${TMPDIR}/blk_${id}"
        local deadline=$((SECONDS + DURATION))
        while [ $SECONDS -lt $deadline ]; do
            dd if=/dev/zero of="$f" bs="${BS}" count=2000 \
               conv=notrunc status=none 2>/dev/null || true
            dd if="$f" of=/dev/null bs="${BS}" count=2000 \
               status=none 2>/dev/null || true
        done
    }
    for i in $(seq 1 "$JOBS"); do
        writer "$i" &
    done
    wait
fi

echo "[heavy_blk] Done"
