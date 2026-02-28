#!/usr/bin/env bash
# Xkernel build script — installs dependencies and builds all components.
#
# Usage:
#   sudo ./build.sh              # Full build (deps + kernel modules + BPF)
#   sudo ./build.sh --skip-deps  # Skip dependency installation
#
# Prerequisites:
#   - Custom kernel 6.14.0-xkernel installed and booted (see install.sh)
#   - Kernel source at $KERNELDIR (default: ~/linux-6.14.0-xkernel)

set -euo pipefail

KERNELDIR="${KERNELDIR:-$HOME/linux-6.14.0-xkernel}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LIBBPF_DIR="${SCRIPT_DIR}/../libbpf"
SKIP_DEPS=false

for arg in "$@"; do
    case "$arg" in
        --skip-deps) SKIP_DEPS=true ;;
    esac
done

# ── 1. System packages ─────────────────────────────────────────────────
install_deps() {
    echo "==> Installing system packages..."
    apt-get update -qq
    apt-get install -y \
        clang llvm pahole pkg-config libelf-dev \
        libgflags-dev build-essential
}

# ── 2. libbpf (from source, latest) ───────────────────────────────────
install_libbpf() {
    echo "==> Building libbpf from source..."
    if [ ! -d "$LIBBPF_DIR" ]; then
        git clone https://github.com/libbpf/libbpf.git "$LIBBPF_DIR"
    fi
    pushd "$LIBBPF_DIR/src" > /dev/null
    make -j"$(nproc)"
    make install                    # headers -> /usr/include/bpf/
    cp ./*.so /usr/local/lib/
    ldconfig
    popd > /dev/null
    echo "    libbpf $(grep LIBBPF_MINOR_VERSION "$LIBBPF_DIR/src/libbpf_version.h" \
        | awk '{print $3}' | head -1) installed"
}

# ── 3. bpftool (from kernel source tree) ──────────────────────────────
install_bpftool() {
    echo "==> Building bpftool..."
    local bpftool_src="${KERNELDIR}/tools/bpf/bpftool"
    if [ ! -d "$bpftool_src" ]; then
        echo "    ERROR: Kernel source not found at ${KERNELDIR}"
        echo "    Run install.sh first to download the kernel source."
        exit 1
    fi
    make -C "$bpftool_src" -j"$(nproc)"
    cp "$bpftool_src/bpftool" /usr/local/sbin/bpftool
    echo "    $(bpftool version)"
}

# ── 4. Kernel modules (kfuncs + consistency) ──────────────────────────
build_kernel_modules() {
    echo "==> Building kernel modules..."
    pushd "$SCRIPT_DIR/kernel/kfuncs" > /dev/null
    make -j"$(nproc)"
    popd > /dev/null
    pushd "$SCRIPT_DIR/kernel/consistency" > /dev/null
    make -j"$(nproc)"
    popd > /dev/null
    echo "    xk-kfuncs.ko      OK"
    echo "    xk-consistency.ko  OK"
}

# ── 5. vmlinux.h ─────────────────────────────────────────────────────
generate_vmlinux_h() {
    local vmlinux_h="$SCRIPT_DIR/bpf/vmlinux.h"
    if [ -s "$vmlinux_h" ]; then
        echo "==> vmlinux.h already exists ($(wc -l < "$vmlinux_h") lines), skipping"
        return
    fi
    echo "==> Generating vmlinux.h from running kernel BTF..."
    bpftool btf dump file /sys/kernel/btf/vmlinux format c > "$vmlinux_h"
    echo "    $(wc -l < "$vmlinux_h") lines"
}

# ── 6. BPF programs ──────────────────────────────────────────────────
build_bpf() {
    echo "==> Compiling BPF programs..."
    make -C "$SCRIPT_DIR/bpf" -j"$(nproc)"
    echo "    $(ls "$SCRIPT_DIR"/bpf/stubs/*.bpf.o 2>/dev/null | wc -l) programs compiled"
}

# ── Main ──────────────────────────────────────────────────────────────
echo "============================================"
echo "  Xkernel Build"
echo "============================================"
echo "  Kernel source: $KERNELDIR"
echo "  Project root:  $SCRIPT_DIR"
echo ""

if [ "$SKIP_DEPS" = false ]; then
    install_deps
    install_libbpf
    install_bpftool
fi

build_kernel_modules
generate_vmlinux_h
build_bpf

echo ""
echo "============================================"
echo "  Build complete"
echo "============================================"
echo ""
echo "Next steps:"
echo "  ./xkernel-tool build              # Run codegen pipeline (gen + codegen + compile)"
echo "  ./xkernel-tool load 0 <ConstID>   # Load BPF program (Immediate mode)"
