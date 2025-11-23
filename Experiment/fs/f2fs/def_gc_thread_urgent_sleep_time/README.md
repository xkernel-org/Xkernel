- Before starting, follow the max_vmap_retries README.md to set things up, and then verify the mount options:

```bash
$ findmnt /mnt/f2fs-test
TARGET         SOURCE     FSTYPE OPTIONS
/mnt/f2fs-test /dev/loop0 f2fs   rw,relatime,lazytime,background_gc=on,nogc_merge,discard,discard_unit=block,user_xattr,inline_xattr,acl,inline_data,inline_dentry,flush_merge,barrier,extent_cache,mode=adaptive,active_logs=6,alloc_mode=reuse,checkpoint_merge,fsync_mode=posix,compress_algorithm=lz4,compress_log_size=2,compress_chksum,compress_mode=fs,memory=normal,errors=continue
```

- Unmount and remount the filesystem, because this macro is triggered when `f2fs ` is mounted:

```bash
$ sudo umount /mnt/f2fs-test

$ sudo mount -t f2fs   -o compress_algorithm=lz4,compress_mode=fs,compress_chksum   /dev/loop0 /mnt/f2fs-test
```