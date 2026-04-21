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

    stub_hdr_sf="${STUBS_DIR}/xtune_stub_${CONST_ID_SF}.bpf.h"
    stub_hdr_delay="${STUBS_DIR}/xtune_stub_${CONST_ID_DELAY}.bpf.h"
    stub_sf="${STUBS_DIR}/xtune_stub_${CONST_ID_SF}.bpf.c"
    stub_delay="${STUBS_DIR}/xtune_stub_${CONST_ID_DELAY}.bpf.c"

    # ── Detect whether hystart_update is inlined or standalone ───────
    # On some kernels (e.g. 6.8.12), hystart_update is inlined into
    # cubictcp_acked and the symbol doesn't exist.  On others (e.g.
    # 6.8.0-101-generic), it is a standalone function.
    if grep -qw 'hystart_update$' /proc/kallsyms 2>/dev/null; then
        HYSTART_INLINED=0
        log "hystart_update is a STANDALONE function — using original offsets"
    else
        HYSTART_INLINED=1
        log "hystart_update is INLINED into cubictcp_acked — patching offsets"
    fi

    if [[ "$HYSTART_INLINED" -eq 1 ]]; then
        # ── Fix inlined function offsets ─────────────────────────────
        # Mapping (.o → vmlinux):
        #   hystart_update+0x161 (SAVE)  → cubictcp_acked+0x211
        #   hystart_update+0x164 (APPLY) → cubictcp_acked+0x214
        #   hystart_update+0x16e (APPLY) → cubictcp_acked+0x21e
        log "Fixing kprobe offsets (hystart_update → cubictcp_acked) ..."
        sed -i 's|hystart_update+0x161|cubictcp_acked+0x211|g' "$stub_hdr_sf"
        sed -i 's|hystart_update|cubictcp_acked|g' "$stub_hdr_sf"
        sed -i 's|hystart_update|cubictcp_acked|g' "$stub_hdr_delay"
        TARGET_FUNC="cubictcp_acked"
        SF_OFFSET="+0x214"
        DELAY_OFFSET="+0x21e"
    else
        # Standalone: the codegen generates .o offsets with cubictcp_acked
        # (because hystart_update is inlined in the .o file).  We must
        # rewrite them to hystart_update with the matching vmlinux offsets.
        # Mapping (.o cubictcp_acked → vmlinux hystart_update):
        #   cubictcp_acked+0x211 (SAVE)  → hystart_update+0x161
        #   cubictcp_acked+0x214 (APPLY) → hystart_update+0x164
        #   cubictcp_acked+0x21e (APPLY) → hystart_update+0x16e
        log "Fixing codegen offsets (cubictcp_acked → hystart_update) ..."
        sed -i 's|cubictcp_acked+0x211|hystart_update+0x161|g' "$stub_hdr_sf"
        sed -i 's|cubictcp_acked|hystart_update|g' "$stub_hdr_sf"
        sed -i 's|cubictcp_acked|hystart_update|g' "$stub_hdr_delay"
        TARGET_FUNC="hystart_update"
        SF_OFFSET="+0x164"
        DELAY_OFFSET="+0x16e"
    fi

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

    # Fix function names + offsets in .bpf.c files to match running kernel
    sed -i "s|cubictcp_acked, \"+0x214\"|${TARGET_FUNC}, \"${SF_OFFSET}\"|g" "$stub_sf"
    sed -i "s|hystart_update, \"+0x164\"|${TARGET_FUNC}, \"${SF_OFFSET}\"|g" "$stub_sf"
    sed -i "s|cubictcp_acked, \"+0x21e\"|${TARGET_FUNC}, \"${DELAY_OFFSET}\"|g" "$stub_delay"
    sed -i "s|hystart_update, \"+0x16e\"|${TARGET_FUNC}, \"${DELAY_OFFSET}\"|g" "$stub_delay"

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
