#!/bin/bash

# First follow the README.md of `xfs_inode_batch` to create a `xfs` filesystem.

for i in {1..1000}; do
    sudo fstrim -v /mnt/xfs-test
done