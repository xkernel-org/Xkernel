Dependencies

```shell
# General Linux build
sudo apt install build-essential flex bison libelf-dev libssl-dev

# LLVM
wget https://apt.llvm.org/llvm.sh -O /tmp/llvm.sh
chmod +x /tmp/llvm.sh
sudo /tmp/llvm.sh 20

# wllvm
sudo apt install python3-pip
pip install wllvm==1.3.1

# Misc
sudo apt install cmake bear
```

Get whole-program LLVM for Linux

```shell
git clone https://github.com/torvalds/linux.git --branch=v6.14 --depth=1 linux-wllvm-defconfig

cd linux-wllvm-defconfig

git apply - << 'EOF'
diff --git a/arch/x86/boot/compressed/vmlinux.lds.S b/arch/x86/boot/compressed/vmlinux.lds.S
index 083ec6d77..264d77981 100644
--- a/arch/x86/boot/compressed/vmlinux.lds.S
+++ b/arch/x86/boot/compressed/vmlinux.lds.S
@@ -74,6 +74,9 @@ SECTIONS

 	STABS_DEBUG
 	DWARF_DEBUG
+
+	.llvm_bc 0 : { *(.llvm_bc) }
+
 	ELF_DETAILS

 	DISCARDS
diff --git a/arch/x86/kernel/vmlinux.lds.S b/arch/x86/kernel/vmlinux.lds.S
index 0deb4887d..ad7377de3 100644
--- a/arch/x86/kernel/vmlinux.lds.S
+++ b/arch/x86/kernel/vmlinux.lds.S
@@ -441,6 +441,8 @@ SECTIONS
 	.llvm_bb_addr_map : { *(.llvm_bb_addr_map) }
 #endif

+	.llvm_bc 0 : { *(.llvm_bc) }
+
 	ELF_DETAILS

 	DISCARDS
EOF

git commit -am 'wllvm: make linker happy'

cat << EOF >> .gitignore

*.bc
*.ll
*.mutated
EOF

git commit -am 'data flow: suppress git diff when we mutate const value to locate it in IR'

export LLVM_COMPILER=clang
export PATH=/lib/llvm-20/bin:$PATH
make CC=wllvm AR=llvm-ar HOSTCC=clang defconfig
./scripts/config -e LTO_CLANG
./scripts/config -e DEBUG_INFO_DWARF_TOOLCHAIN_DEFAULT
make CC=wllvm AR=llvm-ar HOSTCC=clang olddefconfig
# To include some constants in vmlinux
./scripts/config -e INFINIBAND
./scripts/config -e SMC
./scripts/config -e RDS
./scripts/config -e RDS_RDMA
./scripts/config -e NET_SCH_PIE
make CC=wllvm AR=llvm-ar HOSTCC=clang olddefconfig
# 2min51s 14900k
# 4min27s c6420
/usr/bin/time -v make CC=wllvm AR=llvm-ar HOSTCC=clang -j

# TODO check whether it boots
# TODO check if LTO is necessary; does the result reflect before- or after-LTO

# 56s 14900k
# 2min19s c6420
/usr/bin/time -v extract-bc vmlinux
# 5min49s 14900k
# 14min50s c6420
/usr/bin/time -v llvm-dis vmlinux.bc -o vmlinux.ll
```

Analysis goal:

Given a start instruction with a constant in it, e.g. `%15 = select i1 %14, i32 3600, i32 %13`

1. Tell me if the constant affects any variable or not (e.g. via assignment)
2. If there are affected variables, recursively find their affected ones
3. Stops at one of the below cases
    1. A global variable
    2. A pointer parameter of current function
    3. The value is used in a function call
    4. The value is used in return

Usage:

Build the analysis pass

```shell
bash build-pass.sh
```

Experiment with small programs

```shell
export LLVM_COMPILER=clang
export PATH=/lib/llvm-20/bin:$PATH
bash build-tests.sh
bash run-tests.sh
python validate.py
```

Run with kernel

```shell
KERNEL_DIR=path/to/your/linux-wllvm \
bash run-kernel.sh
```
