#!/usr/bin/env bash
# scripts/check_deps.sh — Verify KernelX prerequisites
set -uo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BOLD='\033[1m'
RST='\033[0m'

pass=0
warn=0
fail=0

ok()   { echo -e "  ${GREEN}✓${RST} $1"; ((pass++)); }
skip() { echo -e "  ${YELLOW}⚠${RST} $1"; ((warn++)); }
err()  { echo -e "  ${RED}✗${RST} $1"; ((fail++)); }

echo -e "${BOLD}KernelX Dependency Check${RST}"
echo "========================="
echo

# ── Python ──
echo -e "${BOLD}Python${RST}"
if command -v python3 &>/dev/null; then
    py_ver=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    py_maj=$(echo "$py_ver" | cut -d. -f1)
    py_min=$(echo "$py_ver" | cut -d. -f2)
    if [[ "$py_maj" -ge 3 && "$py_min" -ge 11 ]]; then
        ok "python3 $py_ver"
    else
        err "python3 $py_ver (need >= 3.11 for tomllib)"
    fi
else
    err "python3 not found"
fi

if python3 -c 'import tomllib' 2>/dev/null; then
    ok "tomllib (stdlib)"
else
    err "tomllib not available (Python 3.11+ required)"
fi

echo

# ── BPF Toolchain ──
echo -e "${BOLD}BPF Toolchain${RST}"
for cmd in clang llc; do
    if command -v "$cmd" &>/dev/null; then
        ver=$("$cmd" --version 2>&1 | head -1)
        ok "$cmd ($ver)"
    else
        err "$cmd not found (apt install clang llvm)"
    fi
done

bpftool_bin="${BPFTOOL:-}"
if [[ -z "$bpftool_bin" ]]; then
    bpftool_bin=$(ls /usr/lib/linux-tools/*/bpftool 2>/dev/null | tail -n 1 || true)
fi
if [[ -z "$bpftool_bin" ]]; then
    bpftool_bin=$(command -v bpftool 2>/dev/null || true)
fi
if [[ -n "$bpftool_bin" ]]; then
    ok "bpftool ($($bpftool_bin version 2>&1 | head -1))"
else
    err "bpftool not found (build from kernel source or apt install linux-tools-common)"
fi

if pkg-config --exists libbpf 2>/dev/null; then
    ok "libbpf ($(pkg-config --modversion libbpf))"
elif [[ -f /usr/local/lib/libbpf.so ]]; then
    ok "libbpf (found at /usr/local/lib/libbpf.so)"
else
    err "libbpf not found (build from github.com/libbpf/libbpf)"
fi

echo

# ── Build Tools ──
echo -e "${BOLD}Build Tools${RST}"
for cmd in make gcc pahole pkg-config; do
    if command -v "$cmd" &>/dev/null; then
        ok "$cmd"
    else
        err "$cmd not found"
    fi
done

if command -v pahole &>/dev/null; then
    pahole_ver=$(pahole --version 2>/dev/null | grep -oE '[0-9]+(\.[0-9]+)+' | head -1 || true)
    if [[ "$(uname -r)" == "6.14.8-061408-generic" ]]; then
        if [[ -n "$pahole_ver" && "$(printf '%s\n%s\n' "1.26" "$pahole_ver" | sort -V | head -1)" == "1.26" ]]; then
            ok "pahole $pahole_ver supports Linux 6.14 module BTF"
        else
            err "pahole ${pahole_ver:-unknown} too old for Linux 6.14 module BTF (need >= 1.26; run ./xkernel-tool setup --pahole)"
        fi
    fi
fi

if dpkg -s libelf-dev &>/dev/null 2>&1; then
    ok "libelf-dev"
else
    skip "libelf-dev not detected (may still be installed)"
fi

echo

# ── Kernel ──
echo -e "${BOLD}Kernel${RST}"
kver=$(uname -r)
echo -e "  Running kernel: ${BOLD}$kver${RST}"

if [[ "$kver" == *xkernel* ]]; then
    ok "Custom xkernel kernel detected"
else
    skip "Not running xkernel kernel (load/unload requires it)"
fi

# Check BTF support
if [[ -f /sys/kernel/btf/vmlinux ]]; then
    ok "BTF enabled (/sys/kernel/btf/vmlinux)"
else
    err "BTF not available (kernel must be built with CONFIG_DEBUG_INFO_BTF=y)"
fi

# Check vmlinux.h
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
if [[ -f "$PROJECT_ROOT/bpf/vmlinux.h" ]]; then
    ok "bpf/vmlinux.h exists"
else
    skip "bpf/vmlinux.h missing (run: bpftool btf dump file /sys/kernel/btf/vmlinux format c > bpf/vmlinux.h)"
fi

# Check kernel modules
echo
echo -e "${BOLD}Kernel Modules${RST}"
if [[ -f "$PROJECT_ROOT/kernel/kfuncs/xk-kfuncs.ko" ]]; then
    ok "xk-kfuncs.ko built"
else
    skip "xk-kfuncs.ko not built (cd kernel && ./build.sh)"
fi

if [[ -f "$PROJECT_ROOT/kernel/consistency/xk-consistency.ko" ]]; then
    ok "xk-consistency.ko built"
else
    skip "xk-consistency.ko not built (cd kernel && ./build.sh)"
fi

echo
echo "========================="
echo -e "  ${GREEN}$pass passed${RST}, ${YELLOW}$warn warnings${RST}, ${RED}$fail errors${RST}"
if [[ $fail -gt 0 ]]; then
    echo -e "  ${RED}Some required dependencies are missing.${RST}"
    exit 1
else
    echo -e "  ${GREEN}All required dependencies satisfied.${RST}"
    exit 0
fi
