#!/usr/bin/env bash
# Xkernel build script — installs dependencies and builds all components.
#
# Usage:
#   sudo ./build.sh              # Full build (deps + kernel modules + BPF)
#   sudo ./build.sh --skip-deps  # Skip dependency installation
#
# Prerequisites:
#   - Kernel source at $KERNELDIR or $KERNEL_DIR (default: ~/linux-6.8.0)
#
# For selective dep installation, use: ./xkernel-tool setup

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
KERNELDIR="${KERNELDIR:-${KERNEL_DIR:-$HOME/linux-6.8.0}}"
SKIP_DEPS=false

for arg in "$@"; do
    case "$arg" in
        --skip-deps) SKIP_DEPS=true ;;
    esac
done

# ── Main ──────────────────────────────────────────────────────────────
echo "============================================"
echo "  Xkernel Build"
echo "============================================"
echo "  Kernel source: $KERNELDIR"
echo "  Project root:  $SCRIPT_DIR"
echo ""

# ── 1. Dependencies (delegates to install_deps.sh) ───────────────────
if [ "$SKIP_DEPS" = false ]; then
    bash "$SCRIPT_DIR/scripts/install_deps.sh"
fi

# ── 2. Kernel modules ────────────────────────────────────────────────
echo "==> Building kernel modules..."
pushd "$SCRIPT_DIR/kernel/kfuncs" > /dev/null
make -j"$(nproc)" CC="${CC:-gcc}"
popd > /dev/null
pushd "$SCRIPT_DIR/kernel/consistency" > /dev/null
make -j"$(nproc)" CC="${CC:-gcc}"
popd > /dev/null
echo "    xk-kfuncs.ko      OK"
echo "    xk-consistency.ko  OK"

# ── 3. BPF programs ──────────────────────────────────────────────────
echo "==> Compiling BPF programs..."
make -C "$SCRIPT_DIR/bpf" -j"$(nproc)"
echo "    $(ls "$SCRIPT_DIR"/bpf/stubs/*.bpf.o 2>/dev/null | wc -l) programs compiled"

echo ""
echo "============================================"
echo "  Build complete"
echo "============================================"
echo ""
echo "Next steps:"
echo "  ./xkernel-tool run tunables/blk_max_request_count.toml  # Build + load in one step"
echo "  ./xkernel-tool load 0 <ConstID>   # Load BPF program (Immediate mode)"
