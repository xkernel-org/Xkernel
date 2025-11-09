# 0) 工具 & 模块
which mkfs.btrfs || (sudo apt-get update && sudo apt-get install -y btrfs-progs)   # 安装 btrfs-progs
sudo modprobe btrfs                                                                 # 加载内核模块

# 1) 映像文件与 loop 设备
IMG=/users/yltang/sdb/btrfs.img
sudo mkdir -p /mnt/btrfs
[ -s "$IMG" ] || truncate -s 8G "$IMG"                                              # 没有就创建 8G 映像
# 绑定并取回真实 loop 节点
LOOP=$(sudo losetup -f --show "$IMG"); echo "LOOP=$LOOP"
sudo losetup -a | grep "$LOOP"                                                      # 确认映射存在

# 2) 确认当前 loop 上有没有文件系统；如果没有就 mkfs.btrfs
sudo blkid "$LOOP" || true
sudo file -s "$LOOP" | head -n 1

# ——如果上两行没显示 TYPE="btrfs"，那就格式化：——
sudo mkfs.btrfs -f -L testbtrfs "$LOOP"   # mkfs.btrfs 可以对块设备或“文件背后的 loop 设备”建 FS

# 3) 先不带任何奇怪选项尝试挂载，成功后再加你要的选项
sudo mount -t btrfs "$LOOP" /mnt/btrfs
findmnt /mnt/btrfs

# 4) 成功后，按你的实验需求重新挂载（禁用数据校验、压缩）
sudo umount /mnt/btrfs
sudo mount -t btrfs -o nodatasum,compress=no "$LOOP" /mnt/btrfs
findmnt /mnt/btrfs

sudo fallocate -l 4G /mnt/btrfs/test.bin
ls -lh /mnt/btrfs/test.bin

fio --name=seed --filename=/mnt/btrfs/test.bin \
    --rw=write --bs=1M --size=4G --direct=1 --ioengine=libaio --iodepth=1 --end_fsync=1

sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'   # 可选：清页缓存
fio --name=dio_read --filename=/mnt/btrfs/test.bin \
    --rw=read --direct=1 --bs=4M --ioengine=libaio --iodepth=1 \
    --numjobs=1 --time_based=1 --runtime=10
