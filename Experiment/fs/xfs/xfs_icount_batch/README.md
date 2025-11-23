- Prepare a disk image and mount it as `xfs`:

```bash
IMG=/users/yltang/sdb/xfs.img

# Find a free loop device
DEV=$(losetup -f)                 

# Allocate space when needed
sudo fallocate -l 2G "$IMG"
sudo losetup "$DEV" "$IMG"
sudo mkfs.xfs -f "$DEV"           
sudo mkdir -p /mnt/xfs-test
sudo mount -o inode64 "$DEV" /mnt/xfs-test
sudo xfs_db -r "$DEV" -c 'version'
```

- Create small files concurrently to trigger it:

```bash
cd /mnt/xfs-test
mkdir files && cd files
sudo sh -c 'seq 1 20000 | xargs -n1 -P"$(nproc)" -I{} touch f_{}'
sync
```