#!/usr/bin/env bash
# tune_blk_max_req.sh — Use xkernel-tool to set BLK_MAX_REQUEST_COUNT = 1
#
# This script builds the BLK_MAX_REQUEST_COUNT tunable, patches the
# generated BPF stub to use value 1 (original: 32), recompiles, and
# loads it in immediate mode (mode 0).
#
# Usage:
#   sudo bash tune_blk_max_req.sh          # default: set value to 1
#   sudo bash tune_blk_max_req.sh 16       # custom value
#   sudo bash tune_blk_max_req.sh unload   # unload the tunable

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
XKTOOL="$PROJECT_ROOT/xkernel-tool"
TOML="$PROJECT_ROOT/tunables/blk_max_request_count.toml"

SCOPE_TABLE="/dev/shm/xkernel/scope_table"
CS_RAW="/dev/shm/xkernel/cs_raw"
STUBS_DIR="$PROJECT_ROOT/bpf/stubs"

NEW_VALUE="${1:-1}"
ORIG_VALUE=32
MODE=0  # Immediate mode
TARGET_FUNC="blk_add_rq_to_plug"

# ── helpers ──────────────────────────────────────────────────────────
die()  { echo "[✗] $*" >&2; exit 1; }
log()  { echo "[*] $*"; }
ok()   { echo "[✓] $*"; }

find_const_id() {
    # Look up the ConstID for BLK_MAX_REQUEST_COUNT from CS raw table.
    # CS raw format: ConstID\tFunctionName\tStartOffset\tEndOffset
    [[ -f "$CS_RAW" ]] || die "CS raw table not found at $CS_RAW — build first"
    local id
    id=$(awk -F'\t' -v fn="$TARGET_FUNC" '$2 == fn {print $1; exit}' "$CS_RAW")
    [[ -n "$id" ]] || die "Could not find ConstID for $TARGET_FUNC in $CS_RAW"
    echo "$id"
}

find_stub_src() {
    local const_id="$1"
    # Read BPF_File (column 6) from scope table for this ConstID
    local bpf_obj
    bpf_obj=$(awk -F'\t' -v id="$const_id" '$1 == id {print $6; exit}' "$SCOPE_TABLE")
    [[ -n "$bpf_obj" ]] || die "No BPF_File found for ConstID=$const_id"
    local stub_src="${STUBS_DIR}/${bpf_obj%.bpf.o}.bpf.c"
    [[ -f "$stub_src" ]] || die "Stub source not found: $stub_src"
    echo "$stub_src"
}

# ── unload shortcut ──────────────────────────────────────────────────
if [[ "$NEW_VALUE" == "unload" ]]; then
    CONST_ID=$(find_const_id)
    log "Unloading ConstID=$CONST_ID ..."
    "$XKTOOL" unload "$CONST_ID"
    ok "BLK_MAX_REQUEST_COUNT unloaded"
    exit 0
fi

# ── main flow ────────────────────────────────────────────────────────

# 1. Build the tunable (generates BPF stubs + populates scope/CS/SS tables)
log "Building tunables from $TOML ..."
"$XKTOOL" build "$TOML"

# 2. Resolve ConstID
CONST_ID=$(find_const_id)
log "BLK_MAX_REQUEST_COUNT → ConstID=$CONST_ID"

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

ok "BLK_MAX_REQUEST_COUNT is now set to $NEW_VALUE (ConstID=$CONST_ID, mode=$MODE)"
