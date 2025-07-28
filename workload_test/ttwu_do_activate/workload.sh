#!/bin/bash

CPU_IDX=24

trap "exit" SIGINT SIGTERM

while true; do
    timeout 1 ./wakeup_task $CPU_IDX 100 || true
    timeout 1 ./wakeup_task $CPU_IDX 200 || true
    timeout 1 ./wakeup_task $CPU_IDX 400 || true
    timeout 1 ./wakeup_task $CPU_IDX 800 || true
    timeout 1 ./wakeup_task $CPU_IDX 1600 || true
done
