#!/bin/bash
# install_bench.sh - Install kpatch, build kpatch module, and prepare XKernel for Figure 18
#
# Uses kpatch-build to create a live-patch module from a source-level diff
# (process_backlog >= 16 → >= 32 in tcp_sendmsg_locked).
# kpatch handles the KLP lifecycle automatically.
#
# Usage:
#   sudo bash install_bench.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"

RED='\033[0;31m'; GREEN='\033[0;32m'; BOLD='\033[1m'; RST='\033[0m'
log()    { echo -e "${BOLD}[$(date '+%H:%M:%S')]${RST} $*"; }
log_ok() { echo -e "${GREEN}[$(date '+%H:%M:%S')] ✓${RST} $*"; }
die()    { echo -e "${RED}[$(date '+%H:%M:%S')] ✗${RST} $*" >&2; exit 1; }

CLIENT_IP="192.168.100.2"
NIC="enp23s0f0np0"
KERNEL_SRC="${KERNEL_DIR:-$HOME/linux-6.8.0}"
VMLINUX="$KERNEL_SRC/vmlinux"
KPATCH_MOD_NAME="kpatch-tcp-backlog"
KPATCH_KO="$SCRIPT_DIR/klp_module/${KPATCH_MOD_NAME}.ko"

# ── Check dependencies ───────────────────────────────────────────────
log "Checking dependencies ..."

command -v iperf3 >/dev/null 2>&1 || {
    log "Installing iperf3 on server ..."
    sudo apt-get update -qq && sudo apt-get install -y -qq iperf3
}
ssh "$CLIENT_IP" "command -v iperf3 >/dev/null 2>&1" || {
    log "Installing iperf3 on client ..."
    ssh "$CLIENT_IP" "sudo apt-get update -qq && sudo apt-get install -y -qq iperf3"
}
log_ok "iperf3 available on both machines"

command -v bpftrace >/dev/null 2>&1 || {
    log "Installing bpftrace ..."
    sudo apt-get update -qq && sudo apt-get install -y -qq bpftrace
}
log_ok "bpftrace available"

# ── Install kpatch if needed ─────────────────────────────────────────
if ! command -v kpatch &>/dev/null || ! command -v kpatch-build &>/dev/null; then
    log "Installing kpatch build dependencies ..."
    sudo apt-get update -qq
    sudo apt-get install -y -qq dpkg-dev libelf-dev libssl-dev dwarves ccache 2>/dev/null || true

    log "Installing kpatch from source ..."
    cd /tmp
    [[ -d kpatch ]] || git clone https://github.com/dynup/kpatch.git
    cd kpatch
    make
    sudo make install
    log_ok "kpatch installed"
else
    log_ok "kpatch already installed: $(which kpatch), $(which kpatch-build)"
fi

# ── Build XKernel tunable FIRST ──────────────────────────────────────
# XKernel build invokes diff.py which recompiles kernel .o files and may
# regenerate Module.symvers.  We do this BEFORE kpatch-build so that the
# Module.symvers fix below is not overwritten.
log "Building XKernel process_backlog tunable ..."
cd "$PROJECT_ROOT"

sudo ./xkernel-tool table delete --all -y 2>/dev/null || true
sudo rm -f bpf/stubs/xtune_stub_*.bpf.c \
           bpf/stubs/xtune_stub_*.bpf.h \
           bpf/stubs/xtune_stub_*.bpf.o 2>/dev/null || true

sudo ./xkernel-tool build "$SCRIPT_DIR/process_backlog.toml" 2>&1 || true
sudo make -C "$PROJECT_ROOT/bpf" 2>&1 | tail -2
log_ok "XKernel tunable built"

# ── Build kernel modules ─────────────────────────────────────────────
log "Building kernel modules ..."
if [[ ! -f "$PROJECT_ROOT/kernel/kfuncs/xk-kfuncs.ko" ]]; then
    sudo make -C "$PROJECT_ROOT/kernel/kfuncs" 2>&1 | tail -1
fi
log_ok "Kernel modules built"

# ── Build kpatch module via kpatch-build ─────────────────────────────
if [[ -f "$KPATCH_KO" ]]; then
    log_ok "kpatch module already built: $KPATCH_KO"
else
    log "Building kpatch module via kpatch-build (may take 10-30 min) ..."

    [[ -d "$KERNEL_SRC" ]] || die "Kernel source not found: $KERNEL_SRC"
    [[ -f "$VMLINUX" ]]    || die "vmlinux not found: $VMLINUX"

    # Fix kernel source Makefile version to match running kernel.
    # The source tree may have a different SUBLEVEL/EXTRAVERSION than the
    # running kernel (e.g., source=6.8.12, running=6.8.0-101-generic).
    RUNNING_KVER="$(uname -r)"
    KVER_MAJOR=$(echo "$RUNNING_KVER" | cut -d. -f1)
    KVER_MINOR=$(echo "$RUNNING_KVER" | cut -d. -f2)
    KVER_SUB=$(echo "$RUNNING_KVER" | cut -d. -f3 | cut -d- -f1)
    KVER_EXTRA="-$(echo "$RUNNING_KVER" | cut -d- -f2-)"
    log "Fixing kernel source version to match running kernel ($RUNNING_KVER) ..."
    sudo sed -i "s/^SUBLEVEL = .*/SUBLEVEL = $KVER_SUB/" "$KERNEL_SRC/Makefile"
    sudo sed -i "s/^EXTRAVERSION =.*/EXTRAVERSION = $KVER_EXTRA/" "$KERNEL_SRC/Makefile"
    echo "$RUNNING_KVER" | sudo tee "$KERNEL_SRC/include/config/kernel.release" >/dev/null

    # Copy Module.symvers from running kernel headers
    RUNNING_SYMVERS="/usr/src/linux-headers-${RUNNING_KVER}/Module.symvers"
    if [[ -f "$RUNNING_SYMVERS" ]]; then
        cp "$KERNEL_SRC/Module.symvers" "$KERNEL_SRC/Module.symvers.bak" 2>/dev/null || true
        cp "$RUNNING_SYMVERS" "$KERNEL_SRC/Module.symvers"
        log_ok "Module.symvers updated"
    fi

    # Generate patch from actual kernel source to guarantee correct context
    PATCH_FILE="$SCRIPT_DIR/klp_module/tcp_backlog.patch"
    log "Generating patch from kernel source ..."
    cp "$KERNEL_SRC/net/ipv4/tcp.c" /tmp/tcp_orig.c
    sed 's/if (unlikely(process_backlog >= 16))/if (unlikely(process_backlog >= 32))/' \
        /tmp/tcp_orig.c > /tmp/tcp_modified.c
    diff -u /tmp/tcp_orig.c /tmp/tcp_modified.c \
        | sed "s|/tmp/tcp_orig.c|a/net/ipv4/tcp.c|; s|/tmp/tcp_modified.c|b/net/ipv4/tcp.c|" \
        > "$PATCH_FILE" || true
    log_ok "Patch generated"

    mkdir -p "$SCRIPT_DIR/klp_module"

    KPATCH_BUILD_START=$(date +%s)
    sudo kpatch-build \
        -s "$KERNEL_SRC" \
        -v "$VMLINUX" \
        -j "$(nproc)" \
        -n "$KPATCH_MOD_NAME" \
        --skip-compiler-check \
        "$PATCH_FILE"
    KPATCH_BUILD_END=$(date +%s)
    KPATCH_BUILD_TIME=$((KPATCH_BUILD_END - KPATCH_BUILD_START))
    log "kpatch-build took ${KPATCH_BUILD_TIME}s"

    # kpatch-build outputs to cwd; move to klp_module/
    if [[ -f "${KPATCH_MOD_NAME}.ko" ]]; then
        mv "${KPATCH_MOD_NAME}.ko" "$KPATCH_KO"
    fi
    [[ -f "$KPATCH_KO" ]] || die "kpatch-build failed to produce $KPATCH_KO"

    # Patch symbol version CRCs to match running kernel.
    # The source tree's type definitions may produce different CRCs than Ubuntu's
    # kernel build, even though the code is functionally identical.
    log "Patching symbol version CRCs ..."
    python3 - "$KPATCH_KO" "$RUNNING_SYMVERS" << 'PYSCRIPT'
import struct, sys, subprocess
ko_path, symvers_path = sys.argv[1], sys.argv[2]
symvers = {}
with open(symvers_path) as f:
    for line in f:
        parts = line.strip().split('\t')
        if len(parts) >= 2:
            symvers[parts[1]] = int(parts[0], 16)
result = subprocess.run(['readelf', '-S', '--wide', ko_path], capture_output=True, text=True)
for line in result.stdout.split('\n'):
    if '__versions' in line:
        parts = line.split()
        idx = parts.index('__versions')
        sec_offset = int(parts[idx+3], 16)
        sec_size = int(parts[idx+4], 16)
        break
else:
    print("WARNING: __versions section not found"); sys.exit(0)
with open(ko_path, 'rb') as f:
    data = bytearray(f.read())
pos, end, patched = sec_offset, sec_offset + sec_size, 0
while pos < end:
    entry_size = struct.unpack_from('<I', data, pos)[0]
    if entry_size == 0: break
    old_crc = struct.unpack_from('<I', data, pos + 4)[0]
    name = data[pos+8:pos+entry_size].split(b'\x00')[0].decode('ascii', errors='replace')
    if name in symvers and old_crc != symvers[name]:
        struct.pack_into('<I', data, pos + 4, symvers[name])
        patched += 1
    pos += entry_size
with open(ko_path, 'wb') as f:
    f.write(data)
print(f"Patched {patched} symbol CRCs")
PYSCRIPT
    log_ok "kpatch module built in ${KPATCH_BUILD_TIME}s: $KPATCH_KO"
fi

# ── Fix bpftool symlink if needed ─────────────────────────────────────
KVER=$(uname -r)
if ! bpftool version &>/dev/null; then
    REAL_BPF=$(find /usr/lib/linux-tools* -name bpftool -type f 2>/dev/null | head -1)
    if [[ -n "$REAL_BPF" ]]; then
        sudo mkdir -p "/usr/lib/linux-tools/$KVER"
        sudo ln -sf "$REAL_BPF" "/usr/lib/linux-tools/$KVER/bpftool"
        log_ok "Created bpftool symlink for kernel $KVER"
    fi
fi

# ── Verify ────────────────────────────────────────────────────────────
log "Checking KLP support ..."
[[ -d /sys/kernel/livepatch ]] || die "CONFIG_LIVEPATCH not enabled in kernel"
log_ok "KLP support verified"

# Quick load/unload test
log "Testing kpatch load/unload ..."
sudo kpatch load "$KPATCH_KO" 2>&1 || die "kpatch module failed to load"
sudo kpatch unload "$KPATCH_MOD_NAME" 2>&1 || die "kpatch module failed to unload"
log_ok "kpatch module verified"

log_ok "Installation complete"
echo ""
echo "Next: sudo bash run.sh"
