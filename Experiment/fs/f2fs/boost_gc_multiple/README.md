Using `null_blk` to simulate a zoned device

- Create a zoned `null_blk` device:

```bash
$ sudo modprobe null_blk nr_devices=1 zoned=1 gb=10 zone_size=64 zone_nr_conv=3 memory_backed=1

lsblk -o NAME,ZONED,ZONE-SZ,ZONE-NR /dev/nullb0
sudo blkzone report /dev/nullb0 | head
```

- Format the device as `f2fs` and mount it:

```bash
$ sudo mkfs.f2fs -f -m /dev/nullb0
$ sudo mkdir -p /mnt/f2
$ sudo mount -t f2fs -o background_gc=on /dev/nullb0 /mnt/f2
```

- Configure the `f2fs` GC-related settings:

```bash
$ DEV=nullb0
$ BASE=/sys/fs/f2fs/$DEV
$ cat $BASE/gc_no_zoned_gc_percent 
$ echo 95  | sudo tee $BASE/gc_no_zoned_gc_percent            
$ cat $BASE/gc_boost_zoned_gc_percent
$ echo 50  | sudo tee $BASE/gc_boost_zoned_gc_percent         
```

- Trigger garbage collection (ensure you have at least 6 GiB free space in `/mnt/f2`):

```bash
$ fio --name=fill --filename=/mnt/f2/big.bin --rw=write --bs=1M --size=6G --direct=1 --iodepth=32 --ioengine=libaio

$ fio --name=churn --filename=/mnt/f2/big.bin --rw=randwrite --bs=4k --time_based --runtime=120 --fsync=1 --direct=1 --iodepth=32 --ioengine=libaio
```