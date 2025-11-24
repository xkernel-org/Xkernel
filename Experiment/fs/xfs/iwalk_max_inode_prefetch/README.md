- Follow the setup and triggering instructions in the `xfs_inode_batch` README.md

- Before experiment:

```bash
sudo apt install xfslibs-dev xfsprogs

grep ^CONFIG_XFS /boot/config-$(uname -r)
# It may output like this
CONFIG_XFS_FS=m
CONFIG_XFS_SUPPORT_V4=y
CONFIG_XFS_SUPPORT_ASCII_CI=y
CONFIG_XFS_QUOTA=y
CONFIG_XFS_POSIX_ACL=y
CONFIG_XFS_RT=y


modinfo xfs 2>/dev/null || echo "no xfs module installed"
lsmod | grep ^xfs

grep -w xfs_iwalk_threaded /proc/kallsyms

for d in /mnt/xfs-test/batch{00..09}; do
  sudo mkdir -p "$d"  
  seq -w 0 999 | xargs -I{} sudo sh -c ': > "$1"' _ "$d"/f{}
done
```