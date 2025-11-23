#!/bin/bash
# assume two nodes: 0 and 1
TASK="./t 0"
numactl --membind=0 --cpunodebind=0 $TASK &
PID=$!
echo "Started pid $PID on node0"

sleep 10

# move to CPU on node1
echo "Migrating pid $PID to CPU 3"
taskset -p -c 3 $PID

sleep 10

# move back to node0 cpu
echo "Migrating pid $PID back to CPU 0"
taskset -p -c 0 $PID

