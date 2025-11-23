- Prepare `ubifs` filesystem:

```bash
sudo apt-get update && sudo apt-get install -y mtd-utils

# 32MiB, batch size is 128KiB
sudo modprobe -r mtdram || true
sudo modprobe mtdram total_size=32768 erase_size=128

sudo ubiformat /dev/mtd0 -y
sudo ubiattach /dev/ubi_ctrl -m 0

sudo ubimkvol /dev/ubi0 -N ubifs-test -s 24MiB

sudo mkdir -p /mnt/ubi
sudo mount -t ubifs -o compr=none ubi0:ubifs-test /mnt/ubi
mount | grep ubifs  
```

- Trigger steps:

```bash
DIR=/mnt/ubi
cd "$DIR"

# Create fragmentation by writing many small files (using /dev/urandom)
# 22000 is an arbitrary number
# the specific size can be set according to the size of 
# the /mnt/ubi file you create
for i in $(seq 1 22000); do
  sudo dd if=/dev/urandom of="s_$i" bs=4096 count=1 status=none
done
sync

# Randomly delete a portion to create a dirty hole
ls s_* | shuf | head -n 9000 | xargs -P"$(nproc)" -I{} rm -f "{}"

# Calculate the available space within the volume and 
# write 1.5 times it to force budget failure → make_free_space() → run_gc()
AVAIL_K=$(df -k . | awk 'NR==2{print $4}')
SZ=$(( AVAIL_K + AVAIL_K/2 ))
sudo dd if=/dev/urandom of=big.bin bs=1024 count="$SZ" oflag=direct status=none || true
```