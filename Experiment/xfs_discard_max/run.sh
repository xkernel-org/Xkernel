#!/bin/bash
for i in {1..1000}; do
    sudo fstrim -v /mnt/xfs_test
done