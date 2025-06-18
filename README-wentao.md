## General Setup

```shell
sudo apt -yq install \
git bc libncurses-dev wget busybox libssl-dev libelf-dev dwarves flex \
bison build-essential qemu-system clang llvm lld cmake pkg-config bear
```

```shell
sudo usermod -aG kvm $USER
```

```shell
export PATH="/lib/llvm-19/bin:$PATH"
export LD_LIBRARY_PATH="/lib64:$LD_LIBRARY_PATH"
export XKERNEL_WORKDIR=$HOME
# Derived
# export KERNELDIR=$XKERNEL_WORKDIR/linux-6.14.7
export REPODIR=$XKERNEL_WORKDIR/Xkernel
export PATH="$KERNELDIR/tools/bpf/bpftool/:$PATH"
```

## Build Pahole

```shell
sudo apt -yq install libdw-dev
cd /tmp
git clone https://github.com/acmel/dwarves.git --branch v1.30
cd dwarves
mkdir build
cd build
cmake -DBUILD_SHARED_LIBS=OFF ..
make -j$(nproc)
sudo make install
cd /tmp
rm -rf dwarves
```

## Build libbpf

```shell
cd /tmp/
git clone https://github.com/libbpf/libbpf.git --branch v1.5.1
cd libbpf/
cd src
make -j$(nproc)
sudo make install
cd /tmp/
rm -rf libbpf
```

## Get LLVM

```shell
cd /tmp/
wget https://apt.llvm.org/llvm.sh -O llvm.sh
chmod +x llvm.sh
sudo ./llvm.sh 19
rm -rf llvm.sh
```

## Build Linux

```shell
pahole --version
# v1.30
clang -v
# Ubuntu clang version 19.1.7 (++20250114103320+cd708029e0b2-1~exp1~20250114103432.75)
# Target: x86_64-pc-linux-gnu
# Thread model: posix
# InstalledDir: /usr/lib/llvm-19/bin
# Found candidate GCC installation: /usr/lib/gcc/x86_64-linux-gnu/11
# Selected GCC installation: /usr/lib/gcc/x86_64-linux-gnu/11
# Candidate multilib: .;@m64
# Selected multilib: .;@m64
```

```shell
# wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.14.7.tar.xz -O /tmp/linux-6.14.7.tar.xz
# mkdir -p $XKERNEL_WORKDIR
# cd $XKERNEL_WORKDIR
# tar Jxvf /tmp/linux-6.14.7.tar.xz -C.
# rm /tmp/linux-6.14.7.tar.xz
mkdir -p $KERNELDIR
cd $KERNELDIR
git init
git fetch https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git \
    refs/tags/v6.14.7:refs/tags/v6.14.7 \
    --depth=1
git remote add wentao https://github.com/whentojump/linux-play.git
git checkout -b xkernel
git pull wentao xkernel
```

```shell
cd $KERNELDIR
make LLVM=1 mrproper
make LLVM=1 defconfig
# For convinience {
./scripts/config -e CONFIG_9P_FS_POSIX_ACL
./scripts/config -e CONFIG_9P_FS
./scripts/config -e CONFIG_NET_9P_VIRTIO
./scripts/config -e CONFIG_NET_9P
./scripts/config -e CONFIG_PCI
./scripts/config -e CONFIG_VIRTIO_PCI
./scripts/config -e CONFIG_OVERLAY_FS
./scripts/config -e CONFIG_DEBUG_FS
./scripts/config -e CONFIG_CONFIGFS_FS
./scripts/config -e CONFIG_MAGIC_SYSRQ
make LLVM=1 olddefconfig
# } // End of "For convinience"
# Xkernel infrastructure {
./scripts/config -e CONFIG_DEBUG_INFO_DWARF5
make LLVM=1 olddefconfig
./scripts/config -e CONFIG_BPF_SYSCALL
./scripts/config -e CONFIG_BPF_JIT
./scripts/config -e CONFIG_DEBUG_INFO_BTF
make LLVM=1 olddefconfig
# } // End of "Xkernel infrastructure"
make LLVM=1 -j$(nproc)
```

```shell
cd $KERNELDIR
scripts/clang-tools/gen_compile_commands.py
llvm-objdump -d vmlinux > vmlinux.disas.txt
make LLVM=1 -C tools/bpf/bpftool
gcc dummy_user.c -o dummy_user
gcc dummy2_user.c -o dummy2_user
```

## Get Repo

```shell
cd $XKERNEL_WORKDIR
git clone git@github.com:zhongjiechen/Xkernel.git --branch wentao
cd Xkernel
cd kernel_module
make
```

## Experiments in host

```shell
FUNC_NAME="ttwu_do_activate"

TEXT_OFFSET=$(     sudo readelf -W --segments /proc/kcore |\
                   grep '^  LOAD' |\
                   awk '{ print $2; }' |\
                   head -1 | tail -1 )
TEXT_VA_START=$(   sudo readelf -W --segments /proc/kcore |\
                   grep '^  LOAD' |\
                   awk '{ print $3; }' |\
                   head -1 | tail -1 )
MODULE_OFFSET=$(   sudo readelf -W --segments /proc/kcore |\
                   grep '^  LOAD' |\
                   awk '{ print $2; }' |\
                   head -3 | tail -1 )
MODULE_VA_START=$( sudo readelf -W --segments /proc/kcore |\
                   grep '^  LOAD' |\
                   awk '{ print $3; }' |\
                   head -3 | tail -1 )
MODULE_VA=0x$(     sudo grep ' kfuncs_probe_write_kernel' /proc/kallsyms |\
                   awk '{ print $1; }' )
MODULE_VA2=0x$(    sudo grep ' kfuncs_probe_write_kernel' -A1 /proc/kallsyms |\
                   tail -n1 |\
                   awk '{ print $1; }' )
TEXT_VA=0x$(       sudo grep " $FUNC_NAME\$" /proc/kallsyms |\
                   awk '{ print $1; }' )
TEXT_VA2=0x$(      sudo grep " $FUNC_NAME\$" -A1 /proc/kallsyms |\
                   tail -n1 |\
                   awk '{ print $1; }' )

SIZE=128

# Inspect loaded module code

sudo dd if=/proc/kcore of=insns.bin bs=1 \
skip=$((MODULE_VA-MODULE_VA_START+MODULE_OFFSET)) \
count=$((MODULE_VA2-MODULE_VA)) status=none

objdump -b binary -m i386:x86-64 -D insns.bin --adjust-vma=$MODULE_VA | less

# There should be a call to this address
sudo grep 'T memcpy$' /proc/kallsyms

# Inspect vmlinux code

sudo dd if=/proc/kcore of=insns.bin bs=1 \
skip=$((TEXT_VA-TEXT_VA_START+TEXT_OFFSET)) \
count=$((TEXT_VA2-TEXT_VA)) status=none

objdump -b binary -m i386:x86-64 -D insns.bin --adjust-vma=$TEXT_VA | less

# If the program is loaded, a jmp should have been patched after the
# instruction of interests. (Loading may also cause garbage bytes after
# "jmp" that confuses the disassembler)

VA=0xffffffffc12f7081 # <= FILL IN THIS MANUALLY FROM THE PREVIOUS OUTPUT

sudo dd if=/proc/kcore of=insns.bin bs=1 \
skip=$((VA-MODULE_VA_START+MODULE_OFFSET)) \
count=$SIZE status=none

objdump -b binary -m i386:x86-64 -D insns.bin --adjust-vma=$VA | less

# There should be a call to this address
sudo grep 't optimized_callback$' /proc/kallsyms
# There should also be a jmp back to vmlinux address range, a few
# instruction(s) after the one of interests and after the patched jmp.
```

```shell
sudo insmod $REPODIR/kernel_module/kfuncs.ko
sudo cat /proc/modules | grep kfuncs
cd $REPODIR/bpf_kprobe/
bpftool btf dump file /sys/kernel/btf/vmlinux format c > bpf/vmlinux.h
make
```

```shell
cd $REPODIR/bpf_kprobe/
sudo cat /sys/kernel/tracing/trace_pipe &
sudo ./kprobe_loader &
```

## Get QEMU wrapper

```shell
cd $KERNELDIR
wget https://raw.githubusercontent.com/xlab-uiuc/linux-mcdc/refs/heads/llvm-trunk-next/scripts/q -O q
chmod +x q
```

```shell
cd $KERNELDIR
VM_NUM_CPU=8 ./q
```

## Experiments in guest

### 1. Dummy system call

```shell
insmod $REPODIR/kernel_module/kfuncs.ko
mount -t tracefs none /sys/kernel/tracing
cd $REPODIR/bpf_kprobe/
bpftool btf dump file /sys/kernel/btf/vmlinux format c > bpf/vmlinux.h
make
```

```shell
cd $REPODIR/bpf_kprobe/
\cat /sys/kernel/tracing/trace_pipe &
./kprobe_loader &

$KERNELDIR/dummy_user

# echo 1 > /sys/kernel/debug/dummy/reset
# $KERNELDIR/dummy2_user
```

### 2. Understand the mechanism

```shell
FUNC_NAME="__x64_sys_dummy"
FUNC_NAME="ttwu_do_activate"

TEXT_OFFSET=$(     readelf -W --segments /proc/kcore |\
                   grep '^  LOAD' |\
                   awk '{ print $2; }' |\
                   head -1 | tail -1 )
TEXT_VA_START=$(   readelf -W --segments /proc/kcore |\
                   grep '^  LOAD' |\
                   awk '{ print $3; }' |\
                   head -1 | tail -1 )
MODULE_OFFSET=$(   readelf -W --segments /proc/kcore |\
                   grep '^  LOAD' |\
                   awk '{ print $2; }' |\
                   head -3 | tail -1 )
MODULE_VA_START=$( readelf -W --segments /proc/kcore |\
                   grep '^  LOAD' |\
                   awk '{ print $3; }' |\
                   head -3 | tail -1 )
MODULE_VA=0x$(     grep ' kfuncs_probe_write_kernel' /proc/kallsyms |\
                   awk '{ print $1; }' )
TEXT_VA=0x$(       grep " $FUNC_NAME\$" /proc/kallsyms |\
                   awk '{ print $1; }' )

SIZE=1024

# Inspect loaded module code

dd if=/proc/kcore of=insns.bin bs=1 \
skip=$((MODULE_VA-MODULE_VA_START+MODULE_OFFSET)) \
count=$SIZE status=none

objdump -b binary -m i386:x86-64 -D insns.bin --adjust-vma=$MODULE_VA

# Inspect vmlinux code
# (Loading may cause garbage bytes after "jmp" that confuses the disassembler)

dd if=/proc/kcore of=insns.bin bs=1 \
skip=$((TEXT_VA-TEXT_VA_START+TEXT_OFFSET)) \
count=$SIZE status=none

objdump -b binary -m i386:x86-64 -D insns.bin --adjust-vma=$TEXT_VA

# Inspect kprobe trampoline

VA=0xffffffffc0203000 # <= FILL IN THIS MANUALLY FROM THE PREVIOUS OUTPUT

dd if=/proc/kcore of=insns.bin bs=1 \
skip=$((VA-MODULE_VA_START+MODULE_OFFSET)) \
count=$SIZE status=none

objdump -b binary -m i386:x86-64 -D insns.bin --adjust-vma=$VA
```

### 3. sched, `ttwu_do_activate`

```shell
insmod $REPODIR/kernel_module/kfuncs.ko
mount -t tracefs none /sys/kernel/tracing
cd $REPODIR/bpf_kprobe/
bpftool btf dump file /sys/kernel/btf/vmlinux format c > bpf/vmlinux.h
make
```

```shell
cd $REPODIR/bpf_kprobe/
./kprobe_loader &
```

```shell
cd $KERNELDIR/benchmarks/avg_idle/
rm -f *.csv *.png
./build.sh
./run.sh
python plot_results.py
```
