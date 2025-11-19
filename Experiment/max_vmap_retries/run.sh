#!/bin/bash
FILE=/mnt/f2fs-test/bigfile.bin

# 先热身一次，确保文件真的存在且可读
dd if="$FILE" of=/dev/null bs=128K status=none

# 多进程一起读
NPROC=8

while true; do
    sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'

    for i in $(seq 1 $NPROC); do
        dd if="$FILE" of=/dev/null bs=128K status=none &
    done

    wait
done
