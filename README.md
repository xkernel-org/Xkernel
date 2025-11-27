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
*.diff
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
./scripts/config -e AMT
./scripts/config -e IP_VS
./scripts/config -e NFS_V4_1
./scripts/config -e PNFS_FLEXFILE_LAYOUT
./scripts/config -e MEMORY_FAILURE
./scripts/config -e XFS_FS
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

Analysis goal of the LLVM pass:

Given a start instruction with a constant in it, e.g. `%15 = select i1 %14, i32 3600, i32 %13`

1. Tell me if the constant affects any variable or not (e.g. via assignment)
2. If there are affected variables, recursively find their affected ones
3. When seeing one of the below cases, optionally track the data flow in
   the target function
    1. A pointer parameter of current function
    2. The value is used in a function call
    3. The value is used in return
4. Stop when there are no more assignments; or assigned to a global variable

Usage of the LLVM pass:

Build the pass

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

Programs are found as [`tests/*.c`](./tests/).
After running the above steps, IR for each is found as `tests/*.ll`;
analysis results by the pass as `tests/*.results.txt`.
If a program is included in [`validate.py`](./validate.py), its analysis
results are checked against expectation (annotated in the program itself
with `// FINDME`, `// DONT FINDME` etc).

Run with one case in Linux kernel

```shell
KERNEL_DIR=path/to/your/linux-wllvm \
bash run-kernel.sh
```

Run all cases in Linux kernel

```shell
bash extract-kernel-params.sh
/usr/bin/time -v bash run-kernel-all.sh |& tee run-kernel-all.log
```

## Development

Steps of adding more kernel cases:

1. Pick up a constant from https://gist.github.com/zhongjiechen/6ab1bc5e5ec2b28499592f817c344b8a.
   E.g., `TCP_DELACK_MIN`.
2. Find the file where it's defined (`include/net/tcp.h`) and the file(s)
   where it's used (`net/dccp/{timer,tcp_output}.c`).
3. For each file where the constant is used, add the following to
   [`./locate-const-in-ir.sh`](./locate-const-in-ir.sh) and run the script.

   ```shell
   DEFINITION_SOURCE_FILE=include/net/tcp.h
   SOURCE_FILE=net/dccp/timer.c
   SED_PATTERN='s|\#define TCP_DELACK_MIN	((unsigned)(HZ/25))|\#define TCP_DELACK_MIN	10|'
   ```

4. The results would include two parts, first the IR diff

   ```diff
   386c386
   <   %14 = add i64 %13, 40, !dbg !12866
   ---
   >   %14 = add i64 %13, 10, !dbg !12866
   ```

   Second, automatically generated parameter list for telling the LLVM pass how to
   find this instruction in the bitcode:

   ```shell
   # # %14 = add i64 %13, 40, !dbg !12866
   # # Conclusion: []
   #
   # SOURCE_FILE=net/dccp/timer.c
   # FUNCTION_NAME=dccp_delack_timer
   # SOURCE_OP="add"
   # CONSTANT_VALUE=40
   # OCCURENCE=1
   ```

5. Put the second part in [`run-kernel.sh`](./run-kernel.sh) and run it

   ```text
   === Taint Tracker Configuration ===
   Function: dccp_delack_timer
   Opcode: add
   Constant: 40
   Verbose: OFF
   Interproc: OFF
   Occurrence: 1 (of constant 40)

   [SOURCE] Tainting:   %14 = add i64 %13, 40, !dbg !12338 <net/dccp/timer.c:181:19>
   [USE] Source instruction in data flow <net/dccp/timer.c:181:19>
   [USE] Processing uses of:   %14 = add i64 %13, 40, !dbg !12338
     [EXTERNAL CALL] Tainted value used in external/indirect call <net/dccp/timer.c:180:3>

   === Taint Analysis Complete ===
   ```

   Double check the analysis indeed starts with an instruction that
   previously showed up in diff. Occasionally the autogenerated parameters are
   not accurate and the analysis starts with an irrelevant instruction. In
   such cases, manually correct the parameters, e.g. using higher `OCCURENCE`
   values.

   If no starting instruction is found at all, check for example if the autogenerated
   `CONSTANT_VALUE` parameter is correct.

Known limits of the diff approach: raw diff would include `range()` diff such as

```diff
17021c17021
<   %63 = tail call i32 @llvm.umin.i32(i32 %61, i32 range(i32 2, 17) 2), !dbg !22565
---
>   %63 = tail call i32 @llvm.umin.i32(i32 %61, i32 range(i32 2, 16) 2), !dbg !22565
```
