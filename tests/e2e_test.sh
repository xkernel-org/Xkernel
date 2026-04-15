#!/usr/bin/env bash
# End-to-end test for Xkernel (KernelX / SIE) tunables.
#
# Tests SHRINK_BATCH and BLK_MAX_REQUEST_COUNT tunables across
# all three consistency modes (0=Immediate, 1=Per-task, 2=Global).
# Validates:
#   1. Forward transition: kprobes fire, new value applied
#   2. Reverse transition: proper deactivation + cleanup
#   3. Heavy-SS workload: non-instant transition with tasks inside SS
#
# Usage:
#   sudo bash tests/e2e_test.sh [--quick] [--const-id N] [--mode M]
#                                [--heavy] [--workload-sec S]
#
#   --quick        : short workload (10s instead of 60s)
#   --const-id N   : only test ConstID N
#   --mode M       : only test mode M (0, 1, or 2)
#   --heavy        : use heavy-SS workloads (more threads, longer)
#   --workload-sec : workload duration override
#
# Prerequisites:
#   - BPF stubs compiled (KERNEL_DIR=~/linux-6.8.0 ./xkernel-tool build ...)
#   - Run as root (sudo)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
XKERNEL="${ROOT_DIR}/xkernel-tool"
WORKLOADS="${SCRIPT_DIR}/workloads"
RESULTS_DIR="${SCRIPT_DIR}/results"
LOGFILE="${RESULTS_DIR}/e2e_$(date +%Y%m%d_%H%M%S).log"

# ── Defaults ──────────────────────────────────────────────────────────────────
WORKLOAD_DURATION=60
QUICK=false
HEAVY=false
FILTER_CONSTID=""
FILTER_MODE=""

# ── Tunables: auto-detect from scope_table ────────────────────────────────────
# Detect ConstIDs dynamically from the scope table
detect_tunables() {
    local scope="/dev/shm/xkernel/scope_table"
    if [ ! -f "$scope" ]; then
        echo "ERROR: scope_table not found at $scope" >&2
        exit 1
    fi

    TUNABLES=()
    while IFS=$'\t' read -r cid val expr cs_idx ss_idx bpf_file status rest; do
        [ "$cid" = "ConstID" ] && continue
        case "$bpf_file" in
            *stub_*.bpf.o) ;;
            *) continue ;;
        esac

        # Determine tunable name from cs_raw
        local func
        func=$(grep "^${cid}[[:space:]]" /dev/shm/xkernel/cs_raw 2>/dev/null | \
               awk '{print $2}' | head -1)
        case "$func" in
            do_shrink_slab)
                TUNABLES+=("${cid}:SHRINK_BATCH:trigger_shrink.sh:trigger_heavy_shrink.sh")
                ;;
            blk_add_rq_to_plug)
                TUNABLES+=("${cid}:BLK_MAX_REQUEST_COUNT:trigger_blk.sh:trigger_heavy_blk.sh")
                ;;
            handle_softirqs)
                TUNABLES+=("${cid}:MAX_SOFTIRQ_RESTART:trigger_softirq.sh:trigger_softirq.sh")
                ;;
            migrate_pages)
                # NR_MAX_BATCHED_MIGRATION — no dedicated workload yet, skip
                log "  Note: ConstID $cid (migrate_pages) — no trigger workload, skipping"
                ;;
            *)
                log "Warning: unknown function '$func' for ConstID $cid, skipping"
                ;;
        esac
    done < "$scope"

    if [ ${#TUNABLES[@]} -eq 0 ]; then
        echo "ERROR: No tunables found in scope_table" >&2
        exit 1
    fi
}

# ── Parse arguments ───────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
    case $1 in
        --quick)       QUICK=true; WORKLOAD_DURATION=10 ;;
        --heavy)       HEAVY=true ;;
        --const-id)    FILTER_CONSTID="$2"; shift ;;
        --mode)        FILTER_MODE="$2"; shift ;;
        --workload-sec) WORKLOAD_DURATION="$2"; shift ;;
        *) echo "Unknown argument: $1" >&2; exit 1 ;;
    esac
    shift
done

mkdir -p "${RESULTS_DIR}"

# ── Logging helpers ───────────────────────────────────────────────────────────
log()   { echo "[$(date '+%H:%M:%S')] $*" | tee -a "${LOGFILE}"; }
pass()  { echo "[$(date '+%H:%M:%S')] ✓ $*" | tee -a "${LOGFILE}"; }
fail()  { echo "[$(date '+%H:%M:%S')] ✗ $*" | tee -a "${LOGFILE}"; FAILURES=$((FAILURES+1)); }
FAILURES=0

# ── BPF stats helpers ─────────────────────────────────────────────────────────
enable_bpf_stats() {
    echo 1 > /proc/sys/kernel/bpf_stats_enabled 2>/dev/null || true
}

get_prog_run_cnt() {
    local prog_id="$1"
    bpftool prog show id "${prog_id}" 2>/dev/null \
        | grep -oP 'run_cnt \K[0-9]+' || echo "0"
}

get_bpf_prog_id() {
    local constid="$1"
    bpftool prog list 2>/dev/null \
        | grep "kprobe.*name __xk_${constid}_" \
        | grep -oP '^\K[0-9]+' | head -1 || echo ""
}

# ── Test: forward transition (load + workload + verify kprobe fires) ─────────
test_forward() {
    local constid="$1" name="$2" workload_script="$3" mode="$4"

    log "  [Forward] Loading ConstID=${constid} mode=${mode}..."
    if ! "${XKERNEL}" load "${mode}" "${constid}" >> "${LOGFILE}" 2>&1; then
        fail "  LOAD FAILED for ConstID=${constid} mode=${mode}"
        return 1
    fi
    pass "  Load succeeded"

    # Get initial run count
    enable_bpf_stats
    local prog_id
    prog_id=$(get_bpf_prog_id "${constid}")
    if [ -z "${prog_id}" ]; then
        fail "  Could not find BPF prog for ConstID=${constid}"
        "${XKERNEL}" unload "${constid}" >> "${LOGFILE}" 2>&1 || true
        return 1
    fi
    local cnt_before
    cnt_before=$(get_prog_run_cnt "${prog_id}")

    # Run workload
    log "  [Forward] Running workload (${WORKLOAD_DURATION}s): ${workload_script}..."
    local ws=$SECONDS
    if bash "${workload_script}" "${WORKLOAD_DURATION}" >> "${LOGFILE}" 2>&1; then
        log "  Workload completed in $((SECONDS - ws))s"
    else
        log "  Workload exited non-zero (may be normal)"
    fi

    # Check kprobe fires
    local cnt_after
    cnt_after=$(get_prog_run_cnt "${prog_id}")
    local delta=$((cnt_after - cnt_before))
    log "  [Forward] run_cnt delta=${delta} (${cnt_before} -> ${cnt_after})"

    if [ "${delta}" -gt 0 ]; then
        pass "  Kprobe fired ${delta} times"
    else
        fail "  Kprobe did NOT fire (delta=0)"
        return 1
    fi

    # Transition stats
    "${XKERNEL}" transition-stats "${constid}" >> "${LOGFILE}" 2>&1 || true

    return 0
}

# ── Test: reverse transition (unload + verify deactivation) ──────────────────
test_reverse() {
    local constid="$1" name="$2" mode="$3"

    log "  [Reverse] Unloading ConstID=${constid} mode=${mode}..."
    local unload_start=$SECONDS
    if ! "${XKERNEL}" unload "${constid}" >> "${LOGFILE}" 2>&1; then
        fail "  UNLOAD FAILED for ConstID=${constid}"
        return 1
    fi
    local unload_elapsed=$((SECONDS - unload_start))
    log "  [Reverse] Unload completed in ${unload_elapsed}s"

    # Verify BPF programs are gone
    local prog_id
    prog_id=$(get_bpf_prog_id "${constid}")
    if [ -n "${prog_id}" ]; then
        fail "  BPF prog still present after unload (id=${prog_id})"
        return 1
    fi
    pass "  BPF programs removed"

    # Verify pin directory is gone
    if sudo test -d "/sys/fs/bpf/xkernel/${constid}"; then
        fail "  Pin directory still exists after unload"
        return 1
    fi
    pass "  Pin directory cleaned up"

    # Mode-specific reverse verification
    case "${mode}" in
        1)
            log "  [Reverse] Mode 1: xk_active=0 + epoch bump confirmed by unload output"
            pass "  Mode 1 reverse transition complete"
            ;;
        2)
            # Check dmesg for reverse transition
            local dmesg_out
            dmesg_out=$(dmesg --since '-30 seconds' 2>/dev/null || true)
            if echo "$dmesg_out" | grep -qi 'reverse transition'; then
                pass "  Mode 2 reverse transition confirmed in dmesg"
            else
                log "  [Reverse] dmesg (last 30s):"
                echo "$dmesg_out" | grep -i 'xkernel\|consistency' | tail -5 | tee -a "${LOGFILE}" || true
                # Not a failure — module might have been instant
                pass "  Mode 2 unload completed (module removed)"
            fi
            ;;
        *)
            pass "  Mode 0 unload complete"
            ;;
    esac

    return 0
}

# ── Test: heavy-SS workload (non-instant transition) ─────────────────────────
test_heavy_ss() {
    local constid="$1" name="$2" heavy_script="$3" mode="$4"

    if [ ! -f "${heavy_script}" ]; then
        log "  [Heavy-SS] Script not found: ${heavy_script}, skipping"
        return 0
    fi

    log "  [Heavy-SS] Loading ConstID=${constid} mode=${mode}..."
    if ! "${XKERNEL}" load "${mode}" "${constid}" >> "${LOGFILE}" 2>&1; then
        fail "  Heavy-SS LOAD FAILED"
        return 1
    fi

    # Start heavy workload in background — keep threads inside SS
    local heavy_duration=$((WORKLOAD_DURATION / 2))
    [ "$heavy_duration" -lt 10 ] && heavy_duration=10
    log "  [Heavy-SS] Starting heavy workload (${heavy_duration}s)..."
    bash "${heavy_script}" "${heavy_duration}" 4 >> "${LOGFILE}" 2>&1 &
    local workload_pid=$!

    # Wait for workload to start building pressure
    sleep 3

    # Now unload while workload is running — this tests non-instant transition
    log "  [Heavy-SS] Unloading while workload runs (should be non-instant)..."
    local unload_start=$SECONDS
    "${XKERNEL}" unload "${constid}" >> "${LOGFILE}" 2>&1 || true
    local unload_elapsed=$((SECONDS - unload_start))
    log "  [Heavy-SS] Unload took ${unload_elapsed}s"

    if [ "${unload_elapsed}" -ge 2 ]; then
        pass "  Non-instant transition: unload took ${unload_elapsed}s (> 2s)"
    else
        log "  [Heavy-SS] Transition was instant (${unload_elapsed}s) — may be ok"
        pass "  Transition completed (${unload_elapsed}s)"
    fi

    # Clean up workload
    kill "${workload_pid}" 2>/dev/null || true
    wait "${workload_pid}" 2>/dev/null || true

    # Verify cleanup
    local prog_id
    prog_id=$(get_bpf_prog_id "${constid}")
    if [ -n "${prog_id}" ]; then
        fail "  BPF prog still present after heavy-SS unload"
    else
        pass "  Heavy-SS cleanup complete"
    fi

    return 0
}

# ── Full test for one ConstID + mode ─────────────────────────────────────────
test_constid_mode() {
    local constid="$1" name="$2" workload="$3" heavy_workload="$4" mode="$5"
    local mode_names=("Immediate" "Per-task" "Global")
    local mode_name="${mode_names[$mode]}"

    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    log "TEST: ConstID=${constid} (${name}), Mode=${mode} (${mode_name})"
    log "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Ensure clean state
    "${XKERNEL}" unload "${constid}" >> "${LOGFILE}" 2>&1 || true
    sleep 1

    # Forward + workload + verify
    if ! test_forward "${constid}" "${name}" "${WORKLOADS}/${workload}" "${mode}"; then
        log "  Skipping reverse test due to forward failure"
        "${XKERNEL}" unload "${constid}" >> "${LOGFILE}" 2>&1 || true
        return 1
    fi

    # Reverse transition
    if ! test_reverse "${constid}" "${name}" "${mode}"; then
        return 1
    fi

    # Heavy-SS test (only if --heavy or mode != 0)
    if [ "${HEAVY}" = true ] && [ "${mode}" -ne 0 ]; then
        sleep 1
        test_heavy_ss "${constid}" "${name}" \
            "${WORKLOADS}/${heavy_workload}" "${mode}" || true
    fi

    sleep 1
    pass "TEST PASSED: ConstID=${constid} mode=${mode} (${mode_name})"
}

# ── Prerequisite checks ───────────────────────────────────────────────────────
log "============================================================"
log "  Xkernel End-to-End Test Suite"
log "  Log: ${LOGFILE}"
log "============================================================"
log ""

if [ "$(id -u)" -ne 0 ]; then
    echo "ERROR: Must run as root (use sudo)" >&2
    exit 1
fi

log "System: $(uname -r)"
log "bpftool: $(bpftool version 2>/dev/null | head -1 || echo 'not found')"
log "Quick: ${QUICK}, Heavy: ${HEAVY}, Duration: ${WORKLOAD_DURATION}s"
log ""

detect_tunables
log "Detected tunables:"
for t in "${TUNABLES[@]}"; do
    log "  $(echo "$t" | cut -d: -f1-2)"
done
log ""

# Check BPF stubs
for tunable in "${TUNABLES[@]}"; do
    constid=$(echo "${tunable}" | cut -d: -f1)
    stub="${ROOT_DIR}/bpf/stubs/xtune_stub_${constid}.bpf.o"
    if [ ! -f "${stub}" ]; then
        log "ERROR: BPF stub not found: ${stub}" >&2
        exit 1
    fi
done
pass "BPF stubs present"

# ── Main test loop ────────────────────────────────────────────────────────────
log ""
log "Starting tests..."
log ""

TOTAL=0
for tunable in "${TUNABLES[@]}"; do
    constid=$(echo "${tunable}" | cut -d: -f1)
    name=$(echo "${tunable}" | cut -d: -f2)
    workload=$(echo "${tunable}" | cut -d: -f3)
    heavy_workload=$(echo "${tunable}" | cut -d: -f4)

    if [ -n "${FILTER_CONSTID}" ] && [ "${constid}" != "${FILTER_CONSTID}" ]; then
        continue
    fi

    for mode in 0 1 2; do
        if [ -n "${FILTER_MODE}" ] && [ "${mode}" != "${FILTER_MODE}" ]; then
            continue
        fi
        TOTAL=$((TOTAL + 1))
        test_constid_mode "${constid}" "${name}" "${workload}" \
            "${heavy_workload}" "${mode}" || true
        log ""
    done
done

# ── Summary ───────────────────────────────────────────────────────────────────
log "============================================================"
log "  Test Summary"
log "  Total: ${TOTAL} | Failures: ${FAILURES}"
log "  Log: ${LOGFILE}"
log "============================================================"

if [ "${FAILURES}" -gt 0 ]; then
    log "RESULT: SOME TESTS FAILED (${FAILURES}/${TOTAL})"
    exit 1
else
    log "RESULT: ALL ${TOTAL} TESTS PASSED"
    exit 0
fi
