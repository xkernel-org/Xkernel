#!/usr/bin/env bash
# scripts/install_deps.sh — One-click dependency installer for KernelX
#
# Usage:
#   sudo bash scripts/install_deps.sh          # Install everything
#   sudo bash scripts/install_deps.sh --apt    # Only apt packages
#   sudo bash scripts/install_deps.sh --pahole # Force install newer pahole
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
if [[ -n "${SUDO_USER:-}" ]]; then
    TARGET_HOME="$(getent passwd "$SUDO_USER" | cut -d: -f6)"
else
    TARGET_HOME="$HOME"
fi

info()  { echo -e "${GREEN}==>${RST} ${BOLD}$1${RST}"; }
warn()  { echo -e "${YELLOW}==>${RST} $1"; }
die()   { echo -e "${RED}ERROR:${RST} $1" >&2; exit 1; }

is_ae_linux_614() {
    [[ "$(uname -r)" == "6.14.8-061408-generic" ]]
}

# ── Parse arguments ──────────────────────────────────────────────────
DO_APT=false
DO_PAHOLE=false
DO_LIBBPF=false
DO_VMLINUX=false
DO_PYTEST=false
DO_KERNEL_SRC=false
DO_ALL=true

for arg in "$@"; do
    case "$arg" in
        --apt)        DO_APT=true;        DO_ALL=false ;;
        --pahole)     DO_PAHOLE=true;     DO_ALL=false ;;
        --libbpf)     DO_LIBBPF=true;     DO_ALL=false ;;
        --vmlinux)    DO_VMLINUX=true;     DO_ALL=false ;;
        --pytest)     DO_PYTEST=true;      DO_ALL=false ;;
        --kernel-src) DO_KERNEL_SRC=true;  DO_ALL=false ;;
        -h|--help)
            echo "Usage: sudo bash $0 [--apt] [--pahole] [--libbpf] [--vmlinux] [--pytest] [--kernel-src]"
            echo ""
            echo "  (no flags)     Install standard dependencies; auto-add Linux 6.14 tools when uname -r needs them"
            echo "  --apt          Only install apt packages; auto-add gcc-14/g++-14 on Linux 6.14"
            echo "  --pahole       Force build and install newer pahole from dwarves source"
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
    if is_ae_linux_614; then
        DO_PAHOLE=true
    fi
fi

# ── Check root for apt / libbpf ─────────────────────────────────────
if ($DO_APT || $DO_PAHOLE || $DO_LIBBPF || $DO_KERNEL_SRC) && [[ $EUID -ne 0 ]]; then
    die "This script needs root privileges. Run with: sudo bash $0 $*"
fi

# ── 1. APT packages ─────────────────────────────────────────────────
install_apt() {
    info "Installing system packages via apt..."
    apt-get update -qq
    apt-get install -y \
        clang llvm \
        pahole pkg-config elfutils libdw-dev libelf-dev \
        build-essential \
        linux-tools-common \
        flex bison libssl-dev bc libncurses-dev xz-utils rsync dwarves \
        2>&1 | tail -1
    echo -e "  ${GREEN}✓${RST} clang llvm pahole pkg-config libelf-dev build-essential flex bison libssl-dev"

    if is_ae_linux_614; then
        info "Detected Linux 6.14.8 AE kernel; installing GCC 14 toolchain..."
        apt-get install -y gcc-14 g++-14 2>&1 | tail -1
        echo -e "  ${GREEN}✓${RST} gcc-14 g++-14"
    else
        warn "Running kernel $(uname -r) does not need Figure10/11 Linux 6.14 toolchain; skipping gcc-14/g++-14"
    fi
}

version_ge() {
    local have="$1"
    local need="$2"
    [[ "$(printf '%s\n%s\n' "$need" "$have" | sort -V | head -1)" == "$need" ]]
}

pahole_version() {
    if command -v pahole &>/dev/null; then
        pahole --version 2>/dev/null | grep -oE '[0-9]+(\.[0-9]+)+' | head -1
    fi
}

install_pahole_source() {
    local min_ver="1.26"
    local have
    have=$(pahole_version || true)

    if [[ -n "$have" ]] && version_ge "$have" "$min_ver"; then
        warn "pahole $have already installed; skipping source build"
        return
    fi

    info "Installing pahole >= $min_ver from dwarves source..."
    apt-get install -y cmake git build-essential pkg-config libelf-dev libdw-dev zlib1g-dev 2>&1 | tail -1

    local dwarves_dir="${PROJECT_ROOT}/../dwarves"
    if [[ ! -d "$dwarves_dir" ]]; then
        git clone --depth 1 https://github.com/acmel/dwarves.git "$dwarves_dir"
    else
        warn "dwarves directory already exists at $dwarves_dir, reusing"
    fi

    cmake -S "$dwarves_dir" -B "$dwarves_dir/build" -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=/usr/local 2>&1 | tail -5
    cmake --build "$dwarves_dir/build" -j"$(nproc)" 2>&1 | tail -5
    cmake --install "$dwarves_dir/build" 2>&1 | tail -5
    ldconfig

    have=$(pahole_version || true)
    if [[ -z "$have" ]] || ! version_ge "$have" "$min_ver"; then
        die "pahole source install did not provide version >= $min_ver (found: ${have:-none})"
    fi

    echo -e "  ${GREEN}✓${RST} pahole $have installed"
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
    local bpftool_bin
    bpftool_bin="${BPFTOOL:-}"
    if [[ -z "$bpftool_bin" ]]; then
        bpftool_bin=$(ls /usr/lib/linux-tools/*/bpftool 2>/dev/null | tail -n 1 || true)
    fi
    if [[ -z "$bpftool_bin" ]]; then
        bpftool_bin=$(command -v bpftool 2>/dev/null || true)
    fi
    if [[ -z "$bpftool_bin" ]]; then
        die "bpftool not found — install it first, then rerun with --vmlinux"
    fi
    if [[ ! -f /sys/kernel/btf/vmlinux ]]; then
        die "No BTF data at /sys/kernel/btf/vmlinux — kernel must have CONFIG_DEBUG_INFO_BTF=y"
    fi
    "$bpftool_bin" btf dump file /sys/kernel/btf/vmlinux format c > "$vmlinux_h"
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

    local base_ver="${kver%%-*}"
    local kernel_dir="${TARGET_HOME}/linux-${base_ver}"

    if [[ "$kver" == "6.14.8-061408-generic" ]]; then
        kernel_dir="${TARGET_HOME}/linux-6.14.8-061408-generic"
    fi

    if [[ -d "$kernel_dir" && -f "$kernel_dir/Makefile" ]]; then
        warn "Kernel source already exists at $kernel_dir, skipping"
        echo -e "  Set ${BOLD}export KERNEL_DIR=$kernel_dir${RST} to use it"
        return
    fi

    # Ubuntu mainline kernels are installed from standalone .deb files and do
    # not reliably expose a matching source package through apt. Figure 10/11
    # use this kernel, so fetch the matching upstream source tarball directly.
    if [[ "$kver" == "6.14.8-061408-generic" ]]; then
        info "Detected AE Linux 6.14.8 kernel; downloading upstream source tarball..."
        apt-get install -y build-essential gcc-14 g++-14 bc bison dwarves elfutils flex libdw-dev libelf-dev libssl-dev \
            ncurses-dev rsync xz-utils wget 2>&1 | tail -1
        install_pahole_source

        local tmpdir
        tmpdir=$(mktemp -d)
        chmod 777 "$tmpdir"
        pushd "$tmpdir" > /dev/null

        if [[ -n "${SUDO_USER:-}" ]]; then
            su "$SUDO_USER" -c "cd '$tmpdir' && wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.14.8.tar.xz" 2>&1 | tail -3
        else
            wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.14.8.tar.xz 2>&1 | tail -3
        fi
        tar -xf linux-6.14.8.tar.xz
        mv linux-6.14.8 "$kernel_dir"
        popd > /dev/null
        rm -rf "$tmpdir"

        pushd "$kernel_dir" > /dev/null
        cp "/boot/config-${kver}" .config
        scripts/config -d CONFIG_SYSTEM_TRUSTED_KEYS || true
        scripts/config -d CONFIG_SYSTEM_REVOCATION_KEYS || true
        scripts/config --set-str CONFIG_LOCALVERSION "-061408-generic" || true
        make olddefconfig 2>&1 | tail -1

        info "Preparing kernel source tree for Xkernel code generation..."
        make prepare scripts 2>&1 | tail -5
        make -j"$(nproc)" mm/shrinker.o mm/migrate.o 2>&1 | tail -5
        popd > /dev/null

        if [[ -n "${SUDO_USER:-}" ]]; then
            chown -R "$SUDO_USER:$SUDO_USER" "$kernel_dir"
        fi

        echo -e "  ${GREEN}✓${RST} Kernel source installed at ${BOLD}$kernel_dir${RST}"
        echo -e "  Use: ${BOLD}export KERNEL_DIR=$kernel_dir${RST}"
        return
    fi

    # Resolve source package name from installed kernel image package
    local src_pkg=""
    local candidate info_line
    for candidate in "linux-image-unsigned-${kver}" "linux-image-${kver}"; do
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

    # Ensure deb-src repositories are enabled BEFORE querying source versions
    if ! apt-get indextargets --format '$(CREATED_BY)' 2>/dev/null | grep -q '^Sources$'; then
        warn "deb-src repositories not enabled — attempting to enable..."
        if [[ -f /etc/apt/sources.list.d/ubuntu.sources ]]; then
            # Ubuntu deb822 format
            sed -i '/^Types:/ s/\bdeb-src\b//g; /^Types:/ s/\bdeb\b.*/deb deb-src/' /etc/apt/sources.list.d/ubuntu.sources
        elif [[ -f /etc/apt/sources.list ]]; then
            sed -i 's/^# *deb-src/deb-src/' /etc/apt/sources.list
        fi
        apt-get update -qq
    else
        apt-get update -qq
    fi

    # Now source indexes should exist
    local pkg_ver
    pkg_ver=$(apt-cache madison "$src_pkg" 2>/dev/null \
        | awk -F'|' '/Sources/ {gsub(/ /,"",$2); print $2}' \
        | sort -V | tail -1)

    if [[ -z "$pkg_ver" ]]; then
        die "No source version found for package '$src_pkg' in apt repos even after enabling deb-src. " \
            "Check your Ubuntu source repositories."
    fi

    info "Source package: ${src_pkg}=${pkg_ver}"

    apt-get install -y dpkg-dev 2>&1 | tail -1

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

    local src_dir
    src_dir=$(find . -maxdepth 1 -type d -name 'linux-*' | head -1)
    if [[ -z "$src_dir" || ! -f "$src_dir/Makefile" ]]; then
        die "Failed to extract kernel source — no linux-*/Makefile found in $tmpdir"
    fi

    mv "$src_dir" "$kernel_dir"
    popd > /dev/null
    rm -rf "$tmpdir"

    pushd "$kernel_dir" > /dev/null
    if [[ -f "/boot/config-${kver}" ]]; then
        cp "/boot/config-${kver}" .config
        scripts/config -d CONFIG_SYSTEM_TRUSTED_KEYS || true
        scripts/config -d CONFIG_SYSTEM_REVOCATION_KEYS || true
        make olddefconfig 2>&1 | tail -1
        info "Applied /boot/config-${kver} to source tree"
    fi

    info "Compiling kernel (this will take a while)..."
    /usr/bin/time -v make -j"$(nproc)" 2>&1 | tail -5
    chmod +x ./debian/scripts/sign-module 2>/dev/null || true
    make modules_install -j"$(nproc)" 2>&1 | tail -3
    make install 2>&1 | tail -3
    popd > /dev/null

    if [[ -n "${SUDO_USER:-}" ]]; then
        chown -R "$SUDO_USER:$SUDO_USER" "$kernel_dir"
    fi

    echo -e "  ${GREEN}✓${RST} Kernel source installed at ${BOLD}$kernel_dir${RST}"
    echo -e "  Use: ${BOLD}export KERNEL_DIR=$kernel_dir${RST}"
}

# ── Run selected steps ───────────────────────────────────────────────
echo -e "${BOLD}KernelX Dependency Installer${RST}"
echo "=============================="
echo

$DO_APT        && install_apt          && echo
$DO_PAHOLE     && install_pahole_source && echo
$DO_LIBBPF     && install_libbpf       && echo
$DO_VMLINUX    && generate_vmlinux     && echo
$DO_PYTEST     && install_pytest       && echo
$DO_KERNEL_SRC && install_kernel_source && echo

echo -e "${GREEN}Done.${RST} Run ${BOLD}./xkernel-tool doctor${RST} to verify."
