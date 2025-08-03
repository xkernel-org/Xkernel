# Adapted from https://github.com/ece-fast-lab/ASPLOS-2025-M5.git

THIS_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

# Replace this with the desired workload
CMD=${CMD:-"bash $THIS_DIR/micro3/run.sh"}

echo "CMD: $CMD"

CGROUP_PATH=/sys/fs/cgroup/app

# FIXME: pick a value for your workload
MEM_SIZE=18000M

set_cgroup_cfg() {
    echo "--------------------------------"
    echo "Setting cgroup to node(s): $1, size: $2"
    # FIXME: pick a list for your workload and machine
    # In my experiment, these are all on node 0
    echo '0,2,4,6,8,10,12,14,16,18,20,22,24,26,28,30,32,34,36,38' |\
        sudo tee $CGROUP_PATH/cpuset.cpus > /dev/null
    echo $1 | sudo tee $CGROUP_PATH/cpuset.mems > /dev/null
    echo max | sudo tee $CGROUP_PATH/memory.high > /dev/null
    echo $2 | sudo tee $CGROUP_PATH/memory.max > /dev/null

    printf "cpuset.cpus: $(cat $CGROUP_PATH/cpuset.cpus)\n"
    printf "cpuset.mems: $(cat $CGROUP_PATH/cpuset.mems)\n"
    printf "cpuset.mems.effective: $(cat $CGROUP_PATH/cpuset.mems.effective)\n"
    printf "memory.high: $(cat $CGROUP_PATH/memory.high)\n"
    printf "memory.max: $(cat $CGROUP_PATH/memory.max)\n"

    echo "--------------------------------"
}

sleep_and_migrate() {
    echo "sleeping $1, waiting for load"
    sleep $1
    echo "re-enable migration"
    set_cgroup_cfg "0,1" "$MEM_SIZE"
}

# lock memory to node1
set_cgroup_cfg "1" "$MEM_SIZE"

# then gradually migrate to node 0
sleep_and_migrate 10 &

# run!
/usr/bin/time -v \
    sudo cgexec -g cpuset,memory:app $CMD
