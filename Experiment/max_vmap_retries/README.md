grep F2FS_FS /boot/config-$(uname -r) | grep -E 'COMPRESSION|_FS=y'

# 1) 创建 4G 镜像
dd if=/dev/zero of=/tmp/f2fs.img bs=1M count=4096

# 2) 关联到 loop 设备
sudo losetup /dev/loop0 /tmp/f2fs.img

# 3) 用 compression feature 格式化
sudo mkfs.f2fs -O extra_attr,compression /dev/loop0


sudo mkdir -p /mnt/f2fs-test
sudo mount -t f2fs \
  -o compress_algorithm=lz4,compress_mode=fs,compress_chksum \
  /dev/loop0 /mnt/f2fs-test


mount | grep f2fs-test
# 或者
cat /proc/mounts | grep f2fs-test

cd /mnt/f2fs-test

# 为整个挂载点开启压缩标志（新建的文件默认带 C）
sudo chattr +c .

# 或者只对某个目录：
# sudo mkdir data
# sudo chattr -R +c data

lsattr bigfile.bin
# 正常应该看到类似：----C-------- bigfile.bin
# 其中 C 就是 compression 标志

cd /mnt/f2fs-test

# 确保 bigfile.bin 不存在
sudo rm -f bigfile.bin

# 写入 1 GiB 全 0 的数据（高度可压缩）
dd if=/dev/zero of=bigfile.bin bs=128K count=8192 status=progress

sync

运行run.sh脚本
