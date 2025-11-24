#!/bin/bash

# Follow the setup and triggering instructions in the `xfs_inode_batch` README.md

for i in {1..100}; do
    sudo ./t /mnt/xfs-test
done