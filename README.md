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

export LLVM_COMPILER=clang
make CC=wllvm AR=llvm-ar HOSTCC=clang defconfig
./scripts/config -e LTO_CLANG
./scripts/config -e DEBUG_INFO_DWARF_TOOLCHAIN_DEFAULT
make CC=wllvm AR=llvm-ar HOSTCC=clang olddefconfig
# 2min51s
/usr/bin/time -v make CC=wllvm AR=llvm-ar HOSTCC=clang -j

# TODO check whether it boots
# TODO check if LTO is necessary; does the result reflect before- or after-LTO

extract-bc vmlinux
llvm-dis vmlinux.bc -o vmlinux.ll
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
bash build-tests.sh
bash run-tests.sh
python validate.py
```

Run with kernel

```shell
KERNEL_DIR=path/to/your/linux-wllvm \
bash run-kernel.sh
```
