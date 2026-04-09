#!/bin/bash
# run.sh — Figure 9 experiment: vary MAX_SOFTIRQ_RESTART = {1,5,10,15,20}
#
# Measures cyclictest tail/avg latency and CPU utilization under heavy
# softirq load for each value of MAX_SOFTIRQ_RESTART.
#
# Prerequisites:
#   - 3 iperf3 clients already sending traffic (see client.sh)
#   - Flows steered to CPU $CPU (see steer_flows.sh)
#
# Usage: bash run.sh [CPU] [REPS]

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CPU=${1:-3}
REPS=${2:-3}                       # repetitions per value
VALUES=(1 5 10 15 20)
CYCLICTEST_LOOPS=20000             # ~20s per run
OUTFILE="results/figure9.csv"

mkdir -p results

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

# Parse sar output for average CPU utilization (100 - %idle)
parse_sar() {
    local file="$1"
    awk '/^Average:/ && $2 != "CPU" {printf "%.0f", 100 - $NF}' "$file"
}

# ── CSV header ───────────────────────────────────────────────────────

echo "MAX_SOFTIRQ_RESTART,WorstLatUs,AvgLatUs,CpuUtilPct" | tee "$OUTFILE"

# ── sweep ────────────────────────────────────────────────────────────

for val in "${VALUES[@]}"; do
    echo ""
    echo "========== MAX_SOFTIRQ_RESTART = $val =========="

    if [[ "$val" -eq 10 ]]; then
        # 10 is the default kernel value — no need to load tunable
        echo "[*] Using default kernel value (no tunable loaded)"
    else
        bash "$SCRIPT_DIR/tune_softirq_restart.sh" "$val"
    fi

    for rep in $(seq 1 "$REPS"); do
        tag="${val}_rep${rep}"
        lat_file="results/lat_${tag}.txt"
        cpu_file="results/cpu_${tag}.txt"

        sar -u -P "$CPU" 1 > "$cpu_file" &
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
        bash "$SCRIPT_DIR/tune_softirq_restart.sh" unload
    fi

    # Clean tables and stubs between rounds to avoid stale state
    ~/Xkernel/xkernel-tool table delete --all -y
    rm -rf ~/Xkernel/bpf/stubs/*
done

# ── done ─────────────────────────────────────────────────────────────

echo ""
echo "[✓] Done. Results: $OUTFILE"
