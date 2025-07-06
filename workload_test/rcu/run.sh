#!/bin/bash

echo "[INFO] Collecting slabtop and meminfo before insmod..."
sudo slabtop -o > slabtop_before.txt
cat /proc/meminfo > meminfo_before.txt

sudo dmesg -C

echo "[INFO] Inserting rcu_workload.ko..."
sudo insmod rcu_workload.ko
if [ $? -ne 0 ]; then
    echo "[ERROR] insmod failed! Exiting."
    exit 1
fi

sleep 1

echo "[INFO] Collecting slabtop and meminfo after alloc..."
sudo slabtop -o > slabtop_after_alloc.txt
cat /proc/meminfo > meminfo_after_alloc.txt

echo "[INFO] Waiting for free..."
sleep 3

sudo rmmod rcu_workload.ko

echo "[INFO] Collecting slabtop and meminfo after free..."
sudo slabtop -o > slabtop_after_free.txt
cat /proc/meminfo > meminfo_after_free.txt

echo "[INFO] Done."

sudo dmesg