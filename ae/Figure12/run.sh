#!/usr/bin/env bash
# run.sh — Reproduce Figure 12: NGINX FCT under different TCP CUBIC HyStart parameters
#
# This experiment measures tail latency (FCT) of NGINX serving heavy-tailed
# content under different network RTTs, comparing:
#   - Vanilla kernel (SF=3, HYSTART_DELAY_MAX=16ms — default tcp_cubic)
#   - KernelX tuned  (SF=1 for RTT>=80ms, HYSTART_DELAY_MAX=32ms)
#
# KernelX tunes two perf-consts in tcp_cubic's HyStart delay detection:
#   ConstID 1 (tcp_cubic):       delay_min >> SF   (SF: 3→1 when curr_rtt>=80ms)
#   ConstID 2 (hystart_delay_max): clamp upper bound (16ms→32ms)
#
# Setup:
#   - Server: 192.168.6.1 (runs NGINX on ports 80 + 8080, KernelX, this script)
#   - Client: 192.168.6.2 (runs two wrk2 instances simultaneously)
#   - NIC: ens1f1np1
#   - Port 80  → 20ms RTT (netem delay 10ms each side)
#   - Port 8080 → 80ms RTT (netem delay 40ms each side)
#
# Usage:
#   bash run.sh [--duration SECS] [--rate RPS] [--threads N] [--connections N]
#
# Prerequisites:
#   - Server: bash install_nginx.sh  (NGINX + workload files + wrk2 on client)
#   - Server: sudo bash build.sh     (build KernelX)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
XKTOOL="$PROJECT_ROOT/xkernel-tool"
TUNE_SCRIPT="$SCRIPT_DIR/tune_tcp_cubic.sh"

# ── Configuration ────────────────────────────────────────────────────
SERVER_IP="192.168.6.1"
CLIENT_IP="192.168.6.2"
NIC="ens1f1np1"

# Server ports: port 80 → 20ms RTT, port 8080 → 80ms RTT
PORT_20MS=80
PORT_80MS=8080

# wrk2 parameters (per port)
DURATION=60             # seconds per run
RATE=800                # target requests/sec per port
THREADS=4               # wrk2 threads per port
CONNECTIONS=200         # wrk2 connections per port
TIMEOUT=120             # request timeout in seconds

# Network shaping
RATE_LIMIT="1gbit"      # bottleneck bandwidth per port (netem rate on server)
NETEM_LIMIT=100000      # netem queue limit (server)
CLIENT_NETEM_LIMIT=1000000  # netem queue limit (client)

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
systemctl is-active nginx &>/dev/null || die "NGINX not running. Run: bash install_nginx.sh"

# Check wrk2 on client
ssh "$CLIENT_IP" "test -x /usr/local/bin/wrk2" || \
    die "wrk2 not found on client $CLIENT_IP. Run: bash install_nginx.sh"

# Check Lua script on client
LUA_SCRIPT="$SCRIPT_DIR/lua/zipf.lua"
[[ -f "$LUA_SCRIPT" ]] || die "Lua script not found: $LUA_SCRIPT"

mkdir -p "$RESULT_DIR"

log_ok "Server: NGINX running on $SERVER_IP (ports $PORT_20MS, $PORT_80MS)"
log_ok "Client: wrk2 available on $CLIENT_IP"
log_ok "NIC: $NIC (rate limit: $RATE_LIMIT per port)"
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
    echo "PORT_20MS=$PORT_20MS"
    echo "PORT_80MS=$PORT_80MS"
    echo "DURATION=$DURATION"
    echo "RATE=$RATE"
    echo "THREADS=$THREADS"
    echo "CONNECTIONS=$CONNECTIONS"
    echo "RATE_LIMIT=$RATE_LIMIT"
    echo "NETEM_LIMIT=$NETEM_LIMIT"
    echo "CLIENT_NETEM_LIMIT=$CLIENT_NETEM_LIMIT"
    echo "TIMEOUT=$TIMEOUT"
} > "$RESULT_DIR/log.txt"

# ── Helper: configure per-port netem ─────────────────────────────────
# Port 80 → 20ms RTT (10ms each side), Port 8080 → 80ms RTT (40ms each side)
# Uses prio qdisc with tc filters to steer traffic by port.
set_dual_delay() {
    # Server: classify by source port (server sends FROM port 80/8080)
    sudo tc qdisc del dev "$NIC" root 2>/dev/null || true
    sudo tc qdisc add dev "$NIC" root handle 1: prio bands 3 \
        priomap 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2
    sudo tc qdisc add dev "$NIC" parent 1:1 handle 10: netem \
        delay 10ms rate "$RATE_LIMIT" limit "$NETEM_LIMIT"
    sudo tc qdisc add dev "$NIC" parent 1:2 handle 20: netem \
        delay 40ms rate "$RATE_LIMIT" limit "$NETEM_LIMIT"
    sudo tc filter add dev "$NIC" protocol ip parent 1:0 prio 1 \
        u32 match ip sport "$PORT_20MS" 0xffff flowid 1:1
    sudo tc filter add dev "$NIC" protocol ip parent 1:0 prio 1 \
        u32 match ip sport "$PORT_80MS" 0xffff flowid 1:2

    # Client: classify by dest port (client sends TO port 80/8080)
    ssh "$CLIENT_IP" "
    sudo tc qdisc del dev $NIC root 2>/dev/null
    sudo tc qdisc add dev $NIC root handle 1: prio bands 3 \
        priomap 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2 2
    sudo tc qdisc add dev $NIC parent 1:1 handle 10: netem \
        delay 10ms limit $CLIENT_NETEM_LIMIT
    sudo tc qdisc add dev $NIC parent 1:2 handle 20: netem \
        delay 40ms limit $CLIENT_NETEM_LIMIT
    sudo tc filter add dev $NIC protocol ip parent 1:0 prio 1 \
        u32 match ip dport $PORT_20MS 0xffff flowid 1:1
    sudo tc filter add dev $NIC protocol ip parent 1:0 prio 1 \
        u32 match ip dport $PORT_80MS 0xffff flowid 1:2
    "
    log "netem: port $PORT_20MS → 20ms RTT, port $PORT_80MS → 80ms RTT"
}

clear_delay() {
    sudo tc qdisc del dev "$NIC" root 2>/dev/null || true
    ssh "$CLIENT_IP" "sudo tc qdisc del dev $NIC root 2>/dev/null" || true
    log "netem: cleared on both sides"
}

# ── Helper: copy Lua script to client and run wrk2 on both ports ─────
run_dual_wrk2() {
    local label="$1"
    local outfile_20="$RESULT_DIR/${label}_20ms.txt"
    local outfile_80="$RESULT_DIR/${label}_80ms.txt"

    log "Running wrk2 on both ports simultaneously (label=${label})"

    # Copy Lua script to client
    scp -q "$LUA_SCRIPT" "${CLIENT_IP}:/tmp/zipf.lua"

    # Launch two wrk2 instances in parallel
    # -H "Connection: close" forces a new TCP connection per request,
    # ensuring every request goes through slow start where HyStart fires.
    ssh "$CLIENT_IP" "/usr/local/bin/wrk2 -t$THREADS -c$CONNECTIONS -d${DURATION}s -R$RATE \
        --timeout ${TIMEOUT}s --latency -H 'Connection: close' -s /tmp/zipf.lua \
        http://${SERVER_IP}:${PORT_20MS}/" > "$outfile_20" 2>&1 &
    local pid_20=$!

    ssh "$CLIENT_IP" "/usr/local/bin/wrk2 -t$THREADS -c$CONNECTIONS -d${DURATION}s -R$RATE \
        --timeout ${TIMEOUT}s --latency -H 'Connection: close' -s /tmp/zipf.lua \
        http://${SERVER_IP}:${PORT_80MS}/" > "$outfile_80" 2>&1 &
    local pid_80=$!

    wait $pid_20 $pid_80

    log_ok "  20ms → $(basename "$outfile_20") ($(wc -l < "$outfile_20") lines)"
    log_ok "  80ms → $(basename "$outfile_80") ($(wc -l < "$outfile_80") lines)"
}

# ── Phase 1: Vanilla kernel (default tcp_cubic) ─────────────────────
log_section "Phase 1: Vanilla kernel (SF=3, HYSTART_DELAY_MAX=16ms)"

# Make sure no KernelX tunables are loaded
sudo bash "$TUNE_SCRIPT" unload 2>/dev/null || true

set_dual_delay
sleep 2

run_dual_wrk2 "vanilla"

# ── Phase 2: KernelX tuned HyStart ──────────────────────────────────
log_section "Phase 2: KernelX tuned (SF=1 for RTT>=80ms, HYSTART_DELAY_MAX=32ms)"

# Build tunables (one-time) and load both ConstIDs
sudo bash "$TUNE_SCRIPT" build
sudo bash "$TUNE_SCRIPT" load

set_dual_delay
sleep 2

run_dual_wrk2 "xkernel"

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
