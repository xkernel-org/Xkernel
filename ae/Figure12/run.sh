#!/usr/bin/env bash
# run.sh — Reproduce Figure 12: NGINX FCT under different TCP CUBIC HyStart parameters
#
# This experiment measures tail latency (FCT) of NGINX serving heavy-tailed
# content under different network RTTs, comparing:
#   - Vanilla kernel (SF=3, HYSTART_DELAY_MAX=16ms — default tcp_cubic)
#   - KernelX tuned  (SF=1, HYSTART_DELAY_MAX=32ms — relaxed HyStart detection)
#
# KernelX tunes two perf-consts in tcp_cubic's HyStart delay detection:
#   ConstID 1 (tcp_cubic):       delay_min >> SF   (SF: 3→1, wider threshold)
#   ConstID 2 (hystart_delay_max): clamp upper bound (16ms→32ms)
#
# Setup:
#   - Server: 192.168.6.1 (runs NGINX + KernelX, this script)
#   - Client: 192.168.6.2 (runs wrk2)
#   - NIC: ens1f1np1 (netem for RTT simulation + rate limiting)
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
RATE=800                # target requests/sec
THREADS=4               # wrk2 threads
CONNECTIONS=200         # wrk2 connections
TIMEOUT=120             # request timeout in seconds

# Network shaping: netem delay + rate limit
RATE_LIMIT="2gbit"      # bottleneck bandwidth (netem rate on server)
NETEM_LIMIT=100000      # netem queue limit (server)
CLIENT_NETEM_LIMIT=1000000  # netem queue limit (client)

# RTT values to test (symmetric: half RTT delay on each side)
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
log_ok "NIC: $NIC (rate limit: $RATE_LIMIT)"
log_ok "Duration: ${DURATION}s, Rate: ${RATE} req/s, Threads: $THREADS, Conns: $CONNECTIONS"

# ── Sysctl tuning ───────────────────────────────────────────────────
log "Disabling TCP metrics cache (tcp_no_metrics_save=1) ..."
sudo sysctl -w net.ipv4.tcp_no_metrics_save=1 -q

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
    echo "RATE_LIMIT=$RATE_LIMIT"
    echo "NETEM_LIMIT=$NETEM_LIMIT"
    echo "CLIENT_NETEM_LIMIT=$CLIENT_NETEM_LIMIT"
    echo "TIMEOUT=$TIMEOUT"
} > "$RESULT_DIR/log.txt"

# ── Helper: configure netem delay (symmetric: both server and client) ─
set_delay() {
    local rtt_ms="$1"
    local half_rtt=$(( rtt_ms / 2 ))

    # Clear existing qdiscs on both sides
    sudo tc qdisc del dev "$NIC" root 2>/dev/null || true
    ssh "$CLIENT_IP" "sudo tc qdisc del dev $NIC root 2>/dev/null" || true

    if [[ "$rtt_ms" -gt 0 ]]; then
        # Server: netem delay (half RTT) + rate limit (bandwidth bottleneck)
        sudo tc qdisc add dev "$NIC" root netem \
            delay "${half_rtt}ms" rate "$RATE_LIMIT" limit "$NETEM_LIMIT"
        # Client: netem delay only (half RTT, no rate limit)
        ssh "$CLIENT_IP" "sudo tc qdisc add dev $NIC root netem \
            delay ${half_rtt}ms limit $CLIENT_NETEM_LIMIT"
        log "netem: ${half_rtt}ms delay each side (RTT=${rtt_ms}ms), server rate $RATE_LIMIT"
    else
        log "netem: cleared on both sides"
    fi
}

clear_delay() {
    sudo tc qdisc del dev "$NIC" root 2>/dev/null || true
    ssh "$CLIENT_IP" "sudo tc qdisc del dev $NIC root 2>/dev/null" || true
    log "netem: cleared on both sides"
}

# ── Helper: copy Lua script to client and run wrk2 ──────────────────
run_wrk2() {
    local rtt_ms="$1"
    local label="$2"
    local outfile="$RESULT_DIR/${label}_${rtt_ms}ms.txt"

    log "Running wrk2 on client (RTT=${rtt_ms}ms, label=${label}) → $outfile"

    # Copy Lua script to client
    scp -q "$LUA_SCRIPT" "${CLIENT_IP}:/tmp/zipf.lua"

    # Run wrk2 directly via SSH (blocking).
    # wrk2 --latency outputs HdrHistogram-compatible percentile data.
    ssh "$CLIENT_IP" "wrk2 -t$THREADS -c$CONNECTIONS -d${DURATION}s -R$RATE \
        --timeout ${TIMEOUT}s --latency -s /tmp/zipf.lua \
        http://${SERVER_IP}/" > "$outfile" 2>&1

    local lines
    lines=$(wc -l < "$outfile")
    log_ok "  Collected $lines lines → $(basename "$outfile")"
}

# ── Phase 1: Vanilla kernel (default tcp_cubic) ─────────────────────
log_section "Phase 1: Vanilla kernel (SF=3, HYSTART_DELAY_MAX=16ms)"

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

# ── Phase 2: KernelX tuned HyStart ──────────────────────────────────
log_section "Phase 2: KernelX tuned (SF=1, HYSTART_DELAY_MAX=32ms)"

# Build tunables (one-time) and load both ConstIDs
sudo bash "$TUNE_SCRIPT" build
sudo bash "$TUNE_SCRIPT" load

for rtt in "${RTTS[@]}"; do
    log_section "KernelX: RTT = ${rtt}ms"
    set_delay "$rtt"
    sleep 2

    run_wrk2 "$rtt" "xkernel"

    clear_delay
    sleep 2
done

# Unload after all runs
sudo bash "$TUNE_SCRIPT" unload

# ── Cleanup ──────────────────────────────────────────────────────────
log_section "Cleanup"

clear_delay

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
log "  python3 plot/plot.py       # → plot/figure12.pdf"
