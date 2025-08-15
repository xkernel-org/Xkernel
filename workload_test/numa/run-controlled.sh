#!/bin/bash

THIS_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
REPEAT=${REPEAT:-6}

bash $THIS_DIR/helpers/disas__task_numa_fault.sh

for i in `seq 1 $REPEAT`; do

    echo --------
    echo Repeat $i
    echo --------

    sudo sync && echo 3 | sudo tee /proc/sys/vm/drop_caches >& /dev/null

    python $THIS_DIR/helpers/numa_stat.py save1

    ## Use this to get the scale of background noise

    /usr/bin/time -v sleep 60

    ## Buffer size: 100G

    ## One thread, init only
    # /usr/bin/time -v $THIS_DIR/controlled/1-thread 1 100000 1 1
    # /usr/bin/time -v taskset -c 0 $THIS_DIR/controlled/1-thread 1 100000 1 1
    ## One thread, init + access
    # /usr/bin/time -v $THIS_DIR/controlled/1-thread 1 100000 1 0
    # /usr/bin/time -v taskset -c 0 $THIS_DIR/controlled/1-thread 1 100000 1 0

    ## Buffer size: 5G

    ## One thread, init only
    # /usr/bin/time -v $THIS_DIR/controlled/1-thread 1 5000 1 1
    # /usr/bin/time -v taskset -c 0 $THIS_DIR/controlled/1-thread 1 5000 1 1
    ## One thread, init + access
    # /usr/bin/time -v $THIS_DIR/controlled/1-thread 1 5000 1 0
    # /usr/bin/time -v taskset -c 0 $THIS_DIR/controlled/1-thread 1 5000 1 0
    ## One thread, init + access more rounds
    # /usr/bin/time -v taskset -c 0 $THIS_DIR/controlled/1-thread 1 5000 5 0
    ## Two threads, init only
    # /usr/bin/time -v $THIS_DIR/controlled/2-threads 2 2500 1 1
    ## Two threads, init + access
    # /usr/bin/time -v $THIS_DIR/controlled/2-threads 2 2500 1 0
    ## Two threads, init + access more rounds
    # /usr/bin/time -v $THIS_DIR/controlled/2-threads 2 2500 50 0

    python $THIS_DIR/helpers/numa_stat.py save2
    python $THIS_DIR/helpers/numa_stat.py diff

done

bash $THIS_DIR/helpers/disas__task_numa_fault.sh
