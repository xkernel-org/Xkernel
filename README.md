# Xkernel

## Dependencies

```shell
# For linux-image-$(uname -r)-dbgsym
echo "deb http://ddebs.ubuntu.com $(lsb_release -cs) main restricted universe multiverse" | sudo tee -a /etc/apt/sources.list.d/ddebs.list
echo "deb http://ddebs.ubuntu.com $(lsb_release -cs)-updates main restricted universe multiverse" | sudo tee -a /etc/apt/sources.list.d/ddebs.list

sudo apt install ubuntu-dbgsym-keyring && sudo apt update

sudo apt-get install clang llvm libbpf-dev pahole gdb \
    linux-source linux-image-$(uname -r)-dbgsym -y

pushd /usr/src/ && sudo tar -xvf linux-source-6.14.0.tar.bz2 && popd

```

## Workflow

0. Load kfuncs to kernel: `sudo insmod kernel_module/kfuncs.ko`.

1. Determine the offset to attach: `python gdb_core.py hystart_update 434,435 -e`.

2. Write eBPF code in `bpf_kprobe/bpf/examples`, e.g., `cubic.bpf.c`.

3. Modify `BPF_FILE` in `bpf_kprobe/kprobe_loader.cc` and run `sudo ./kprobe_loader`.
