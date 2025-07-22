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

./build-tool.sh
./tests/run.sh
```

## Measure arbitrary Linux builds (e.g. Ubuntu configs)

1. Build the kernel with LLVM
2. Get `compile_commands.json`
    - With new enough kernel versions,

        ```shell
        ./scripts/clang-tools/gen_compile_commands.py
        ```

    - Otherwise, `make LLVM=1 clean` and rebuild with `bear -- make LLVM=1 <options>`

3. Extract the list of compiled C files from `compile_commands.json`

    ```shell
    export KERNEL_DIR=path/to/linux

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
    cd <this directory>
    ./analyze_kernel.sh $KERNEL_DIR ./output/
    less output/all.txt.1
    ```

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
python diff.py log_dir/log-6.15/all.txt.1 log_dir/log-5.15/all.txt.1
```
