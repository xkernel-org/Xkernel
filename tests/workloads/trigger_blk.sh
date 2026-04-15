#!/usr/bin/env bash
# Trigger workload for BLK_MAX_REQUEST_COUNT (blk_add_rq_to_plug).
#
# Generates sequential and random block IO to stress the blk-mq plug path,
# ensuring blk_add_rq_to_plug fires repeatedly so the kprobe at +0x118 runs.
#
# Usage:
#   bash tests/workloads/trigger_blk.sh [duration_sec] [bs] [tmpfile]
#
# Examples:
#   bash tests/workloads/trigger_blk.sh 30        # 30-second run
#   bash tests/workloads/trigger_blk.sh 60 4k     # 60 seconds, 4K blocks

set -euo pipefail

DURATION=${1:-30}
BS=${2:-4k}
TMPFILE=${3:-/tmp/xk_blk_test}
TMPFILE_SIZE="256M"

echo "[trigger_blk] duration=${DURATION}s, bs=${BS}, tmpfile=${TMPFILE}"

cleanup() {
    rm -f "${TMPFILE}" 2>/dev/null || true
}
trap cleanup EXIT

# Phase 1: Sequential write (creates plugged write requests via blk_add_rq_to_plug)
echo "[trigger_blk] Phase 1: sequential writes (${TMPFILE_SIZE})..."
dd if=/dev/zero of="${TMPFILE}" bs="${BS}" count=$((256 * 1024 / 4)) \
   oflag=direct conv=notrunc status=none 2>/dev/null || \
dd if=/dev/zero of="${TMPFILE}" bs="${BS}" count=$((256 * 1024 / 4)) \
   status=none

# Phase 2: Mixed sequential reads and writes for the full duration
echo "[trigger_blk] Phase 2: mixed IO for ${DURATION}s..."
DEADLINE=$((SECONDS + DURATION))
ITER=0
while [ $SECONDS -lt $DEADLINE ]; do
    # Write 1000 blocks
    dd if=/dev/zero of="${TMPFILE}" bs="${BS}" count=1000 \
       conv=notrunc status=none 2>/dev/null || true
    # Read back
    dd if="${TMPFILE}" of=/dev/null bs="${BS}" count=1000 \
       status=none 2>/dev/null || true
    ITER=$((ITER + 1))
done

echo "[trigger_blk] Done: ${ITER} iterations, ~$((ITER * 2000)) IO ops"
