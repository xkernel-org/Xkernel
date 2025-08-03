#!/bin/bash

THIS_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

BENCH_NAME=${BENCH_NAME:-"micro3-cgroup"}

for VALUE in `seq 1 10`; do

    echo =====
    echo $VALUE
    echo =====

    cd $THIS_DIR/../../bpf_kprobe
    clang -g -O2 -target bpf -D__TARGET_ARCH_x86 -Ibpf/ \
        -DNEW_NUMA_PERIOD_THRESHOLD=$VALUE \
        -DSYMBOL_BASE_ADDRESS=0x$(bash $THIS_DIR/helpers/get__task_numa_fault__addr.sh) \
        -I/usr/include/bpf -c bpf/examples/numa_scan_poke.bpf.c \
        -o bpf/examples/numa_scan_poke.bpf.o
    sudo ./kprobe_loader --files numa_scan_poke.bpf.o --one-shot &
    PID=$!

    sleep 1

    bash $THIS_DIR/helpers/disas__task_numa_fault.sh

    case $BENCH_NAME in
        micro3-cgroup)
            bash $THIS_DIR/cgroup-wrapper.sh
            ;;
        liblinear)
            train -s 6 -m 20 /opt/kdd12
            ;;
        test)
            sleep 1
            ;;
    esac

    kill "$PID"
    wait "$PID" 2>/dev/null

done
