# Using `null_blk` to simulate zoned device

```bash
# 1. Create null_blk
sudo modprobe null_blk nr_devices=1 zoned=1 gb=10 zone_size=64 zone_nr_conv=3 memory_backed=1

lsblk -o NAME,ZONED,ZONE-SZ,ZONE-NR /dev/nullb0
sudo blkzone report /dev/nullb0 | head

# 2.Format the device to f2fs and mount
sudo mkfs.f2fs -f -m /dev/nullb0
sudo mkdir -p /mnt/f2
sudo mount -t f2fs -o background_gc=on /dev/nullb0 /mnt/f2

# 3.
DEV=nullb0
BASE=/sys/fs/f2fs/$DEV
cat $BASE/gc_no_zoned_gc_percent 
echo 95  | sudo tee $BASE/gc_no_zoned_gc_percent            
cat $BASE/gc_boost_zoned_gc_percent
echo 50  | sudo tee $BASE/gc_boost_zoned_gc_percent         

# 4.Trigger the gc, and make sure you have enough space(6G) on the directory
fio --name=fill --filename=/mnt/f2/big.bin --rw=write --bs=1M --size=6G --direct=1 --iodepth=32 --ioengine=libaio
fio --name=churn --filename=/mnt/f2/big.bin --rw=randwrite --bs=4k --time_based --runtime=120 --fsync=1 --direct=1 --iodepth=32 --ioengine=libaio
```