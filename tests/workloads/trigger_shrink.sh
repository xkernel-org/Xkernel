#!/usr/bin/env bash
# Trigger workload for SHRINK_BATCH (do_shrink_slab).
#
# Creates memory pressure to force the kernel slab shrinker to run
# do_shrink_slab(), which fires the kprobe at +0x0b.
#
# Usage:
#   bash tests/workloads/trigger_shrink.sh [duration_sec] [mem_mb]
#
# Requires: stress-ng (or falls back to pure-bash memory pressure)

set -euo pipefail

DURATION=${1:-30}
MEM_MB=${2:-512}
TMPDIR_RAM=/dev/shm/xk_shrink_$$

echo "[trigger_shrink] duration=${DURATION}s, mem_pressure=${MEM_MB}MB"

cleanup() {
    rm -rf "${TMPDIR_RAM}" 2>/dev/null || true
}
trap cleanup EXIT

mkdir -p "${TMPDIR_RAM}"

# Phase 1: Warm up slab caches by reading library files (no /proc reads - they can block)
echo "[trigger_shrink] Phase 1: warming slab caches with library reads..."
find /usr/lib -name "*.so*" -type f 2>/dev/null | \
    head -500 | \
    xargs -P4 -I{} sh -c 'cat "{}" > /dev/null 2>&1 || true' 2>/dev/null || true
find /usr/share -name "*.txt" -type f 2>/dev/null | \
    head -200 | \
    xargs -P4 -I{} sh -c 'cat "{}" > /dev/null 2>&1 || true' 2>/dev/null || true

# Phase 2: Drop caches to populate them from scratch, triggering shrinker
echo "[trigger_shrink] Phase 2: initial cache pressure..."
echo 3 | sudo tee /proc/sys/vm/drop_caches >/dev/null 2>&1 || true

# Phase 3: Memory pressure for DURATION seconds
echo "[trigger_shrink] Phase 3: ${DURATION}s memory pressure..."
if command -v stress-ng >/dev/null 2>&1; then
    timeout "${DURATION}" stress-ng \
        --vm 2 --vm-bytes "${MEM_MB}m" \
        --timeout "${DURATION}s" \
        2>/dev/null || true
else
    echo "[trigger_shrink] stress-ng not found, using /dev/shm pressure"
    DEADLINE=$((SECONDS + DURATION))
    FILE="${TMPDIR_RAM}/pressure"
    COUNT=0
    while [ $SECONDS -lt $DEADLINE ]; do
        dd if=/dev/zero of="${FILE}" bs=1M count="${MEM_MB}" status=none 2>/dev/null || true
        echo 3 | sudo tee /proc/sys/vm/drop_caches >/dev/null 2>&1 || true
        sleep 1
        COUNT=$((COUNT + 1))
    done
    echo "[trigger_shrink] Done: ${COUNT} pressure cycles"
fi

# Phase 4: Rapid drop caches to trigger shrinker many times
echo "[trigger_shrink] Phase 4: rapid cache drops..."
for i in $(seq 1 20); do
    echo 3 | sudo tee /proc/sys/vm/drop_caches >/dev/null 2>&1 || true
    sleep 0.1
done

echo "[trigger_shrink] Done"
