- Create img files:

```bash
truncate -s 4G /tmp/btrfs_{0,1,2,3}.img
sudo losetup -fP /tmp/btrfs_0.img
sudo losetup -fP /tmp/btrfs_1.img
sudo losetup -fP /tmp/btrfs_2.img
```

- mkfs: use RAID5 (or RAID6) for data, and RAID1/RAID1c3 for metadata is recommended for better stability:

```bash
sudo mkfs.btrfs -d raid5 -m raid1 $(losetup -j /tmp/btrfs_0.img | cut -d: -f1) \
                              $(losetup -j /tmp/btrfs_1.img | cut -d: -f1) \
                              $(losetup -j /tmp/btrfs_2.img | cut -d: -f1)
```

- Let the kernel scan and register this multi-device filesystem (for multi-device setups, it’s recommended to do this step first):

```bash
sudo btrfs device scan
```

- Create the mount point and mount it (using the UUID printed by mkfs is the most reliable way):

```bash
sudo mkdir -p /mnt/btr
sudo mount -t btrfs UUID=1d7c2192-b2ed-4369-9990-95b45676e1db /mnt/btr
# You can also mount using any one of the /dev/loopX devices directly;
# this also works as long as the devices have been scanned.
# sudo mount /dev/loop2 /mnt/btr

findmnt /mnt/btr
sudo btrfs filesystem show /mnt/btr
sudo btrfs filesystem df /mnt/btr

dd if=/dev/zero of=/mnt/btr/test.dd bs=4K oflag=direct count=200000 status=progress
```

- Compile and run:

```bash
gcc -O2 -Wall t.c -o t
./t /mnt/btr/hot 20
```
