# 1) 三/四个回环盘
truncate -s 4G /tmp/btrfs_{0,1,2,3}.img
sudo losetup -fP /tmp/btrfs_0.img
sudo losetup -fP /tmp/btrfs_1.img
sudo losetup -fP /tmp/btrfs_2.img
# 可选第四个：sudo losetup -fP /tmp/btrfs_3.img

# 2) mkfs：数据 RAID5（或 RAID6），元数据建议 RAID1/RAID1c3 更稳
sudo mkfs.btrfs -d raid5 -m raid1 $(losetup -j /tmp/btrfs_0.img | cut -d: -f1) \
                              $(losetup -j /tmp/btrfs_1.img | cut -d: -f1) \
                              $(losetup -j /tmp/btrfs_2.img | cut -d: -f1)

(base) yltang@node-0:~/sdb/Xkernel/Experiment/rbio_cache_size$ sudo mkfs.btrfs -d raid5 -m raid1 $(losetup -j /tmp/btrfs_0.img | cut -d: -f1) \
                              $(losetup -j /tmp/btrfs_1.img | cut -d: -f1) \
                              $(losetup -j /tmp/btrfs_2.img | cut -d: -f1)
btrfs-progs v6.6.3
See https://btrfs.readthedocs.io for more information.

WARNING: RAID5/6 support has known problems is strongly discouraged
         to be used besides testing or evaluation.

Performing full device TRIM /dev/loop3 (4.00GiB) ...
Performing full device TRIM /dev/loop4 (4.00GiB) ...
Performing full device TRIM /dev/loop2 (4.00GiB) ...
NOTE: several default settings have changed in version 5.15, please make sure
      this does not affect your deployments:
      - DUP for metadata (-m dup)
      - enabled no-holes (-O no-holes)
      - enabled free-space-tree (-R free-space-tree)

Label:              (null)
UUID:               1d7c2192-b2ed-4369-9990-95b45676e1db
Node size:          16384
Sector size:        4096
Filesystem size:    12.00GiB
Block group profiles:
  Data:             RAID5           819.12MiB
  Metadata:         RAID1           256.00MiB
  System:           RAID1             8.00MiB
SSD detected:       no
Zoned device:       no
Incompat features:  extref, raid56, skinny-metadata, no-holes, free-space-tree
Runtime features:   free-space-tree
Checksum:           crc32c
Number of devices:  3
Devices:
   ID        SIZE  PATH      
    1     4.00GiB  /dev/loop2
    2     4.00GiB  /dev/loop3
    3     4.00GiB  /dev/loop4

这是我输出的信息，下一步应该怎么操作

# 让内核扫描并登记这套多设备文件系统（多设备场景推荐先做这步）
sudo btrfs device scan

# 建挂载点并挂载（用 mkfs 输出里的 UUID 最稳妥）
sudo mkdir -p /mnt/btr
sudo mount -t btrfs UUID=1d7c2192-b2ed-4369-9990-95b45676e1db /mnt/btr
# 也可以直接用其中任一 /dev/loopX 挂载；在已扫描设备的前提下同样有效
# sudo mount /dev/loop2 /mnt/btr

findmnt /mnt/btr
sudo btrfs filesystem show /mnt/btr
sudo btrfs filesystem df /mnt/btr

dd if=/dev/zero of=/mnt/btr/test.dd bs=4K oflag=direct count=200000 status=progress

gcc -O2 -Wall hotstripe.c -o hotstripe
./hotstripe /mnt/btr/hot 20
