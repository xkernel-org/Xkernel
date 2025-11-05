```bash
# Make sure you already have a mounted f2fs device:
# It should output like this
$ findmnt /mnt/f2
TARGET SOURCE  FSTYPE OPTIONS
/mnt/f2
       /dev/nullb0
               f2fs   rw,relatime,lazytime,background_gc=on,nogc_merge,discard,discard_unit=sec

# umount the previous one, then remount it again
$ sudo umount /mnt/f2
$ sudo mount -t f2fs -o background_gc=on /dev/nullb0 /mnt/f2
```