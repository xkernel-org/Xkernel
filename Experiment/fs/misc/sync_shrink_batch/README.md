- Attach the eBPF programs:

```bash
sudo ./kprobe_loader --files sync_shrink_batch.bpf.o,hash_bucket_bits.bpf.o,shrink_divisor.bpf.o
```

- Create a disk image:

```bash
truncate -s 4G /tmp/x.img

# before creating the ext4 image, must attach hash_bucket_bits.bpf.o
sudo mkfs.ext4 -F /tmp/x.img

sudo tune2fs -m 0 /tmp/x.img

sudo mkdir -p /mnt/x
sudo mount -o loop,user_xattr /tmp/x.img /mnt/x

mount | grep " /mnt/x "
df -h /mnt/x
df -i /mnt/x

sudo mkdir -p /mnt/x/xx
```

- Limit CPU we can use:

```bash
cat echo 1 | sudo tee /sys/devices/virtual/workqueue/cpumask
echo 1 | sudo tee /sys/devices/virtual/workqueue/cpumask
```

- Create another process to contend the CPU:

```bash
sudo taskset -c 0 chrt -f 99 bash -c 'while :; do :; done' &
```

- Run the program:

```bash
sudo taskset -c 1-15 ./t /mnt/x/xx 512 800000 512
```