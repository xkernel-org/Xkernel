# 1. Prepare a disk image and mount it as XFS
```bash
IMG=/users/yltang/sdb/xfs.img
DEV=$(losetup -f)                 # Find a free loop device
# Allocate space when needed
# sudo fallocate -l 2G "$IMG"
sudo losetup "$DEV" "$IMG"
sudo mkfs.xfs -f "$DEV"           
sudo mkdir -p /mnt/xfs_test
sudo mount -o inode64 "$DEV" /mnt/xfs_test

sudo xfs_db -r "$DEV" -c 'version'
```

# 2. Create small files concurrently to trigger it
```bash
cd /mnt/xfs_test
mkdir files && cd files
sudo sh -c 'seq 1 20000 | xargs -n1 -P"$(nproc)" -I{} touch f_{}'
sync
```