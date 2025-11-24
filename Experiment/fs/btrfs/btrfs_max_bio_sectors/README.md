- Tools & kernel modules:

```bash
sudo apt-get update && sudo apt-get install -y btrfs-progs fio
sudo modprobe btrfs
```

- Image file and loop device:

```bash
IMG=/users/yltang/sdb/btrfs.img
sudo mkdir -p /mnt/btrfs
[ -s "$IMG" ] || truncate -s 8G "$IMG"                               
```

- Bind and retrieve the actual loop device:

```bash
LOOP=$(sudo losetup -f --show "$IMG"); echo "LOOP=$LOOP"
sudo losetup -a | grep "$LOOP"        
```

- Check whether there's already a filesystem on the current loop device; if not, run mkfs.btrfs:

```bash
sudo blkid "$LOOP" || true
sudo file -s "$LOOP" | head -n 1

# mkfs.btrfs can create a filesystem on a 
# block device or a loop device backed by a file
sudo mkfs.btrfs -f -L testbtrfs "$LOOP"   
```

- First, try mounting without any special options; once successful, remount with your desired options:

```bash
sudo mount -t btrfs "$LOOP" /mnt/btrfs
findmnt /mnt/btrfs
```

- After successful basic mount, remount according to your experiment requirements (disable data checksums and compression):

```bash
sudo umount /mnt/btrfs
sudo mount -t btrfs -o nodatasum,compress=no "$LOOP" /mnt/btrfs
findmnt /mnt/btrfs

sudo fallocate -l 4G /mnt/btrfs/test.bin
ls -lh /mnt/btrfs/test.bin

fio --name=seed --filename=/mnt/btrfs/test.bin \
    --rw=write --bs=1M --size=4G --direct=1 --ioengine=libaio --iodepth=1 --end_fsync=1

sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'   # Optional: drop page cache
fio --name=dio_read --filename=/mnt/btrfs/test.bin \
    --rw=read --direct=1 --bs=4M --ioengine=libaio --iodepth=1 \
    --numjobs=1 --time_based=1 --runtime=10
```