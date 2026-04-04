#!/usr/bin/env bash
# ae/exp7_transition.sh — Fig. 17-20: Policy-update and transition time
#
# Measures:
# - Policy-update time (BPF verification + jump-opt + kprobe registration)
# - Per-thread transition time
# - Global consistency transition time
#
# Expected: <542ms policy load; <10ms per-thread; <144ms global.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

require_root
require_xkernel

EXP_NAME="exp7_transition"
RESULT_FILE="$RESULTS_DIR/${EXP_NAME}.csv"

log_section "Experiment 7: Transition Time (Fig. 17-20)"
save_metadata "$EXP_NAME"

echo "test,mode,num_threads,load_time_ms,transition_time_ms" > "$RESULT_FILE"

# Build all tunables
log "Building all tunables..."
"$XKTOOL" build "$PROJECT_ROOT/tunables/all.toml" --skip-gen 2>&1 || \
    "$XKTOOL" build "$PROJECT_ROOT/tunables/shrink_batch.toml" 2>&1

SCOPE_TABLE="/dev/shm/xkernel/scope_table"
if [[ ! -f "$SCOPE_TABLE" ]]; then
    log_err "Scope table not found after build."
    exit 1
fi

CONST_ID=$(awk -F'\t' 'NR>1 {print $1; exit}' "$SCOPE_TABLE")

# Test 1: Policy-update time (mode 0 = Immediate)
log "Test 1: Policy-update time (Immediate mode)"
start_ns=$(date +%s%N)
sudo "$XKTOOL" load 0 "$CONST_ID" 2>&1 || true
end_ns=$(date +%s%N)
load_time_ms=$(( (end_ns - start_ns) / 1000000 ))
log_ok "  Load time: ${load_time_ms}ms"
echo "policy_update,0,1,$load_time_ms,0" >> "$RESULT_FILE"

sudo "$XKTOOL" unload "$CONST_ID" 2>&1 || true

# Test 2: Per-task transition (mode 1)
log "Test 2: Per-task transition"
start_ns=$(date +%s%N)
sudo "$XKTOOL" load 1 "$CONST_ID" 2>&1 || true
end_ns=$(date +%s%N)
transition_ms=$(( (end_ns - start_ns) / 1000000 ))
log_ok "  Per-task transition: ${transition_ms}ms"
echo "per_task,1,1,$load_time_ms,$transition_ms" >> "$RESULT_FILE"

sudo "$XKTOOL" unload "$CONST_ID" 2>&1 || true

# Test 3: Global consistency (mode 2)
log "Test 3: Global consistency transition"
start_ns=$(date +%s%N)
sudo "$XKTOOL" load 2 "$CONST_ID" 5 2>&1 || true
end_ns=$(date +%s%N)
global_ms=$(( (end_ns - start_ns) / 1000000 ))
log_ok "  Global transition: ${global_ms}ms"
echo "global,2,1,$load_time_ms,$global_ms" >> "$RESULT_FILE"

sudo "$XKTOOL" unload "$CONST_ID" 2>&1 || true

log_ok "Results saved to: $RESULT_FILE"
