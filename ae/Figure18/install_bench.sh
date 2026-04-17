#!/bin/bash
# install_bench.sh - Install kpatch and build KLP module for Figure 18
#
# Builds the kpatch module for tcp_sendmsg_locked (process_backlog >= 16 -> >= 32)
# and the XKernel tunable for the same constant.
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

CLIENT_IP="192.168.6.2"
KERNEL_SRC="$HOME/linux-6.8.0"
VMLINUX="$KERNEL_SRC/vmlinux"
KLP_KO="$SCRIPT_DIR/klp_module/kpatch-tcp-backlog.ko"

# -- Check dependencies ---
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

# -- Install kpatch if needed ---
if ! command -v kpatch-build &>/dev/null; then
    log "Installing kpatch from source ..."
    cd /tmp
    [[ -d kpatch ]] || git clone https://github.com/dynup/kpatch.git
    cd kpatch
    make
    sudo make install
    log_ok "kpatch installed"
else
    log_ok "kpatch already installed: $(which kpatch-build)"
fi

# -- Build kpatch module (if not already built) ---
if [[ -f "$KLP_KO" ]]; then
    log_ok "kpatch module already built: $KLP_KO"
else
    log "Building kpatch module (takes ~30 min) ..."

    [[ -d "$KERNEL_SRC" ]] || die "Kernel source not found: $KERNEL_SRC"
    [[ -f "$VMLINUX" ]]    || die "vmlinux not found: $VMLINUX"

    # Create patch: process_backlog >= 16 -> >= 32 in tcp_sendmsg_locked
    PATCH_FILE="$SCRIPT_DIR/klp_module/tcp_backlog.patch"
    cat > "$PATCH_FILE" << 'PATCH'
--- a/net/ipv4/tcp.c
+++ b/net/ipv4/tcp.c
@@ -1145,7 +1145,7 @@ restart:
 
 copy = min_t(int, copy, pfrag->size - pfrag->offset);
 
-if (process_backlog >= 16)
+if (process_backlog >= 32)
 process_backlog = 0;
 
 if (!sk_wmem_schedule(sk, copy))
PATCH

    mkdir -p "$SCRIPT_DIR/klp_module"
    sudo kpatch-build \
        -s "$KERNEL_SRC" \
        -v "$VMLINUX" \
        -j "$(nproc)" \
        -n kpatch-tcp-backlog \
        -o "$SCRIPT_DIR/klp_module" \
        --skip-compiler-check \
        "$PATCH_FILE"

    [[ -f "$KLP_KO" ]] || die "kpatch-build failed to produce $KLP_KO"
    log_ok "kpatch module built: $KLP_KO"
fi

# -- Build XKernel tunable ---
log "Building XKernel process_backlog tunable ..."
cd "$PROJECT_ROOT"

sudo ./xkernel-tool table delete --all -y 2>/dev/null || true
rm -f bpf/stubs/xtune_stub_*.bpf.c bpf/stubs/xtune_stub_*.bpf.h 2>/dev/null || true

./xkernel-tool build "$SCRIPT_DIR/process_backlog.toml"
log_ok "XKernel tunable built"

# -- Build kernel modules ---
log "Building kernel modules ..."
sudo make -C "$PROJECT_ROOT/kernel/kfuncs" clean 2>/dev/null || true
sudo make -C "$PROJECT_ROOT/kernel/kfuncs"
cd "$PROJECT_ROOT/kernel/consistency" && sudo make clean 2>/dev/null || true && sudo make
log_ok "Kernel modules built"

# -- Fix bpftool symlink if needed ---
KVER=$(uname -r)
if ! bpftool version &>/dev/null; then
    REAL_BPF=$(find /usr/lib/linux-tools* -name bpftool -type f 2>/dev/null | head -1)
    if [[ -n "$REAL_BPF" ]]; then
        sudo mkdir -p "/usr/lib/linux-tools/$KVER"
        sudo ln -sf "$REAL_BPF" "/usr/lib/linux-tools/$KVER/bpftool"
        log_ok "Created bpftool symlink for kernel $KVER"
    fi
fi

# -- Verify ---
log "Checking KLP support ..."
[[ -d /sys/kernel/livepatch ]] || die "CONFIG_LIVEPATCH not enabled in kernel"
log_ok "KLP support verified"

log_ok "Installation complete"
echo ""
echo "Next: sudo bash run.sh"
