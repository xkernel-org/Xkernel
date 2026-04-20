#!/bin/bash
# run.sh — Figure 9 experiment: vary MAX_SOFTIRQ_RESTART = {1,5,10,15,20}
#
# Measures cyclictest tail/avg latency and CPU utilization under heavy
# softirq load for each value of MAX_SOFTIRQ_RESTART.
#
# This script is self-contained: it starts iperf3 servers locally and
# launches iperf3 clients on the remote machine (192.168.6.2) via ssh.
#
# Usage: sudo bash run.sh [CPU] [REPS]

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
XKTOOL="$PROJECT_ROOT/xkernel-tool"
CPU=${1:-3}
REPS=${2:-2}                       # repetitions per value
VALUES=(1 5 10 15 20)
CYCLICTEST_LOOPS=100000            # ~100s per run
OUTFILE="results/figure9.csv"
CLIENT_IP="192.168.6.2"
IPERF_DURATION=6000

mkdir -p results

# ── idempotent cleanup: clear stale xkernel state and previous results ─
sudo "$XKTOOL" unload --all 2>/dev/null || true
sudo "$XKTOOL" table delete --all -y 2>/dev/null || true
sudo rmmod xk_kfuncs 2>/dev/null || true
sudo rm -rf "$PROJECT_ROOT/bpf/stubs/"* 2>/dev/null || true
rm -f results/figure9.csv results/lat_*.txt results/cpu_*.txt

# ── workload management ─────────────────────────────────────────────
start_workload() {
    echo "[*] Starting iperf3 servers locally and clients on $CLIENT_IP ..."

    # Kill any stale iperf3 on both sides
    pkill -9 iperf3 2>/dev/null || true
    ssh "$CLIENT_IP" "pkill -9 iperf3" 2>/dev/null || true
    sleep 1

    # Start iperf3 servers on local machine (receiver)
    for port in 5200 5201 5202; do
        iperf3 -s -p "$port" -D 2>/dev/null
    done
    sleep 1

    # Start iperf3 clients on remote machine (sender)
    ssh "$CLIENT_IP" "nohup iperf3 -c 192.168.6.1 -P 2 -l 1k -p 5200 -t $IPERF_DURATION >/dev/null 2>&1 &
                      nohup iperf3 -c 192.168.6.1 -P 2 -l 1k -p 5201 -t $IPERF_DURATION >/dev/null 2>&1 &
                      nohup iperf3 -c 192.168.6.1 -P 2 -l 1k -p 5202 -t $IPERF_DURATION >/dev/null 2>&1 &"
    sleep 3
    echo "[✓] iperf3 workload running"
}

stop_workload() {
    echo "[*] Stopping iperf3 ..."
    ssh "$CLIENT_IP" "pkill -9 iperf3" 2>/dev/null || true
    pkill -9 iperf3 2>/dev/null || true
}

trap stop_workload EXIT

# ── flow steering setup ─────────────────────────────────────────────
echo "========== Setting up flow steering (CPU $CPU) =========="
sudo bash "$SCRIPT_DIR/steer_flows.sh" "$CPU" || true
echo ""

# ── start traffic ────────────────────────────────────────────────────
start_workload

# ── helpers ──────────────────────────────────────────────────────────

# Parse cyclictest output for Max and Avg latency (microseconds)
# cyclictest format: "T: 0 (991565) P:99 I:1000 C:    100 Min:      3 Act:    4 Avg:    5 Max:      18"
# Note: fields like "Max:" and "18" are separate whitespace-delimited tokens
parse_cyclictest() {
    local file="$1"
    awk '/^T:/{
        for(i=1;i<=NF;i++){
            if($i=="Max:") max=$(i+1)+0
            if($i=="Avg:") avg=$(i+1)+0
        }
    } END{print max+0, avg+0}' "$file"
}

# Parse sar -u ALL output for %soft (softirq CPU usage)
parse_sar() {
    local file="$1"
    awk '/^Average:/ && $2 != "CPU" {printf "%.1f", $9}' "$file"
}

# ── CSV header ───────────────────────────────────────────────────────

echo "MAX_SOFTIRQ_RESTART,WorstLatUs,AvgLatUs,SoftirqPct" | tee "$OUTFILE"

# ── Pre-check: verify traffic is flowing to target CPU ───────────────
echo ""
echo "========== Verifying softirq load on CPU $CPU =========="
SOFTIRQ_BEFORE=$(awk '/NET_RX/ {print $'$((CPU+2))'}' /proc/softirqs)
sleep 2
SOFTIRQ_AFTER=$(awk '/NET_RX/ {print $'$((CPU+2))'}' /proc/softirqs)
SOFTIRQ_RATE=$(( (SOFTIRQ_AFTER - SOFTIRQ_BEFORE) / 2 ))
echo "NET_RX softirqs/sec on CPU $CPU: $SOFTIRQ_RATE"
if [[ "$SOFTIRQ_RATE" -lt 1000 ]]; then
    echo "[!] WARNING: Low softirq rate ($SOFTIRQ_RATE/s) — traffic may not be steered to CPU $CPU"
fi

# ── One-time build (kernel diff + codegen + BPF compile) ─────────────
echo ""
echo "========== Building MAX_SOFTIRQ_RESTART tunable (one-time) =========="
sudo bash "$SCRIPT_DIR/tune_softirq_restart.sh" build

# ── sweep ────────────────────────────────────────────────────────────

for val in "${VALUES[@]}"; do
    echo ""
    echo "========== MAX_SOFTIRQ_RESTART = $val =========="

    if [[ "$val" -eq 10 ]]; then
        # 10 is the default kernel value — no need to load tunable
        echo "[*] Using default kernel value (no tunable loaded)"
        sudo bash "$SCRIPT_DIR/tune_softirq_restart.sh" unload 2>/dev/null || true
    else
        # Unload previous, then patch + reload (no kernel rebuild)
        sudo bash "$SCRIPT_DIR/tune_softirq_restart.sh" unload 2>/dev/null || true
        sudo bash "$SCRIPT_DIR/tune_softirq_restart.sh" "$val"
    fi

    for rep in $(seq 1 "$REPS"); do
        tag="${val}_rep${rep}"
        lat_file="results/lat_${tag}.txt"
        cpu_file="results/cpu_${tag}.txt"

        sar -u ALL -P "$CPU" 1 > "$cpu_file" &
        SAR_PID=$!

        sudo cyclictest -t 1 -a "$CPU" -p 99 -d 1000 -l "$CYCLICTEST_LOOPS" \
            2>&1 | tee "$lat_file"

        # sar writes Average line on SIGINT
        kill -INT $SAR_PID 2>/dev/null || true
        wait $SAR_PID 2>/dev/null || true

        read -r worst avg <<< "$(parse_cyclictest "$lat_file")"
        cpu_pct=$(parse_sar "$cpu_file")

        echo "$val,$worst,$avg,$cpu_pct" | tee -a "$OUTFILE"
    done

    if [[ "$val" -ne 10 ]]; then
        sudo bash "$SCRIPT_DIR/tune_softirq_restart.sh" unload 2>/dev/null || true
    fi
done

# ── cleanup ──────────────────────────────────────────────────────────
sudo "$XKTOOL" table delete --all -y 2>/dev/null || true
rm -rf "$PROJECT_ROOT/bpf/stubs/"* 2>/dev/null || true

# ── done ─────────────────────────────────────────────────────────────

echo ""
echo "[✓] Done. Results: $OUTFILE"
echo ""
echo "Next steps:"
echo "  python3 plot/plot.py       # → plot/figure9.pdf"
