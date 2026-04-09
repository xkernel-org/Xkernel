#!/usr/bin/env bash
# tune_shrink_batch.sh — Use xkernel-tool to set SHRINK_BATCH to a new value
#
# This script builds the SHRINK_BATCH tunable, patches the generated BPF stub
# to use the specified value (original: 128), recompiles, and loads it in
# immediate mode (mode 0).
#
# Usage:
#   sudo bash tune_shrink_batch.sh 32         # set SHRINK_BATCH = 32
#   sudo bash tune_shrink_batch.sh unload     # unload the tunable

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
XKTOOL="$PROJECT_ROOT/xkernel-tool"
TOML="$PROJECT_ROOT/tunables/shrink_batch.toml"

SCOPE_TABLE="/dev/shm/xkernel/scope_table"
CS_RAW="/dev/shm/xkernel/cs_raw"
STUBS_DIR="$PROJECT_ROOT/bpf/stubs"

NEW_VALUE="${1:-32}"
ORIG_VALUE=128
MODE=0  # Immediate mode

# ── helpers ──────────────────────────────────────────────────────────
die()  { echo "[✗] $*" >&2; exit 1; }
log()  { echo "[*] $*"; }
ok()   { echo "[✓] $*"; }

find_const_id() {
    [[ -f "$SCOPE_TABLE" ]] || die "Scope table not found at $SCOPE_TABLE — build first"
    local id
    # BPF_File column (6) contains xtune_stub_<ConstID>.bpf.o — match by stub pattern
    id=$(awk -F'\t' 'NR>1 && $6 ~ /xtune_stub_.*\.bpf\.o/ {print $1; exit}' "$SCOPE_TABLE")
    [[ -n "$id" ]] || die "Could not find ConstID for SHRINK_BATCH in $SCOPE_TABLE"
    echo "$id"
}

find_stub_src() {
    local const_id="$1"
    local stub_src="${STUBS_DIR}/xtune_stub_${const_id}.bpf.c"
    [[ -f "$stub_src" ]] || die "Stub source not found: $stub_src"
    echo "$stub_src"
}

# ── unload shortcut ──────────────────────────────────────────────────
if [[ "$NEW_VALUE" == "unload" ]]; then
    CONST_ID=$(find_const_id)
    log "Unloading ConstID=$CONST_ID ..."
    "$XKTOOL" unload "$CONST_ID"
    ok "SHRINK_BATCH unloaded"
    exit 0
fi

# ── main flow ────────────────────────────────────────────────────────

# 1. Build the tunable
log "Building tunable from $TOML ..."
BUILD_OUT=$("$XKTOOL" build "$TOML" 2>&1)
echo "$BUILD_OUT"

# 2. Resolve ConstID from build output (e.g., "SHRINK_BATCH -> ConstID 1")
CONST_ID=$(echo "$BUILD_OUT" | grep -oP 'ConstID \K[0-9]+' | tail -1)
if [[ -z "$CONST_ID" ]]; then
    # Fallback: look up from scope table
    CONST_ID=$(find_const_id)
fi
log "SHRINK_BATCH → ConstID=$CONST_ID"

# 3. Patch the BPF stub: change val from original to NEW_VALUE
STUB_SRC=$(find_stub_src "$CONST_ID")
log "Patching $STUB_SRC: val $ORIG_VALUE → $NEW_VALUE"

if ! grep -q "u64 val = " "$STUB_SRC"; then
    die "Cannot find 'u64 val = ...' in $STUB_SRC"
fi
sed -i "s/u64 val = [0-9]\+;/u64 val = ${NEW_VALUE};/" "$STUB_SRC"

# 4. Recompile the patched stub
log "Recompiling BPF stubs ..."
make -C "$PROJECT_ROOT/bpf/" -j"$(nproc)"

# 5. Load with immediate mode
log "Loading ConstID=$CONST_ID (mode=$MODE) ..."
"$XKTOOL" load "$MODE" "$CONST_ID"

ok "SHRINK_BATCH is now set to $NEW_VALUE (ConstID=$CONST_ID, mode=$MODE)"
