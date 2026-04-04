#!/usr/bin/env bash
# ae/run_all.sh — Master script: runs all artifact evaluation experiments
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

require_root
require_xkernel

log_section "KernelX Artifact Evaluation"
log "Project root: $PROJECT_ROOT"
log "Results dir: $RESULTS_DIR"
log "Kernel: $(uname -r)"

TOTAL_START=$(date +%s)

# Run experiments sequentially
for exp in \
    exp3_shrink_batch.sh \
    exp6_overhead.sh \
    exp7_transition.sh; do

    exp_path="$SCRIPT_DIR/$exp"
    if [[ -f "$exp_path" ]]; then
        log_section "Running: $exp"
        timed bash "$exp_path" || log_err "FAILED: $exp"
    else
        log_err "Script not found: $exp_path"
    fi
done

# Note: exp1, exp2, exp4, exp5 require specific hardware (HDD, NVMe, network cluster)
# and are not run by default. Run them individually with the right hardware.
log ""
log "${YELLOW}Experiments requiring special hardware (not run automatically):${RST}"
log "  exp1_blk_max_request.sh   — Needs HDD + NVMe SSD + RocksDB"
log "  exp2_softirq.sh           — Needs 4-node 25Gbps cluster"
log "  exp4_numa_migration.sh    — Needs multi-NUMA system"
log "  exp5_tcp_cubic_nginx.sh   — Needs NGINX + network topology"
log ""

TOTAL_END=$(date +%s)
TOTAL_DURATION=$((TOTAL_END - TOTAL_START))
log_ok "All experiments completed in ${TOTAL_DURATION}s"
log "Results saved to: $RESULTS_DIR"
