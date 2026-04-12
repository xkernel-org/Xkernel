#!/usr/bin/env bash
# Heavy-SS workload for SHRINK_BATCH (do_shrink_slab).
#
# Keeps multiple threads inside do_shrink_slab's Safe Span concurrently,
# making transition non-instant (mode 2 refcount > 0, mode 1 needs
# multiple guard checks).
#
# Strategy: Run many parallel processes that each create and destroy
# large numbers of slab objects, forcing the shrinker to run continuously.
#
# Usage:
#   bash tests/workloads/trigger_heavy_shrink.sh [duration_sec] [n_workers]

set -euo pipefail

DURATION=${1:-30}
WORKERS=${2:-8}
MEM_MB_PER_WORKER=256

echo "[heavy_shrink] duration=${DURATION}s, workers=${WORKERS}, mem/worker=${MEM_MB_PER_WORKER}MB"

cleanup() {
    # Kill all child processes
    jobs -p 2>/dev/null | xargs -r kill 2>/dev/null || true
    wait 2>/dev/null || true
    rm -rf /dev/shm/xk_heavy_shrink_* 2>/dev/null || true
}
trap cleanup EXIT

# Worker function: cycles between allocating memory and dropping caches
worker() {
    local id=$1
    local tmpdir="/dev/shm/xk_heavy_shrink_${id}"
    mkdir -p "$tmpdir"
    local deadline=$((SECONDS + DURATION))

    while [ $SECONDS -lt $deadline ]; do
        # Allocate slab objects by reading many files
        find /usr/lib -name "*.so*" -type f 2>/dev/null | \
            shuf | head -200 | \
            xargs -I{} cat "{}" > /dev/null 2>&1 || true

        # Create temp files to fill page cache
        dd if=/dev/zero of="${tmpdir}/fill" bs=1M count=${MEM_MB_PER_WORKER} \
           status=none 2>/dev/null || true

        # Force shrinker by dropping caches
        echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null 2>&1 || true

        rm -f "${tmpdir}/fill" 2>/dev/null || true
        sleep 0.1
    done
}

# Launch workers in parallel
for i in $(seq 1 "$WORKERS"); do
    worker "$i" &
done

echo "[heavy_shrink] $WORKERS workers started, running for ${DURATION}s..."
wait
echo "[heavy_shrink] Done"
