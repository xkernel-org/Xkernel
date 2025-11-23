#!/bin/bash

# First follow the README.md of `xfs_inode_batch` to create a `xfs` filesystem.

for i in {1..100}; do
    sudo ./t /mnt/xfs-test
done