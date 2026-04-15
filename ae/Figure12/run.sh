#!/usr/bin/env bash
# run.sh — Reproduce Figure 12: NGINX FCT under different TCP CUBIC scaling factors
#
# This experiment measures tail latency (FCT) of NGINX serving heavy-tailed
# content under different network RTTs, comparing:
#   - Vanilla kernel (SF=3, default tcp_cubic scaling factor)
#   - KernelX adaptive policy (SF=1 for high-RTT flows, SF=3 for low-RTT)
#
# Setup:
#   - Server: 192.168.6.1 (runs NGINX + KernelX, this script)
#   - Client: 192.168.6.2 (runs wrk2)
#   - NIC: ens1f1np1 (netem for RTT simulation)
#
# Usage:
#   sudo bash run.sh [--duration SECS] [--rate RPS] [--threads N] [--connections N]
#
# Prerequisites:
#   - Server: bash install_nginx.sh server  (NGINX + workload files)
#   - Client: bash install_nginx.sh client  (wrk2 + Lua script)
#   - Server: sudo bash build.sh            (build KernelX)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
XKTOOL="$PROJECT_ROOT/xkernel-tool"
TUNE_SCRIPT="$SCRIPT_DIR/tune_tcp_cubic.sh"

# ── Configuration ────────────────────────────────────────────────────
SERVER_IP="192.168.6.1"
CLIENT_IP="192.168.6.2"
NIC="ens1f1np1"

# wrk2 parameters
DURATION=60             # seconds per run
RATE=1000               # target requests/sec
THREADS=4               # wrk2 threads
CONNECTIONS=200         # wrk2 connections

# RTT values to test (netem delay applied on server NIC, one-way;
# TCP effectively sees this as the RTT since return path is ~0ms)
RTTS=(20 80)

# Parse command line
while [[ $# -gt 0 ]]; do
    case "$1" in
        --duration)    DURATION="$2";    shift 2 ;;
        --rate)        RATE="$2";        shift 2 ;;
        --threads)     THREADS="$2";     shift 2 ;;
        --connections) CONNECTIONS="$2"; shift 2 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

RESULT_DIR="$SCRIPT_DIR/results"

RED='\033[0;31m'; GREEN='\033[0;32m'; BOLD='\033[1m'; RST='\033[0m'
log()         { echo -e "${BOLD}[$(date '+%H:%M:%S')]${RST} $*"; }
log_ok()      { echo -e "${GREEN}[$(date '+%H:%M:%S')] ✓${RST} $*"; }
log_section() { echo -e "\n${BOLD}════════════════════════════════════════${RST}"; log "$*"; echo -e "${BOLD}════════════════════════════════════════${RST}"; }
die()         { echo -e "${RED}[$(date '+%H:%M:%S')] ✗${RST} $*" >&2; exit 1; }

# ── Preflight checks ────────────────────────────────────────────────
log_section "Preflight checks"

[[ -x "$XKTOOL" ]]    || die "xkernel-tool not found at $XKTOOL"
command -v tc &>/dev/null || die "tc (iproute2) not found"
systemctl is-active nginx &>/dev/null || die "NGINX not running. Run: bash install_nginx.sh server"

# Check wrk2 on client
ssh "$CLIENT_IP" "which wrk2 >/dev/null 2>&1" || \
    die "wrk2 not found on client $CLIENT_IP. Run: bash install_nginx.sh client"

# Check Lua script on client
LUA_SCRIPT="$SCRIPT_DIR/lua/zipf.lua"
[[ -f "$LUA_SCRIPT" ]] || die "Lua script not found: $LUA_SCRIPT"

mkdir -p "$RESULT_DIR"

log_ok "Server: NGINX running on $SERVER_IP"
log_ok "Client: wrk2 available on $CLIENT_IP"
log_ok "NIC: $NIC"
log_ok "Duration: ${DURATION}s, Rate: ${RATE} req/s, Threads: $THREADS, Conns: $CONNECTIONS"

# ── Save experiment metadata ─────────────────────────────────────────
{
    echo "date:        $(date)"
    echo "kernel:      $(uname -r)"
    echo "git branch:  $(cd "$PROJECT_ROOT" && git rev-parse --abbrev-ref HEAD 2>/dev/null || echo 'unknown')"
    echo "git commit:  $(cd "$PROJECT_ROOT" && git rev-parse HEAD 2>/dev/null || echo 'unknown')"
    echo ""
    echo "=== parameters ==="
    echo "SERVER_IP=$SERVER_IP"
    echo "CLIENT_IP=$CLIENT_IP"
    echo "NIC=$NIC"
    echo "DURATION=$DURATION"
    echo "RATE=$RATE"
    echo "THREADS=$THREADS"
    echo "CONNECTIONS=$CONNECTIONS"
    echo "RTTS=${RTTS[*]}"
} > "$RESULT_DIR/log.txt"

# ── Helper: configure netem delay ────────────────────────────────────
set_delay() {
    local rtt_ms="$1"
    # netem on server NIC: one-way delay = rtt_ms/2.
    # TCP sees effective RTT ≈ rtt_ms (since return path is ~0ms for same-rack).
    # Using rtt_ms/2 as the netem delay gives a reasonable approximation.
    local delay_ms=$(( rtt_ms / 2 ))

    # Clear existing qdisc
    sudo tc qdisc del dev "$NIC" root 2>/dev/null || true

    if [[ "$rtt_ms" -gt 0 ]]; then
        sudo tc qdisc add dev "$NIC" root netem delay "${delay_ms}ms"
        log "netem: ${delay_ms}ms delay on $NIC (target RTT ≈ ${rtt_ms}ms)"
    else
        log "netem: cleared on $NIC"
    fi
}

clear_delay() {
    sudo tc qdisc del dev "$NIC" root 2>/dev/null || true
    log "netem: cleared on $NIC"
}

# ── Helper: copy Lua script to client and run wrk2 ──────────────────
run_wrk2() {
    local rtt_ms="$1"
    local label="$2"
    local outfile="$RESULT_DIR/${label}_${rtt_ms}ms.txt"

    log "Running wrk2 on client (RTT=${rtt_ms}ms, label=${label}) → $outfile"

    # Copy Lua script to client
    scp -q "$LUA_SCRIPT" "${CLIENT_IP}:/tmp/zipf.lua"

    # Run wrk2 on client and collect histogram output
    # wrk2 --latency outputs HdrHistogram-compatible percentile data
    # The Lua script (zipf.lua) generates request paths, so the base URL
    # just needs to point to the server (any valid path works as a placeholder)
    ssh "$CLIENT_IP" bash -c "'
        wrk2 -t$THREADS -c$CONNECTIONS -d${DURATION}s -R$RATE \
            --latency -s /tmp/zipf.lua \
            http://${SERVER_IP}/ 2>&1
    '" > "${outfile}.raw"

    # Extract the latency histogram section (HdrHistogram percentile format)
    # wrk2 outputs "Detailed Percentile spectrum:" followed by:
    #   Value   Percentile   TotalCount   1/(1-Percentile)
    # We also keep the header line for compatibility with the plot script
    {
        echo "       Value   Percentile   TotalCount 1/(1-Percentile)"
        echo ""
        awk '
            /Detailed Percentile spectrum:/ { found=1; next }
            /^[[:space:]]*Value/ && found { next }
            /^#/ && found { exit }
            /^--/ && found { exit }
            found && /^[[:space:]]*[0-9]/ { print }
        ' "${outfile}.raw"
    } > "$outfile"

    # If no histogram data extracted, use the raw wrk2 output
    if [[ $(wc -l < "$outfile") -le 2 ]]; then
        mv "${outfile}.raw" "$outfile"
        log "  WARNING: Could not extract histogram; using raw output"
    else
        rm -f "${outfile}.raw"
    fi

    local lines
    lines=$(wc -l < "$outfile")
    log_ok "  Collected $lines data points → $(basename "$outfile")"
}

# ── Phase 1: Vanilla kernel (SF=3 default) ───────────────────────────
log_section "Phase 1: Vanilla kernel (SF=3, default tcp_cubic)"

# Make sure no KernelX tunables are loaded
sudo bash "$TUNE_SCRIPT" unload 2>/dev/null || true

for rtt in "${RTTS[@]}"; do
    log_section "Vanilla: RTT = ${rtt}ms"
    set_delay "$rtt"
    sleep 2  # let netem stabilize

    run_wrk2 "$rtt" "vanilla"

    clear_delay
    sleep 2
done

# ── Phase 2: Build tcp_cubic tunable (one-time) ──────────────────────
log_section "Building tcp_cubic tunable (one-time)"
sudo bash "$TUNE_SCRIPT" build

# ── Phase 3: KernelX adaptive policy ─────────────────────────────────
log_section "Phase 2: KernelX adaptive SF (SF=1 for high-RTT flows)"

# Load adaptive X-tune policy
sudo bash "$TUNE_SCRIPT" adaptive

for rtt in "${RTTS[@]}"; do
    log_section "KernelX Adaptive: RTT = ${rtt}ms"
    set_delay "$rtt"
    sleep 2

    run_wrk2 "$rtt" "xkernel"

    clear_delay
    sleep 2
done

# Unload after all adaptive runs
sudo bash "$TUNE_SCRIPT" unload 2>/dev/null || true

# ── Cleanup ──────────────────────────────────────────────────────────
log_section "Cleanup"

clear_delay
sudo "$XKTOOL" table delete --all -y 2>/dev/null || true
rm -rf "$PROJECT_ROOT/bpf/stubs/"* 2>/dev/null || true

# ── Summary ──────────────────────────────────────────────────────────
log_ok "Figure 12 experiment complete."
log "Results in: $RESULT_DIR/"
ls -la "$RESULT_DIR/"
echo ""
log "Data files:"
for f in "$RESULT_DIR"/*.txt; do
    [[ -f "$f" ]] && echo "  $(basename "$f"): $(wc -l < "$f") lines"
done
echo ""
log "Next steps:"
log "  python plot/plot.py       # → plot/figure12.pdf"
