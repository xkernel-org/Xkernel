#!/bin/bash
# run.sh — Full Figure 9 experiment (server side)
#
# Measures cyclictest latency under heavy softirq load, then repeats
# with MAX_SOFTIRQ_RESTART tuned down.
#
# Prerequisites:
#   - 3 iperf3 clients already sending traffic (see client.sh)
#   - Flows steered to CPU $CPU (see steer_flows.sh)
#
# Usage: bash run.sh [CPU]

set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CPU=${1:-3}

mkdir -p results

echo "========== Baseline (MAX_SOFTIRQ_RESTART = 10) =========="
bash "$SCRIPT_DIR/metric.sh" "$CPU" > /tmp/softirq_pre_baseline
mpstat -P "$CPU" 1 25 > results/baseline_cpu.txt &
MPSTAT_PID=$!
sudo cyclictest -t 1 -a "$CPU" -p 99 -d 1000 -l 20000 2>&1 | tee results/baseline_lat.txt
wait $MPSTAT_PID 2>/dev/null || true
bash "$SCRIPT_DIR/metric.sh" "$CPU" > /tmp/softirq_post_baseline

echo -e "\n=== Baseline Softirq Increments ==="
awk 'NR==FNR{pre[$1]=$2;next}{printf "%-20s %10d\n",$1,$2-(pre[$1]?pre[$1]:0)}' \
    /tmp/softirq_pre_baseline /tmp/softirq_post_baseline | tee results/baseline_softirq.txt

echo ""
echo "========== Tuned (MAX_SOFTIRQ_RESTART = 1) =========="
bash "$SCRIPT_DIR/tune_softirq_restart.sh" 1

bash "$SCRIPT_DIR/metric.sh" "$CPU" > /tmp/softirq_pre_tuned
mpstat -P "$CPU" 1 25 > results/tuned_cpu.txt &
MPSTAT_PID=$!
sudo cyclictest -t 1 -a "$CPU" -p 99 -d 1000 -l 20000 2>&1 | tee results/tuned_lat.txt
wait $MPSTAT_PID 2>/dev/null || true
bash "$SCRIPT_DIR/metric.sh" "$CPU" > /tmp/softirq_post_tuned

echo -e "\n=== Tuned Softirq Increments ==="
awk 'NR==FNR{pre[$1]=$2;next}{printf "%-20s %10d\n",$1,$2-(pre[$1]?pre[$1]:0)}' \
    /tmp/softirq_pre_tuned /tmp/softirq_post_tuned | tee results/tuned_softirq.txt

echo ""
echo "========== Cleanup =========="
bash "$SCRIPT_DIR/tune_softirq_restart.sh" unload
~/Xkernel/xkernel-tool table delete --all -y
rm -rf ~/Xkernel/bpf/stubs/*

echo ""
echo "[✓] Done. Results saved to results/"
