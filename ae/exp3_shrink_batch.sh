#!/usr/bin/env bash
# ae/exp3_shrink_batch.sh — Fig. 10: SHRINK_BATCH write latency
#
# Tunes the memory reclamation batch size for the zswap shrinker.
# Demonstrates controlling kernel internal behavior via KernelX.
#
# Expected: values ≤24 avoid thrashing; 128 (default) causes large latency.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

require_root
require_xkernel

EXP_NAME="exp3_shrink_batch"
RESULT_FILE="$RESULTS_DIR/${EXP_NAME}.csv"

log_section "Experiment 3: SHRINK_BATCH (Fig. 10)"
save_metadata "$EXP_NAME"

# Build the SHRINK_BATCH tunable
log "Building SHRINK_BATCH tunable..."
"$XKTOOL" build "$PROJECT_ROOT/tunables/shrink_batch.toml" 2>&1

# Find the ConstID for SHRINK_BATCH from the scope table
SCOPE_TABLE="/dev/shm/xkernel/scope_table"
if [[ ! -f "$SCOPE_TABLE" ]]; then
    log_err "Scope table not found. Build failed?"
    exit 1
fi

CONST_ID=$(awk -F'\t' 'NR>1 {print $1; exit}' "$SCOPE_TABLE")
log "SHRINK_BATCH ConstID: $CONST_ID"

# Prepare results
echo "value,latency_us,cpu_pct,notes" > "$RESULT_FILE"

# Test values (paper uses 8, 16, 24, 32, 64, 128)
VALUES=(8 16 24 32 64 128)

for val in "${VALUES[@]}"; do
    log "Testing SHRINK_BATCH = $val"

    # Note: In a full AE, this would:
    # 1. Edit the X-tune stub to x_set(x_ctx, $val) for zswap shrinker
    # 2. Load the BPF program
    # 3. Run the mmap workload
    # 4. Collect latency metrics
    # 5. Unload

    # Placeholder for workload (real workload needs zswap enabled + mmap test)
    echo "$val,TODO,TODO,placeholder" >> "$RESULT_FILE"
done

log_ok "Results saved to: $RESULT_FILE"
log "To complete this experiment:"
log "  1. Enable zswap: echo 1 > /sys/module/zswap/parameters/enabled"
log "  2. Edit the X-tune stub to set value per-shrinker (see examples/policy/zswap_shrinker.bpf.c)"
log "  3. Run the mmap workload from the paper"
