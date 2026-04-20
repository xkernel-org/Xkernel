#!/usr/bin/env bash
# tune_softirq_restart.sh — Patch, reload, or unload MAX_SOFTIRQ_RESTART
#
# Assumes `xkernel-tool build` has already been run once (by run.sh).
# This script only patches the BPF stub value, recompiles BPF, and reloads —
# no kernel recompilation needed.
#
# Usage:
#   sudo bash tune_softirq_restart.sh build     # one-time build
#   sudo bash tune_softirq_restart.sh <VALUE>   # patch + reload
#   sudo bash tune_softirq_restart.sh unload    # unload

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
XKTOOL="$PROJECT_ROOT/xkernel-tool"
TOML="$PROJECT_ROOT/tunables/max_softirq_restart.toml"

SCOPE_TABLE="/dev/shm/xkernel/scope_table"
CS_RAW="/dev/shm/xkernel/cs_raw"
STUBS_DIR="$PROJECT_ROOT/bpf/stubs"

NEW_VALUE="${1:-1}"
MODE=0  # Immediate mode
TARGET_FUNC="handle_softirqs"

# ── helpers ──────────────────────────────────────────────────────────
die()  { echo "[✗] $*" >&2; exit 1; }
log()  { echo "[*] $*"; }
ok()   { echo "[✓] $*"; }

find_const_id() {
    [[ -f "$CS_RAW" ]] || die "CS raw table not found — run 'build' first"
    local id
    # Use last match (most recently built) in case stale entries exist
    id=$(awk -F'\t' -v fn="$TARGET_FUNC" '$2 == fn {id=$1} END{print id}' "$CS_RAW")
    [[ -n "$id" ]] || die "Could not find ConstID for $TARGET_FUNC in $CS_RAW"
    echo "$id"
}

find_stub_src() {
    local const_id="$1"
    local bpf_obj
    bpf_obj=$(awk -F'\t' -v id="$const_id" '$1 == id {print $6; exit}' "$SCOPE_TABLE")
    [[ -n "$bpf_obj" ]] || die "No BPF_File found for ConstID=$const_id"
    local stub_src="${STUBS_DIR}/${bpf_obj%.bpf.o}.bpf.c"
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
    "$XKTOOL" unload "$CONST_ID"
    ok "MAX_SOFTIRQ_RESTART unloaded"
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
    ok "$BPF_PROGS BPF program(s) loaded — MAX_SOFTIRQ_RESTART = $NEW_VALUE"
else
    die "No BPF programs found — SIE not active"
fi
