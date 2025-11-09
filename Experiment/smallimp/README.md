# 需要多节点机器
numactl -H

# 开启自动 NUMA 平衡（root）
cat /proc/sys/kernel/numa_balancing
echo 1 | sudo tee /proc/sys/kernel/numa_balancing

cat  /proc/sys/kernel/numa_balancing_promote_rate_limit_MBps
65536

echo 64 | sudo tee /proc/sys/kernel/numa_balancing_promote_rate_limit_MBps
64

numactl --cpunodebind=0 --membind=1 \
  stress-ng --vm $(nproc) --vm-bytes 2G \
            --vm-keep --vm-method prime-1 \
            --vm-madvise nohugepage \
            --timeout 60s


numactl --cpunodebind=1 --membind=0 \
  stress-ng --vm $(nproc) --vm-bytes 2G \
            --vm-keep --vm-method prime-1 \
            --vm-madvise nohugepage \
            --timeout 60s