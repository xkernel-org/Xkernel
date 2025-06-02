# Xkernel

## Dependencies
`sudo apt-get install clang llvm libbpf-dev pahole -y`

`sudo apt-get install linux-source gdb -y`

`cd /usr/src/ && sudo tar -xvf linux-source-6.8.0.tar.bz2`

## blk_alloc_queue

1. Get function address: `sudo grep -A1 -E '^[0-9a-fA-F]+ [a-zA-Z] blk_alloc_queue$' /proc/kallsyms`

2. Get attach point: `sudo objdump -d --start-address=0xffffffffabbbe2b0 --stop-address=0xffffffffabbbe4e0 /proc/kcore`

3. Calculate offset.

4. Load eBPF program: `sudo ./kprobe_loader`

5. Run application to trigger eBPF program: `sudo bash test_app.sh`
