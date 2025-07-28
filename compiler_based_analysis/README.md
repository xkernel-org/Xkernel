## Dependencies

```shell
sudo apt install jq bear
# FIXME lock finer-grained version
LLVM_VERSION=20
wget https://apt.llvm.org/llvm.sh -O /tmp/llvm.sh
chmod +x /tmp/llvm.sh
sudo /tmp/llvm.sh $LLVM_VERSION
# In case any of these is missing by default
sudo apt install llvm-$LLVM_VERSION clang-$LLVM_VERSION lld-$LLVM_VERSION libclang-$LLVM_VERSION-dev
rm /tmp/llvm.sh
sudo rm /etc/apt/sources.list.d/archive_uri-http_apt_llvm_org_*_-*.list

export PATH="/lib/llvm-20/bin:$PATH"
export XKERNEL_DIR="path/to/your/Xkernel"

cd $XKERNEL_DIR/compiler_based_analysis
./build-tool.sh
./tests/run.sh
```

## Measure arbitrary Linux builds (e.g. Ubuntu configs)

1. Build the kernel with LLVM

    ```shell
    export KERNEL_DIR="path/to/your/linux"
    ```

2. Get `compile_commands.json`
    - With new enough kernel versions,

        ```shell
        cd $KERNEL_DIR
        ./scripts/clang-tools/gen_compile_commands.py
        ```

    - Otherwise, `make LLVM=1 clean` and rebuild with `bear -- make LLVM=1 <options>`
3. Analyze a single file

    ```shell
    $XKERNEL_DIR/compiler_based_analysis/tool/constant_analysis \
        --mode=int-literal \
        -p $KERNEL_DIR \
        $KERNEL_DIR/kernel/sched/fair.c
    ```

    The results should look like

    ```text
    FINDME_INT,update_load_add,lw->inv_weight,0,<not-a-macro>,kernel/sched/fair.c:170:19
    IntegerLiteral 0x5675ff72aeb8 'int' 0
    FINDME_INT,update_load_sub,lw->inv_weight,0,<not-a-macro>,kernel/sched/fair.c:176:19
    IntegerLiteral 0x5675ff72b310 'int' 0
    FINDME_INT,update_load_set,lw->inv_weight,0,<not-a-macro>,kernel/sched/fair.c:182:19
    IntegerLiteral 0x5675ff72b758 'int' 0
    ...
    ```

Next steps are for analyzing the whole Linux codebase

3. Extract the list of compiled C files from `compile_commands.json`

    ```shell
    jq -r '.[].file' $KERNEL_DIR/compile_commands.json |\
        sed "s|$(realpath $KERNEL_DIR)/||g" |\
        sort | uniq \
        > $KERNEL_DIR/compiled_files.txt
    wc -l < $KERNEL_DIR/compiled_files.txt

    rev $KERNEL_DIR/compiled_files.txt | cut -d. -f1 | rev | sort | uniq -c

    grep .c\$ $KERNEL_DIR/compiled_files.txt |\
        sort | uniq \
        > $KERNEL_DIR/compiled_c_files.txt
    wc -l < $KERNEL_DIR/compiled_c_files.txt
    ```

4. Run analysis

    ```shell
    $XKERNEL_DIR/compiler_based_analysis/analyze_kernel.sh $KERNEL_DIR ./output/
    ```

    The end of script should look like:

    ```text
    ...
    Processing sound/pci/hda/hda_jack.c
    Processing sound/pci/hda/hda_proc.c
    Processing sound/pci/hda/hda_sysfs.c
    Processing sound/sound_core.c
    Processing .vmlinux.export.c
    ----------------------------------------
    Duration:              00:01:13
    Script & tool version: ec7945d "Merge pull request #12 from zhongjiechen/gdb"
    ----------------------------------------
    Ubuntu clang version 20.1.8 (++20250708082409+6fb913d3e2ec-1~exp1~20250708202428.132)
    Target: x86_64-pc-linux-gnu
    Thread model: posix
    InstalledDir: /usr/lib/llvm-20/bin
    ----------------------------------------
    ```

    Inspect output:

    ```shell
    tree output | less
    ```

    ```text
    output
    ├── all.txt.1
    ├── arch
    │  └── x86
    │     ├── boot
    │     │  ├── a20.c.txt
    │     │  ├── cmdline.c.txt
    │     │  ├── compressed
    │     │  │  ├── acpi.c.txt
    ...
    ```

    View all instances in one file

    ```shell
    less output/all.txt.1
    ```

Some statistics

- Intel Core i9-14900k
    - Ubuntu source linux-6.14.0, Ubuntu config
        - build 15min23s
        - analysis: 15min17s
    - Upstream source linux 6.14, defconfig
        - build: 1min15s
        - analysis: 1min16s
- CloudLab c6525-25g
    - Ubuntu source linux-6.14.0, Ubuntu config
        - build: 29min22s
        - analysis: 32min32s
    - Upstream source linux 6.14, defconfig
        - build: 2min45s
        - analysis: 2min51s

## Experiments with Linux x.y.0 defconfig

```shell
build_kernel() {
    MAJOR_VERSION=$(echo $VERSION | cut -d. -f1)
    wget https://cdn.kernel.org/pub/linux/kernel/v$MAJOR_VERSION.x/linux-$VERSION.tar.xz -O /tmp/linux-$VERSION.tar.xz
    tar Jxvf /tmp/linux-$VERSION.tar.xz -C kernel_build_dir
    rm /tmp/linux-$VERSION.tar.xz

    pushd kernel_build_dir/linux-$VERSION

    if [[ $VERSION == "6.1" || $VERSION == "5.15" ]]; then
        patch -p1 << EOF
 arch/x86/entry/vdso/vdso.lds.S | 2 ++
 1 file changed, 2 insertions(+)

diff --git a/arch/x86/entry/vdso/vdso.lds.S b/arch/x86/entry/vdso/vdso.lds.S
index 4bf4846..e8c60ae 100644
--- a/arch/x86/entry/vdso/vdso.lds.S
+++ b/arch/x86/entry/vdso/vdso.lds.S
@@ -27,7 +27,9 @@ VERSION {
 		__vdso_time;
 		clock_getres;
 		__vdso_clock_getres;
+#ifdef CONFIG_X86_SGX
 		__vdso_sgx_enter_enclave;
+#endif
 	local: *;
 	};
 }
EOF
    fi
    make LLVM=1 defconfig
    ./scripts/config -d CONFIG_WERROR
    make LLVM=1 olddefconfig
    /usr/bin/time -v make LLVM=1 -j$(nproc)
    ./scripts/clang-tools/gen_compile_commands.py
    popd
}

prepare_file_list() {
    KERNEL_DIR=kernel_build_dir/linux-$VERSION
    jq -r '.[].file' $KERNEL_DIR/compile_commands.json |\
        sed "s|$(realpath $KERNEL_DIR)/||g" |\
        sort | uniq \
        > $KERNEL_DIR/compiled_files.txt
    wc -l < $KERNEL_DIR/compiled_files.txt

    rev $KERNEL_DIR/compiled_files.txt | cut -d. -f1 | rev | sort | uniq -c

    grep .c\$ $KERNEL_DIR/compiled_files.txt |\
        sort | uniq \
        > $KERNEL_DIR/compiled_c_files.txt
    wc -l < $KERNEL_DIR/compiled_c_files.txt
}

# TODO https://www.reddit.com/r/archlinux/comments/pl9pak/compiling_older_versions_of_the_kernel_using/
# export VERSION=5.10
export VERSION=5.15
export VERSION=6.1
export VERSION=6.6
export VERSION=6.12
export VERSION=6.15

build_kernel
prepare_file_list
./analyze_kernel.sh
```

```shell
V1=6.14
V2=6.15
python diff.py log_dir/log-$V1/all.txt.1 \
               log_dir/log-$V2/all.txt.1 \
               $V1-$V2-diff.csv
```
