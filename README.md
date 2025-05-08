# Xkernel

## blk_alloc_queue

1. Get function address: `sudo cat /proc/kallsyms | grep -B1 -A1 blk_alloc_queue`

2. Get attach point: `sudo objdump -d --start-address=0xffffffffabbbe2b0 --stop-address=0xffffffffabbbe4e0 /proc/kcore`

3. Calculate offset.

4. Load eBPF program: `sudo ./kprobe_loader`

5. Run application to trigger eBPF program: `sudo bash test_app.sh
