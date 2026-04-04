#!/usr/bin/env bash
# scripts/install_deps.sh — One-click dependency installer for KernelX
#
# Usage:
#   sudo bash scripts/install_deps.sh          # Install everything
#   sudo bash scripts/install_deps.sh --apt    # Only apt packages
#   sudo bash scripts/install_deps.sh --libbpf # Only libbpf
#   sudo bash scripts/install_deps.sh --vmlinux # Only generate vmlinux.h
#
set -uo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BOLD='\033[1m'
RST='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

info()  { echo -e "${GREEN}==>${RST} ${BOLD}$1${RST}"; }
warn()  { echo -e "${YELLOW}==>${RST} $1"; }
die()   { echo -e "${RED}ERROR:${RST} $1" >&2; exit 1; }

# ── Parse arguments ──────────────────────────────────────────────────
DO_APT=false
DO_LIBBPF=false
DO_VMLINUX=false
DO_PYTEST=false
DO_ALL=true

for arg in "$@"; do
    case "$arg" in
        --apt)     DO_APT=true;    DO_ALL=false ;;
        --libbpf)  DO_LIBBPF=true; DO_ALL=false ;;
        --vmlinux) DO_VMLINUX=true; DO_ALL=false ;;
        --pytest)  DO_PYTEST=true; DO_ALL=false ;;
        -h|--help)
            echo "Usage: sudo bash $0 [--apt] [--libbpf] [--vmlinux] [--pytest]"
            echo ""
            echo "  (no flags)  Install everything"
            echo "  --apt       Only install apt packages (clang, llvm, pahole, ...)"
            echo "  --libbpf    Only build & install libbpf from source"
            echo "  --vmlinux   Only generate bpf/vmlinux.h from running kernel BTF"
            echo "  --pytest    Only install pytest for running tests"
            exit 0
            ;;
        *)
            die "Unknown option: $arg (try --help)"
            ;;
    esac
done

if $DO_ALL; then
    DO_APT=true
    DO_LIBBPF=true
    DO_VMLINUX=true
    DO_PYTEST=true
fi

# ── Check root for apt / libbpf ─────────────────────────────────────
if ($DO_APT || $DO_LIBBPF) && [[ $EUID -ne 0 ]]; then
    die "This script needs root privileges. Run with: sudo bash $0 $*"
fi

# ── 1. APT packages ─────────────────────────────────────────────────
install_apt() {
    info "Installing system packages via apt..."
    apt-get update -qq
    apt-get install -y \
        clang llvm \
        pahole pkg-config libelf-dev \
        build-essential \
        linux-tools-common \
        2>&1 | tail -1
    echo -e "  ${GREEN}✓${RST} clang llvm pahole pkg-config libelf-dev build-essential"
}

# ── 2. libbpf from source ───────────────────────────────────────────
install_libbpf() {
    info "Building libbpf from source..."
    local libbpf_dir="${PROJECT_ROOT}/../libbpf"
    if [[ ! -d "$libbpf_dir" ]]; then
        git clone --depth 1 https://github.com/libbpf/libbpf.git "$libbpf_dir"
    else
        warn "libbpf directory already exists at $libbpf_dir, reusing"
    fi
    pushd "$libbpf_dir/src" > /dev/null
    make -j"$(nproc)" -s
    make install -s
    cp ./*.so /usr/local/lib/ 2>/dev/null || true
    ldconfig
    popd > /dev/null
    local ver
    ver=$(pkg-config --modversion libbpf 2>/dev/null || echo "unknown")
    echo -e "  ${GREEN}✓${RST} libbpf $ver installed"
}

# ── 3. vmlinux.h ────────────────────────────────────────────────────
generate_vmlinux() {
    info "Generating bpf/vmlinux.h..."
    local vmlinux_h="$PROJECT_ROOT/bpf/vmlinux.h"
    if [[ -s "$vmlinux_h" ]]; then
        warn "bpf/vmlinux.h already exists ($(wc -l < "$vmlinux_h") lines), skipping"
        return
    fi
    if ! command -v bpftool &>/dev/null; then
        die "bpftool not found — install it first, then rerun with --vmlinux"
    fi
    if [[ ! -f /sys/kernel/btf/vmlinux ]]; then
        die "No BTF data at /sys/kernel/btf/vmlinux — kernel must have CONFIG_DEBUG_INFO_BTF=y"
    fi
    bpftool btf dump file /sys/kernel/btf/vmlinux format c > "$vmlinux_h"
    echo -e "  ${GREEN}✓${RST} bpf/vmlinux.h generated ($(wc -l < "$vmlinux_h") lines)"
}

# ── 4. pytest ────────────────────────────────────────────────────────
install_pytest() {
    info "Installing pytest..."
    if python3 -m pytest --version &>/dev/null 2>&1; then
        warn "pytest already installed ($(python3 -m pytest --version 2>&1 | head -1))"
        return
    fi
    if command -v pip3 &>/dev/null; then
        pip3 install pytest
    elif dpkg -l python3-pytest &>/dev/null 2>&1; then
        warn "python3-pytest already installed via apt"
    else
        apt-get install -y python3-pytest 2>&1 | tail -1
    fi
    echo -e "  ${GREEN}✓${RST} pytest installed"
}

# ── Run selected steps ───────────────────────────────────────────────
echo -e "${BOLD}KernelX Dependency Installer${RST}"
echo "=============================="
echo

$DO_APT     && install_apt     && echo
$DO_LIBBPF  && install_libbpf  && echo
$DO_VMLINUX && generate_vmlinux && echo
$DO_PYTEST  && install_pytest  && echo

echo -e "${GREEN}Done.${RST} Run ${BOLD}./xkernel-tool doctor${RST} to verify."
