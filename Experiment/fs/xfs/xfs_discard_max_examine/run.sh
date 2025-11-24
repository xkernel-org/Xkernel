#!/bin/bash

# Follow the setup and triggering instructions in the `xfs_inode_batch` README.md

for i in {1..1000}; do
    sudo fstrim -v /mnt/xfs-test
done