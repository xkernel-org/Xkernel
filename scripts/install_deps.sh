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
DO_KERNEL_SRC=false
DO_ALL=true

for arg in "$@"; do
    case "$arg" in
        --apt)        DO_APT=true;        DO_ALL=false ;;
        --libbpf)     DO_LIBBPF=true;     DO_ALL=false ;;
        --vmlinux)    DO_VMLINUX=true;     DO_ALL=false ;;
        --pytest)     DO_PYTEST=true;      DO_ALL=false ;;
        --kernel-src) DO_KERNEL_SRC=true;  DO_ALL=false ;;
        -h|--help)
            echo "Usage: sudo bash $0 [--apt] [--libbpf] [--vmlinux] [--pytest] [--kernel-src]"
            echo ""
            echo "  (no flags)     Install everything"
            echo "  --apt          Only install apt packages (clang, llvm, pahole, ...)"
            echo "  --libbpf       Only build & install libbpf from source"
            echo "  --vmlinux      Only generate bpf/vmlinux.h from running kernel BTF"
            echo "  --pytest       Only install pytest for running tests"
            echo "  --kernel-src   Only download kernel source for the running kernel"
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
    DO_KERNEL_SRC=true
fi

# ── Check root for apt / libbpf ─────────────────────────────────────
if ($DO_APT || $DO_LIBBPF || $DO_KERNEL_SRC) && [[ $EUID -ne 0 ]]; then
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
        flex bison libssl-dev bc libncurses-dev xz-utils rsync dwarves \
        2>&1 | tail -1
    echo -e "  ${GREEN}✓${RST} clang llvm pahole pkg-config libelf-dev build-essential flex bison libssl-dev"
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

# ── 5. Kernel source for the running kernel ─────────────────────────
install_kernel_source() {
    local kver
    kver=$(uname -r)
    info "Downloading Ubuntu kernel source for running kernel ($kver)..."

    # Determine the target directory: ~/linux-<base_version>
    # e.g., for 6.8.0-101-generic → ~/linux-6.8.0
    local base_ver="${kver%%-*}"                     # 6.8.0
    local kernel_dir="${HOME}/linux-${base_ver}"

    if [[ -d "$kernel_dir" && -f "$kernel_dir/Makefile" ]]; then
        warn "Kernel source already exists at $kernel_dir, skipping"
        echo -e "  Set ${BOLD}export KERNEL_DIR=$kernel_dir${RST} to use it"
        return
    fi

    # Resolve the source package name from the installed kernel image package.
    local src_pkg=""
    for candidate in "linux-image-unsigned-${kver}" "linux-image-${kver}"; do
        local info_line
        info_line=$(apt-cache show "$candidate" 2>/dev/null | grep -m1 "^Source:" || true)
        if [[ -n "$info_line" ]]; then
            src_pkg=$(echo "$info_line" | awk '{print $2}')
            break
        fi
    done

    if [[ -z "$src_pkg" ]]; then
        die "Cannot determine source package for kernel $kver. " \
            "Make sure linux-image-*-${kver} is installed and apt cache is up to date."
    fi

    # The exact installed version (e.g., 6.8.0-101.101) may no longer be in
    # the apt repos — Ubuntu only keeps the original release and latest update.
    # Pick the newest available source version for this package instead; the
    # source tree is the same across all ABI bumps within a series, and we
    # apply the running kernel's /boot/config anyway.
    local pkg_ver
    pkg_ver=$(apt-cache madison "$src_pkg" 2>/dev/null \
        | awk -F'|' '/Sources/ {gsub(/ /,"",$2); print $2}' \
        | sort -V | tail -1)

    if [[ -z "$pkg_ver" ]]; then
        die "No source version found for package '$src_pkg' in apt repos. " \
            "Check that deb-src repositories are enabled and run 'apt-get update'."
    fi

    info "Source package: ${src_pkg}=${pkg_ver}"

    # Ensure deb-src repositories are enabled
    if ! apt-get indextargets --format '$(CREATED_BY)' 2>/dev/null | grep -q "^Sources"; then
        warn "deb-src repositories not enabled — attempting to enable..."
        if [[ -f /etc/apt/sources.list.d/ubuntu.sources ]]; then
            # DEB822 format (Ubuntu 24.04+): ensure "deb-src" is in Types
            sed -i 's/^Types: deb$/Types: deb deb-src/' /etc/apt/sources.list.d/ubuntu.sources
        elif [[ -f /etc/apt/sources.list ]]; then
            # Traditional format: uncomment deb-src lines
            sed -i 's/^# *deb-src/deb-src/' /etc/apt/sources.list
        fi
        apt-get update -qq
    fi

    # Install build dependencies for apt-get source
    apt-get install -y dpkg-dev 2>&1 | tail -1

    # Download and extract the source (drop root — apt-get source dislikes running as root)
    local tmpdir
    tmpdir=$(mktemp -d)
    chmod 777 "$tmpdir"
    pushd "$tmpdir" > /dev/null

    info "Running apt-get source ${src_pkg}=${pkg_ver} (this may take a few minutes)..."
    if [[ -n "${SUDO_USER:-}" ]]; then
        su "$SUDO_USER" -c "cd '$tmpdir' && apt-get source '${src_pkg}=${pkg_ver}'" 2>&1 | tail -3
    else
        apt-get source "${src_pkg}=${pkg_ver}" 2>&1 | tail -3
    fi

    # Find the extracted source directory (largest directory matching linux-*)
    local src_dir
    src_dir=$(find . -maxdepth 1 -type d -name 'linux-*' | head -1)
    if [[ -z "$src_dir" || ! -f "$src_dir/Makefile" ]]; then
        die "Failed to extract kernel source — no linux-*/Makefile found in $tmpdir"
    fi

    # Move to target location
    mv "$src_dir" "$kernel_dir"
    popd > /dev/null
    rm -rf "$tmpdir"

    # Prepare the source tree with the running kernel's config and compile
    pushd "$kernel_dir" > /dev/null
    if [[ -f "/boot/config-${kver}" ]]; then
        cp "/boot/config-${kver}" .config
        # Disable Ubuntu-specific signing keys (not available outside Canonical)
        scripts/config -d CONFIG_SYSTEM_TRUSTED_KEYS
        scripts/config -d CONFIG_SYSTEM_REVOCATION_KEYS
        make olddefconfig 2>&1 | tail -1
        info "Applied /boot/config-${kver} to source tree"
    fi

    info "Compiling kernel (this will take a while)..."
    /usr/bin/time -v make -j"$(nproc)" 2>&1 | tail -5
    chmod +x ./debian/scripts/sign-module 2>/dev/null || true
    make modules_install -j"$(nproc)" 2>&1 | tail -3
    make install 2>&1 | tail -3
    popd > /dev/null

    echo -e "  ${GREEN}✓${RST} Kernel source installed at ${BOLD}$kernel_dir${RST}"
    echo -e "  Use: ${BOLD}export KERNEL_DIR=$kernel_dir${RST}"
}

# ── Run selected steps ───────────────────────────────────────────────
echo -e "${BOLD}KernelX Dependency Installer${RST}"
echo "=============================="
echo

$DO_APT        && install_apt          && echo
$DO_LIBBPF     && install_libbpf       && echo
$DO_VMLINUX    && generate_vmlinux     && echo
$DO_PYTEST     && install_pytest       && echo
$DO_KERNEL_SRC && install_kernel_source && echo

echo -e "${GREEN}Done.${RST} Run ${BOLD}./xkernel-tool doctor${RST} to verify."
