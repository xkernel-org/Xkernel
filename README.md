# Xkernel

## Dependencies of Xkernel

```shell
# Sometimes we find the built-in kernel is too new after upgrading to 25.04, and there is no corresponding dbgsym package.
# Thus, we pick 6.14.0-15-generic.
sudo apt update && sudo apt install linux-image-6.14.0-15-generic linux-headers-6.14.0-15-generic && sudo update-grub && sudo reboot

# For linux-image-$(uname -r)-dbgsym
echo "deb http://ddebs.ubuntu.com $(lsb_release -cs) main restricted universe multiverse" | sudo tee -a /etc/apt/sources.list.d/ddebs.list
echo "deb http://ddebs.ubuntu.com $(lsb_release -cs)-updates main restricted universe multiverse" | sudo tee -a /etc/apt/sources.list.d/ddebs.list

sudo apt install ubuntu-dbgsym-keyring && sudo apt update

sudo apt-get install clang llvm libbpf-dev pahole gdb libgflags-dev \
     linux-image-$(uname -r)-dbgsym -y

# [Optional] Download the source code of the kernel. Xkernel doesn't depend on it.
sudo apt-get install linux-source -y
pushd /usr/src/ && sudo tar -xvf linux-source-6.14.0.tar.bz2 && popd
```

## Workflow of Xkernel

### 0. Compile and load kfuncs to kernel
`make -j && sudo insmod kernel_module/kfuncs.ko`.

### 1. Determine the offset to attach

For most cases, we can leverage gdb to help use analyze the kernel source code and locate the target line directly. \
E.g.,
`python gdb_core.py hystart_update 434,435 -e`.

However, for some cases that gdb is not helpful, we should use objdump to dump all the instructions of the function. \
E.g.,
`python ./objdump.py --func blk_mq_delay_run_hw_queue`.

### 2. Write eBPF code

eBPF files should be placed in `bpf_kprobe/bpf/examples`.

E.g., we want to attach a kprobe to the function `blk_mq_delay_run_hw_queue` at the offset `0xbe`:
```c
SEC("kprobe/blk_mq_delay_run_hw_queue+0xbe")
int BPF_KPROBE(blk_mq_delay_run_hw_queue) {
     return 0;
}
```

E.g., we want to attach a kprobe to the start of the function `blk_mq_delay_run_hw_queue`.
```c
SEC("kprobe/blk_mq_delay_run_hw_queue")
int BPF_KPROBE(blk_mq_delay_run_hw_queue) {
     return 0;
}
```

E.g., we want to attach a kprobe to the end of the function `blk_mq_delay_run_hw_queue`.
```c
SEC("kretprobe/blk_mq_delay_run_hw_queue")
int BPF_KRETPROBE(blk_mq_delay_run_hw_queue) {
     return 0;
}
```

### 3. Load BPF programs

The loader will detect the function name and the offset automatically. \
E.g.,
`sudo ./kprobe_loader --files blk-mq.bpf.o`.

Multiple BPF files are also supported, separated by comma. \
E.g.,
`sudo ./kprobe_loader --files blk-mq.bpf.o,softirq.bpf.o`.

## Case Studies

Cases are summarized in [CaseStudy](CaseStudy/constant.md).






