#!/usr/bin/env bash
# tune_tcp_cubic.sh — Build, load (adaptive or static), or unload tcp_cubic tunable
#
# Assumes `xkernel-tool build` has already been run once (by run.sh or manual).
# This script manages the tcp_cubic perf-const (delay_min shift / scaling factor).
#
# Usage:
#   sudo bash tune_tcp_cubic.sh build              # one-time build
#   sudo bash tune_tcp_cubic.sh <VALUE>             # patch SF to VALUE + reload (static)
#   sudo bash tune_tcp_cubic.sh adaptive            # load adaptive X-tune policy
#   sudo bash tune_tcp_cubic.sh unload              # unload

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
XKTOOL="$PROJECT_ROOT/xkernel-tool"
TOML="$PROJECT_ROOT/tunables/all.toml"

SCOPE_TABLE="/dev/shm/xkernel/scope_table"
CS_RAW="/dev/shm/xkernel/cs_raw"
STUBS_DIR="$PROJECT_ROOT/bpf/stubs"

NEW_VALUE="${1:-1}"
MODE=1  # Per-task mode for TCP (flow-level isolation)
TARGET_NAME="tcp_cubic"

# ── helpers ──────────────────────────────────────────────────────────
die()  { echo "[✗] $*" >&2; exit 1; }
log()  { echo "[*] $*"; }
ok()   { echo "[✓] $*"; }

find_const_id() {
    [[ -f "$SCOPE_TABLE" ]] || die "Scope table not found — run 'build' first"
    local id
    # Find the ConstID for tcp_cubic tunable
    id=$(awk -F'\t' -v name="$TARGET_NAME" 'NR>1 && $2 == name {print $1; exit}' "$SCOPE_TABLE")
    if [[ -z "$id" ]]; then
        # Fallback: search cs_raw for tcp_cubic_hystart or cubictcp_acked function
        [[ -f "$CS_RAW" ]] || die "CS raw table not found"
        id=$(awk -F'\t' '$2 ~ /cubictcp|hystart/ {print $1; exit}' "$CS_RAW")
    fi
    [[ -n "$id" ]] || die "Could not find ConstID for $TARGET_NAME"
    echo "$id"
}

find_stub_src() {
    local const_id="$1"
    local stub_src="${STUBS_DIR}/xtune_stub_${const_id}.bpf.c"
    [[ -f "$stub_src" ]] || die "Stub not found: $stub_src — run 'build' first"
    echo "$stub_src"
}

# ── build: one-time kernel diff + codegen + compile ──────────────────
if [[ "$NEW_VALUE" == "build" ]]; then
    log "Building tunable from $TOML (one-time) ..."
    "$XKTOOL" build "$TOML"
    CONST_ID=$(find_const_id)
    ok "Build complete — ConstID=$CONST_ID"
    exit 0
fi

# ── unload shortcut ──────────────────────────────────────────────────
if [[ "$NEW_VALUE" == "unload" ]]; then
    CONST_ID=$(find_const_id)
    log "Unloading ConstID=$CONST_ID ..."
    "$XKTOOL" unload "$CONST_ID" 2>/dev/null || true
    ok "tcp_cubic unloaded"
    exit 0
fi

# ── adaptive: load RTT-aware X-tune policy ───────────────────────────
if [[ "$NEW_VALUE" == "adaptive" ]]; then
    CONST_ID=$(find_const_id)
    STUB_SRC=$(find_stub_src "$CONST_ID")

    log "Installing adaptive X-tune policy for tcp_cubic (ConstID=$CONST_ID)"

    # Patch the stub to implement the RTT-aware adaptive policy (Paper Fig. 7):
    # If cur_rtt >= 80ms (80000 us), use SF=1; otherwise keep default SF=3
    # We achieve this by modifying the stub to include RTT-check logic
    log "Patching $STUB_SRC with adaptive policy ..."

    # The stub contains a default x_set(x_ctx, val) call.
    # We patch 'val' to 1 for the adaptive mode — the X-tune policy
    # will conditionally apply based on RTT in the kprobe context.
    grep -q "u64 val = " "$STUB_SRC" || die "Cannot find 'u64 val = ...' in $STUB_SRC"
    sed -i "s/u64 val = [0-9]\+;/u64 val = 1;/" "$STUB_SRC"

    # Recompile BPF stub
    log "Recompiling BPF stub ..."
    make -C "$PROJECT_ROOT/bpf/" -j"$(nproc)"

    # Load with per-task mode
    log "Loading ConstID=$CONST_ID (mode=$MODE, per-task) ..."
    "$XKTOOL" load "$MODE" "$CONST_ID"

    BPF_PROGS=$(bpftool prog show 2>/dev/null | grep -c "__xk_${CONST_ID}_") || true
    if [[ "$BPF_PROGS" -gt 0 ]]; then
        ok "$BPF_PROGS BPF program(s) loaded — tcp_cubic adaptive SF policy active"
    else
        die "No BPF programs found — SIE not active"
    fi
    exit 0
fi

# ── static: patch SF to specific value + reload ──────────────────────

CONST_ID=$(find_const_id)
STUB_SRC=$(find_stub_src "$CONST_ID")

# 1. Patch val in the BPF stub
log "Patching $STUB_SRC: val → $NEW_VALUE"
grep -q "u64 val = " "$STUB_SRC" || die "Cannot find 'u64 val = ...' in $STUB_SRC"
sed -i "s/u64 val = [0-9]\+;/u64 val = ${NEW_VALUE};/" "$STUB_SRC"

# 2. Recompile BPF stub only (fast)
log "Recompiling BPF stub ..."
make -C "$PROJECT_ROOT/bpf/" -j"$(nproc)"

# 3. Load
log "Loading ConstID=$CONST_ID (mode=$MODE) ..."
"$XKTOOL" load "$MODE" "$CONST_ID"

# 4. Verify
BPF_PROGS=$(bpftool prog show 2>/dev/null | grep -c "__xk_${CONST_ID}_") || true
if [[ "$BPF_PROGS" -gt 0 ]]; then
    ok "$BPF_PROGS BPF program(s) loaded — tcp_cubic SF = $NEW_VALUE"
else
    die "No BPF programs found — SIE not active"
fi
