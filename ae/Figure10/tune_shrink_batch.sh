#!/usr/bin/env bash
# tune_shrink_batch.sh — Patch, reload, or unload SHRINK_BATCH
#
# Assumes `xkernel-tool build` has already been run once (by run.sh).
# This script only patches the BPF stub value, recompiles BPF, and reloads —
# no kernel recompilation needed.  This is a key benefit of KernelX:
# varying perf-const values at runtime without rebuilding the kernel.
#
# Usage:
#   sudo bash tune_shrink_batch.sh build     # one-time build
#   sudo bash tune_shrink_batch.sh <VALUE>   # patch + reload
#   sudo bash tune_shrink_batch.sh unload    # unload

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
XKTOOL="$PROJECT_ROOT/xkernel-tool"
TOML="$PROJECT_ROOT/tunables/shrink_batch.toml"

SCOPE_TABLE="/dev/shm/xkernel/scope_table"
STUBS_DIR="$PROJECT_ROOT/bpf/stubs"

NEW_VALUE="${1:-32}"
MODE=0  # Immediate mode

# ── helpers ──────────────────────────────────────────────────────────
die()  { echo "[✗] $*" >&2; exit 1; }
log()  { echo "[*] $*"; }
ok()   { echo "[✓] $*"; }

find_const_id() {
    [[ -f "$SCOPE_TABLE" ]] || die "Scope table not found — run 'build' first"
    local id
    id=$(awk -F'\t' 'NR>1 && $6 ~ /xtune_stub_.*\.bpf\.o/ {print $1; exit}' "$SCOPE_TABLE")
    [[ -n "$id" ]] || die "Could not find ConstID in scope table"
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
    BUILD_OUT=$("$XKTOOL" build "$TOML" 2>&1)
    echo "$BUILD_OUT"
    if echo "$BUILD_OUT" | grep -q "No BPF stubs to compile"; then
        die "Codegen failed — no BPF stubs generated"
    fi
    CONST_ID=$(echo "$BUILD_OUT" | grep -oP 'ConstID \K[0-9]+' | tail -1)
    ok "Build complete — ConstID=$CONST_ID"
    exit 0
fi

# ── unload shortcut ──────────────────────────────────────────────────
if [[ "$NEW_VALUE" == "unload" ]]; then
    CONST_ID=$(find_const_id)
    log "Unloading ConstID=$CONST_ID ..."
    "$XKTOOL" unload "$CONST_ID"
    ok "SHRINK_BATCH unloaded"
    exit 0
fi

# ── patch + reload (no kernel rebuild) ───────────────────────────────

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
    ok "$BPF_PROGS BPF program(s) loaded — SHRINK_BATCH = $NEW_VALUE"
else
    die "No BPF programs found — SIE not active"
fi
