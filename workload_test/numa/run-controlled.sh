#!/bin/bash

THIS_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
REPEAT=${REPEAT:-6}
BUFFER_SIZE_MB=${BUFFER_SIZE_MB:-100000}
ROUNDS=${ROUNDS:-5}
bash $THIS_DIR/helpers/disas__task_numa_fault.sh
sudo su -c 'tail -n +1 /sys/kernel/debug/sched/numa_balancing/*'

for i in `seq 1 $REPEAT`; do

    echo --------
    echo Repeat $i
    echo --------

    sudo sync && echo 3 | sudo tee /proc/sys/vm/drop_caches >& /dev/null

    python $THIS_DIR/helpers/numa_stat.py save1

    ## Use this to get the scale of background noise
    # /usr/bin/time -v sleep 60

    ## One thread, init only, pin CPU
    # /usr/bin/time -v $THIS_DIR/controlled/prog 1 $BUFFER_SIZE_MB 1 1 0 1

    ## One thread, init only, do not pin CPU
    # /usr/bin/time -v $THIS_DIR/controlled/prog 1 $BUFFER_SIZE_MB 1 1 0 0

    ## One thread, init + access, pin CPU
    # /usr/bin/time -v $THIS_DIR/controlled/prog 1 $BUFFER_SIZE_MB 1 0 0 1

    ## One thread, init + access, do not pin CPU
    # /usr/bin/time -v $THIS_DIR/controlled/prog 1 $BUFFER_SIZE_MB 1 0 0 0

    ## One thread, init + access x ROUND, pin CPU
    # /usr/bin/time -v $THIS_DIR/controlled/prog 1 $BUFFER_SIZE_MB $ROUNDS 0 0 1

    ## One thread, init + access x ROUND, do not pin CPU
    # /usr/bin/time -v $THIS_DIR/controlled/prog 1 $BUFFER_SIZE_MB $ROUNDS 0 0 0

    ## Two threads, init only, pin CPU
    # /usr/bin/time -v $THIS_DIR/controlled/prog 2 $BUFFER_SIZE_MB 1 1 0 1

    ## Two threads, init only, do not pin CPU
    # /usr/bin/time -v $THIS_DIR/controlled/prog 2 $BUFFER_SIZE_MB 1 1 0 0

    ## Two threads, init + access, pin CPU
    # /usr/bin/time -v $THIS_DIR/controlled/prog 2 $BUFFER_SIZE_MB 1 0 0 1

    ## Two threads, init + access, do not pin CPU
    # /usr/bin/time -v $THIS_DIR/controlled/prog 2 $BUFFER_SIZE_MB 1 0 0 0

    ## Two threads, init + access x ROUND, pin CPU
    # /usr/bin/time -v $THIS_DIR/controlled/prog 2 $BUFFER_SIZE_MB $ROUNDS 0 0 1

    ## Two threads, init + access x ROUND, do not pin CPU
    # /usr/bin/time -v $THIS_DIR/controlled/prog 2 $BUFFER_SIZE_MB $ROUNDS 0 0 0

    ## Two threads, init, access x ROUND from a remote core, pin CPU
    # /usr/bin/time -v $THIS_DIR/controlled/prog 2 $BUFFER_SIZE_MB $ROUNDS 0 1 1

    ## Not valid
    # /usr/bin/time -v $THIS_DIR/controlled/prog 2 $BUFFER_SIZE_MB $ROUNDS 0 1 0

    python $THIS_DIR/helpers/numa_stat.py save2
    python $THIS_DIR/helpers/numa_stat.py diff

    # Sleep a bit longer so that monitoring scripts can sense different
    # repeat rounds
    sleep 5
done

bash $THIS_DIR/helpers/disas__task_numa_fault.sh
sudo su -c 'tail -n +1 /sys/kernel/debug/sched/numa_balancing/*'
