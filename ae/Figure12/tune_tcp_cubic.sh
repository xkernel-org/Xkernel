#!/usr/bin/env bash
# tune_tcp_cubic.sh — Build, load, or unload HyStart tunables (SF + DELAY_MAX)
#
# KernelX tunes two perf-consts in tcp_cubic's HyStart delay detection:
#   ConstID 1 (tcp_cubic):         delay_min >> SF   (SF: 3→1)
#   ConstID 2 (hystart_delay_max): clamp upper bound (16ms→32ms)
#
# Usage:
#   sudo bash tune_tcp_cubic.sh build      # build tunables (idempotent)
#   sudo bash tune_tcp_cubic.sh load       # load both ConstIDs (SF=1, DELAY_MAX=32ms)
#   sudo bash tune_tcp_cubic.sh unload     # unload both ConstIDs

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
XKTOOL="$PROJECT_ROOT/xkernel-tool"
TOML="$SCRIPT_DIR/hystart.toml"

SCOPE_TABLE="/dev/shm/xkernel/scope_table"
STUBS_DIR="$PROJECT_ROOT/bpf/stubs"

ACTION="${1:-load}"
MODE=0  # Immediate mode (no per-task consistency needed)

# ConstID assignments (set after build)
CONST_ID_SF=""         # tcp_cubic (scaling factor)
CONST_ID_DELAY=""      # hystart_delay_max

# ── helpers ──────────────────────────────────────────────────────────
die()  { echo "[✗] $*" >&2; exit 1; }
log()  { echo "[*] $*"; }
ok()   { echo "[✓] $*"; }

find_const_ids() {
    [[ -f "$SCOPE_TABLE" ]] || die "Scope table not found — run 'build' first"
    # With idempotent build (clean + build hystart.toml only),
    # ConstID 1 = tcp_cubic (SF), ConstID 2 = hystart_delay_max
    CONST_ID_SF=1
    CONST_ID_DELAY=2
    # Verify they exist in scope table
    grep -q "^1	" "$SCOPE_TABLE" || die "ConstID 1 not found in scope table"
    grep -q "^2	" "$SCOPE_TABLE" || die "ConstID 2 not found in scope table"
}

# ── build: idempotent — clean state, build only hystart tunables ─────
if [[ "$ACTION" == "build" ]]; then
    log "Cleaning previous state ..."
    "$XKTOOL" table delete --all -y 2>/dev/null || true
    rm -f "$STUBS_DIR"/*.bpf.c "$STUBS_DIR"/*.bpf.h "$STUBS_DIR"/*.bpf.o
    ok "Cleared scope table and bpf/stubs/"

    log "Building tunables from $TOML ..."
    "$XKTOOL" build "$TOML"
    find_const_ids
    ok "Build complete — SF ConstID=$CONST_ID_SF, DELAY_MAX ConstID=$CONST_ID_DELAY"

    # Patch stub values: SF=1, DELAY_MAX=32000
    stub_sf="${STUBS_DIR}/xtune_stub_${CONST_ID_SF}.bpf.c"
    stub_delay="${STUBS_DIR}/xtune_stub_${CONST_ID_DELAY}.bpf.c"

    # Copy RTT-aware X-tune policy for SF (reads curr_rtt, only fires for RTT>=80ms)
    if [[ -f "$SCRIPT_DIR/xtune_policy_sf.bpf.c" ]]; then
        cp "$SCRIPT_DIR/xtune_policy_sf.bpf.c" "$stub_sf"
        log "Installed RTT-aware policy → $stub_sf"
    elif [[ -f "$stub_sf" ]]; then
        sed -i "s/u64 val = [0-9]\+;/u64 val = 1;/" "$stub_sf"
        log "Patched $stub_sf: val=1 (SF=1)"
    fi
    if [[ -f "$stub_delay" ]]; then
        sed -i "s/u64 val = [0-9]\+;/u64 val = 32000;/" "$stub_delay"
        log "Patched $stub_delay: val=32000 (DELAY_MAX=32ms)"
    fi

    # Recompile BPF stubs
    log "Recompiling BPF stubs ..."
    make -C "$PROJECT_ROOT/bpf/" -j"$(nproc)"
    ok "BPF stubs compiled"
    exit 0
fi

# ── unload ───────────────────────────────────────────────────────────
if [[ "$ACTION" == "unload" ]]; then
    find_const_ids 2>/dev/null || true
    if [[ -n "$CONST_ID_SF" ]]; then
        log "Unloading ConstID=$CONST_ID_SF (tcp_cubic SF) ..."
        "$XKTOOL" unload "$CONST_ID_SF" 2>/dev/null || true
    fi
    if [[ -n "$CONST_ID_DELAY" ]]; then
        log "Unloading ConstID=$CONST_ID_DELAY (hystart_delay_max) ..."
        "$XKTOOL" unload "$CONST_ID_DELAY" 2>/dev/null || true
    fi
    ok "HyStart tunables unloaded"
    exit 0
fi

# ── load: load both ConstIDs ─────────────────────────────────────────
if [[ "$ACTION" == "load" ]]; then
    find_const_ids

    log "Loading ConstID=$CONST_ID_SF (SF=1, mode=$MODE) ..."
    "$XKTOOL" load "$MODE" "$CONST_ID_SF"

    log "Loading ConstID=$CONST_ID_DELAY (DELAY_MAX=32ms, mode=$MODE) ..."
    "$XKTOOL" load "$MODE" "$CONST_ID_DELAY"

    ok "Both HyStart tunables loaded (SF=1, DELAY_MAX=32ms)"
    exit 0
fi

die "Unknown action: $ACTION (use: build, load, unload)"
