#!/bin/bash

THIS_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

BENCH_NAME=${BENCH_NAME:-"micro3-cgroup"}
REPEAT=${REPEAT:-3}

for VALUE in `seq 1 10`; do

    echo ==============================
    echo NUMA_PERIOD_THRESHOLD set to $VALUE
    echo ==============================

    cd $THIS_DIR/../../bpf_kprobe
    clang -g -O2 -target bpf -D__TARGET_ARCH_x86 -Ibpf/ \
        -DNEW_NUMA_PERIOD_THRESHOLD=$VALUE \
        -DSYMBOL_BASE_ADDRESS=0x$(bash $THIS_DIR/helpers/get__task_numa_fault__addr.sh) \
        -I/usr/include/bpf -c bpf/examples/numa_scan_poke.bpf.c \
        -o bpf/examples/numa_scan_poke.bpf.o
    sudo ./kprobe_loader --files numa_scan_poke.bpf.o --one-shot --quiet &
    PID=$!

    sleep 1

    bash $THIS_DIR/helpers/disas__task_numa_fault.sh
    sudo su -c 'tail -n +1 /sys/kernel/debug/sched/numa_balancing/*'

    for i in `seq 1 $REPEAT`; do

        echo --------
        echo Repeat $i
        echo --------

        sudo sync && echo 3 | sudo tee /proc/sys/vm/drop_caches >& /dev/null

        python $THIS_DIR/helpers/numa_stat.py save1

        case $BENCH_NAME in
            micro-ringbuf)
                /usr/bin/time -v $THIS_DIR/micro-ringbuf/numa_demo
                ;;
            npb)
                export OMP_NUM_THREADS=$(nproc)
                /usr/bin/time -v cg.E.x
                ;;
            graph500)
                /usr/bin/time -v mpirun -n 32 graph500_reference_bfs 26
                ;;
            gapbs)
                /usr/bin/time -v pr -u 30 -n 10
                ;;
            micro3-cgroup)
                bash $THIS_DIR/cgroup-wrapper.sh
                ;;
            liblinear)
                /usr/bin/time -v train -s 6 -m 20 /opt/kdd12
                ;;
            test)
                sleep 1
                ;;
        esac

        python $THIS_DIR/helpers/numa_stat.py save2
        python $THIS_DIR/helpers/numa_stat.py diff

    done

    bash $THIS_DIR/helpers/disas__task_numa_fault.sh
    sudo su -c 'tail -n +1 /sys/kernel/debug/sched/numa_balancing/*'

    kill "$PID"
    wait "$PID" 2>/dev/null

done
