# Xkernel

## Dependencies
`sudo apt-get install clang llvm libbpf-dev pahole -y`

`sudo apt-get install linux-source gdb -y`

`cd /usr/src/ && sudo tar -xvf linux-source-6.8.0.tar.bz2`

## Workflow

0. Load kfuncs to kernel: `sudo insmod kernel_module/kfuncs.ko`

1. Determine the offset to attach: `python gdb_core.py hystart_update 434,435 -e`

2. Write eBPF code in `kprobe.bpf.c` and load it with `kprobe_loader.cc`

3. Load the eBPF program: `sudo ./kprobe_loader`
