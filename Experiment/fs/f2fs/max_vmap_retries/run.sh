#!/bin/bash
FILE=/mnt/f2fs-test/bigfile.bin

dd if="$FILE" of=/dev/null bs=128K status=none

NPROC=8

while true; do
    sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'

    for i in $(seq 1 $NPROC); do
        dd if="$FILE" of=/dev/null bs=128K status=none &
    done

    wait
done
