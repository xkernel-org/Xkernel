# Follow the setup instructions in the `btrfs_max_bio_sectors` README.md.

MNT=/mnt/btrfs
fallocate -l 2G "$MNT/bigfile"

fio --name=btrfa_defrag_batch --filename="$MNT/bigfile" \
    --rw=randwrite --bs=4k --ioengine=psync --direct=0 \
    --iodepth=1 --time_based=1 --runtime=40 --numjobs=1

sync
sleep 2