#!/usr/bin/env bash
# install_rocksdb.sh — One-click build RocksDB + db_bench with io_uring support
#
# Usage:
#   bash ae/Figure1b/install_rocksdb.sh
#
# After installation, db_bench is available at:
#   ae/Figure1b/rocksdb/db_bench
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROCKSDB_DIR="$SCRIPT_DIR/rocksdb"
ROCKSDB_VERSION="v9.11.2"
NPROC=$(nproc)

RED='\033[0;31m'; GREEN='\033[0;32m'; BOLD='\033[1m'; RST='\033[0m'
log()    { echo -e "${BOLD}[$(date '+%H:%M:%S')]${RST} $*"; }
log_ok() { echo -e "${GREEN}[$(date '+%H:%M:%S')] ✓${RST} $*"; }
die()    { echo -e "${RED}[$(date '+%H:%M:%S')] ✗${RST} $*" >&2; exit 1; }

# ── 1. Install build dependencies ───────────────────────────────────
log "Installing build dependencies ..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    build-essential cmake git \
    libgflags-dev libsnappy-dev zlib1g-dev \
    libbz2-dev liblz4-dev libzstd-dev \
    liburing-dev \
    2>&1 | tail -1

# ── 2. Clone RocksDB ────────────────────────────────────────────────
if [[ -d "$ROCKSDB_DIR" ]]; then
    log "RocksDB directory already exists at $ROCKSDB_DIR"
    cd "$ROCKSDB_DIR"
    CURRENT_TAG=$(git describe --tags --exact-match 2>/dev/null || echo "unknown")
    if [[ "$CURRENT_TAG" != "$ROCKSDB_VERSION" ]]; then
        log "Existing version ($CURRENT_TAG) differs from $ROCKSDB_VERSION, re-cloning..."
        cd "$SCRIPT_DIR"
        rm -rf "$ROCKSDB_DIR"
    else
        log "Already at $ROCKSDB_VERSION, skipping clone"
    fi
fi

if [[ ! -d "$ROCKSDB_DIR" ]]; then
    log "Cloning RocksDB $ROCKSDB_VERSION ..."
    git clone --depth 1 --branch "$ROCKSDB_VERSION" \
        https://github.com/facebook/rocksdb.git "$ROCKSDB_DIR"
fi

cd "$ROCKSDB_DIR"

# ── 3. Build db_bench (release mode, with io_uring) ─────────────────
log "Building db_bench (release, io_uring enabled) with $NPROC jobs ..."

# Use cmake for a clean release build
BUILD_DIR="$ROCKSDB_DIR/build"
mkdir -p "$BUILD_DIR"
cd "$BUILD_DIR"

cmake .. \
    -DCMAKE_BUILD_TYPE=Release \
    -DWITH_SNAPPY=ON \
    -DWITH_LZ4=ON \
    -DWITH_ZSTD=ON \
    -DWITH_BZ2=ON \
    -DWITH_TESTS=OFF \
    -DWITH_TOOLS=ON \
    -DWITH_BENCHMARK_TOOLS=ON \
    -DWITH_CORE_TOOLS=OFF \
    -DROCKSDB_BUILD_SHARED=OFF \
    2>&1 | tail -5

make -j"$NPROC" db_bench 2>&1 | tail -5

# Symlink for convenience
ln -sf "$BUILD_DIR/db_bench" "$ROCKSDB_DIR/db_bench"

# ── 4. Verify ────────────────────────────────────────────────────────
if [[ -x "$ROCKSDB_DIR/db_bench" ]]; then
    log_ok "db_bench built successfully: $ROCKSDB_DIR/db_bench"
    "$ROCKSDB_DIR/db_bench" --version 2>/dev/null || true
else
    die "db_bench build failed"
fi

log_ok "Installation complete. Run: sudo bash ae/Figure1b/run1b.sh"
