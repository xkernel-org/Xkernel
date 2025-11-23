- Verify that your kernel has F2FS and compression support enabled:

```bash
$ grep F2FS_FS /boot/config-$(uname -r) | grep -E 'COMPRESSION|_FS=y'
```

- Create and mount a simple `f2fs` test filesystem with compression enabled:

```bash
$ dd if=/dev/zero of=/tmp/f2fs.img bs=1M count=4096

$ sudo losetup /dev/loop0 /tmp/f2fs.img

$ sudo mkfs.f2fs -O extra_attr,compression /dev/loop0

$ sudo mkdir -p /mnt/f2fs-test

$ sudo mount -t f2fs \
  -o compress_algorithm=lz4,compress_mode=fs,compress_chksum \
  /dev/loop0 /mnt/f2fs-test

$ mount | grep f2fs-test

$ cd /mnt/f2fs-test && sudo chattr +c .
```

- Create the `bigfile.bin` test file and start the workload:

```bash
$ cd /mnt/f2fs-test

$ sudo rm -f bigfile.bin

$ sudo dd if=/dev/zero of=bigfile.bin bs=128K count=8192 status=progress

$ sync

$ ./run.sh
```

